import os
import csv
import json
import time
import logging
import requests
import pandas as pd
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from .exceptions import (
    FR24Error, FR24AuthenticationError, FR24RateLimitError, 
    FR24NotFoundError, FR24ServerError, FR24ClientError, 
    FR24ValidationError, FR24ConnectionError
)
from .viz import DEFAULT_BASEMAP, aspect_key, plot_altitude_chart, plot_flight_map, plot_speed_chart
import datetime
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Configure logger
logger = logging.getLogger(__name__)


def flight_in_progress(record):
    """Whether a flight summary record describes a flight that hadn't landed.

    A landing time settles it, and it settles it first: `flight_ended` marks a
    record as closed out rather than a flight as over, and Flightradar24 leaves
    it false for a while after the wheels are down. DL691 on Aug. 28, 2026 read
    `flight_ended: false` alongside a landing time of 02:10 UTC.

    Worth getting right, because the rest of the record reads differently for a
    flight caught mid-air: the last fix is wherever the aircraft happened to be,
    and the last time it was seen is not an arrival.
    """
    if not record:
        return False
    if record.get('datetime_landed'):
        return False
    ended = record.get('flight_ended')
    return True if ended is None else not ended


def _create_kml_from_tracks(tracks, flight_id):
    """
    Create a KML string from flight track data.
    
    Args:
        tracks: List of track points
        flight_id: Flight identifier for the KML name
        
    Returns:
        str: KML string
    """
    kml_template = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{flight_id}</name>
    <Style id="yellowLineGreenPoly">
      <LineStyle>
        <color>7f00ffff</color>
        <width>4</width>
      </LineStyle>
      <PolyStyle>
        <color>7f00ff00</color>
      </PolyStyle>
    </Style>
    <Placemark>
      <name>{flight_id}</name>
      <styleUrl>#yellowLineGreenPoly</styleUrl>
      <LineString>
        <extrude>1</extrude>
        <tessellate>1</tessellate>
        <altitudeMode>absolute</altitudeMode>
        <coordinates>
{coordinates}
        </coordinates>
      </LineString>
    </Placemark>
  </Document>
</kml>"""

    # Convert track points to KML coordinates
    coordinates = []
    for track in tracks:
        lon = track.get('lon')
        lat = track.get('lat')
        alt = track.get('alt', 0)  # Default to 0 if altitude not available
        if lon is not None and lat is not None:
            coordinates.append(f"{lon},{lat},{alt}")
    
    return kml_template.format(
        flight_id=flight_id,
        coordinates="\n".join(coordinates)
    )

class FR24API:
    """Flightradar24 API client."""
    
    def __init__(self, token=None):
        """Initialize the FR24 API client.
        
        Args:
            token (str, optional): API token. If not provided, will try to get from environment.
        """
        self.token = token or os.getenv('FR24_API_TOKEN') or os.getenv('FLIGHTRADAR_API_KEY')
        if not self.token:
            raise FR24Error("API token is required. Set FR24_API_TOKEN or FLIGHTRADAR_API_KEY environment variable or pass token parameter.")
            
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Version': 'v1',
            'Authorization': f'Bearer {self.token}'
        })
        
        # Use the module-level logger
        self.logger = logger
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        self.logger.debug("API client ready")

    def _make_request(self, method, url, **kwargs):
        """
        Make an HTTP request with error handling and retries.
        
        Args:
            method: HTTP method (get, post, etc.)
            url: URL to request
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            Response object
            
        Raises:
            FR24AuthenticationError: If authentication fails
            FR24RateLimitError: If rate limit is exceeded
            FR24NotFoundError: If resource is not found
            FR24ServerError: If server error occurs
            FR24ClientError: If client error occurs
            FR24ConnectionError: If connection error occurs
        """
        try:
            self.logger.debug(f"Making {method.upper()} request to {url}")
            self.logger.debug(f"Headers: {kwargs.get('headers', {})}")
            self.logger.debug(f"Params: {kwargs.get('params', {})}")
            response = self.session.request(method, url, **kwargs)
            
            # Handle different HTTP status codes
            if response.status_code == 401:
                self.logger.error(f"Authentication failed. Response: {response.text}")
                raise FR24AuthenticationError("Authentication failed. Check your API token.")
            elif response.status_code == 403:
                self.logger.error(f"Access forbidden. Response: {response.text}")
                raise FR24AuthenticationError("Access forbidden. Check your API token permissions.")
            elif response.status_code == 404:
                self.logger.error(f"Resource not found: {url}")
                raise FR24NotFoundError(f"Resource not found: {url}")
            elif response.status_code == 429:
                self.logger.error("Rate limit exceeded")
                raise FR24RateLimitError("Rate limit exceeded. Try again later.")
            elif response.status_code >= 500:
                self.logger.error(f"Server error: {response.status_code}")
                raise FR24ServerError(f"Server error: {response.status_code}")
            elif response.status_code >= 400:
                self.logger.error(f"Client error {response.status_code}. Response: {response.text}")
                raise FR24ClientError(f"Client error: {response.status_code}. Details: {response.text}")
            
            response.raise_for_status()
            return response
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error: {e}")
            raise FR24ConnectionError(f"Connection error: {e}")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error: {e}")
            raise FR24Error(f"Request error: {e}")

    def _validate_and_format_date(self, date_str):
        """
        Validate and format a date string to ISO format.
        
        Args:
            date_str: Date string in YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ format
            
        Returns:
            str: Formatted ISO date string
            
        Raises:
            FR24ValidationError: If date format is invalid
        """
        # Check if it's already in ISO format
        iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'
        if re.match(iso_pattern, date_str):
            return date_str
            
        # Check if it's in YYYY-MM-DD format
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        if re.match(date_pattern, date_str):
            return f"{date_str}T00:00:00Z"
            
        raise FR24ValidationError(
            "Invalid date format. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ"
        )

    def _validate_flights(self, flights):
        """
        Validate and format flight IDs or flight numbers.
        
        Args:
            flights: Single flight ID/number or list of flight IDs/numbers
            
        Returns:
            str: Comma-separated list of flight IDs/numbers
            
        Raises:
            FR24ValidationError: If flight IDs/numbers are invalid
        """
        if isinstance(flights, str):
            # If it's already a comma-separated string, validate each ID/number
            flight_list = [f.strip() for f in flights.split(',')]
        elif isinstance(flights, (list, tuple)):
            # Convert list to comma-separated string
            flight_list = [str(f).strip() for f in flights]
        else:
            # Convert single value to string
            flight_list = [str(flights).strip()]
            
        # Validate each flight ID/number
        for flight in flight_list:
            if not flight:
                raise FR24ValidationError("Empty flight ID/number found")
            # Flight number pattern (e.g., BA123, DL456)
            flight_number_pattern = r'^[A-Z0-9]{2}\d{1,4}[A-Z]?$'
            # Flight ID pattern (alphanumeric with underscores and hyphens)
            flight_id_pattern = r'^[a-zA-Z0-9_-]+$'
            if not (re.match(flight_number_pattern, flight) or re.match(flight_id_pattern, flight)):
                raise FR24ValidationError(
                    f"Invalid flight format: {flight}. Must be either a flight number (e.g., BA123) or flight ID"
                )
                
        return ','.join(flight_list)

    def get_flight_summary_light(self, flights=None, flight_ids=None, flight_datetime_from=None, flight_datetime_to=None, **kwargs):
        """
        Get basic flight summary information.
        
        Args:
            flights: Single flight number or list of flight numbers (e.g., 'UA123' or ['UA123', 'BA456'])
            flight_ids: Single flight ID or list of flight IDs (e.g., '38a384da' or ['38a384da', '38a400e9'])
            flight_datetime_from: Start date in YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ format
            flight_datetime_to: End date in YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ format
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            dict: Flight summary data
            
        Raises:
            FR24ValidationError: If flight numbers/IDs or dates are invalid
            FR24Error: If API request fails
        """
        url = f"https://fr24api.flightradar24.com/api/flight-summary/light"
        params = {}
        
        # Handle flight numbers
        if flights:
            if isinstance(flights, (list, tuple)):
                flights = ','.join(str(f) for f in flights)
            params['flights'] = flights
            
        # Handle flight IDs
        if flight_ids:
            if isinstance(flight_ids, (list, tuple)):
                flight_ids = ','.join(str(f) for f in flight_ids)
            params['flight_ids'] = flight_ids
            
        # Validate at least one type of flight identifier is provided
        if not flights and not flight_ids:
            raise FR24ValidationError("Either flights or flight_ids must be provided")
            
        # Handle dates
        if flight_datetime_from:
            params['flight_datetime_from'] = self._validate_and_format_date(flight_datetime_from)
        if flight_datetime_to:
            params['flight_datetime_to'] = self._validate_and_format_date(flight_datetime_to)
            
        params.update(kwargs)
        response = self._make_request("get", url, headers=self.session.headers, params=params)
        return response.json()

    def get_flight_summary_full(self, flights=None, flight_ids=None, flight_datetime_from=None, flight_datetime_to=None, **kwargs):
        """
        Get detailed flight summary information.
        
        Args:
            flights: Single flight number or list of flight numbers (e.g., 'UA123' or ['UA123', 'BA456'])
            flight_ids: Single flight ID or list of flight IDs (e.g., '38a384da' or ['38a384da', '38a400e9'])
            flight_datetime_from: Start date in YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ format
            flight_datetime_to: End date in YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ format
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            dict: Detailed flight summary data
            
        Raises:
            FR24ValidationError: If flight numbers/IDs or dates are invalid
            FR24Error: If API request fails
        """
        url = f"https://fr24api.flightradar24.com/api/flight-summary/full"
        params = {}
        
        # Handle flight numbers
        if flights:
            if isinstance(flights, (list, tuple)):
                flights = ','.join(str(f) for f in flights)
            params['flights'] = flights
            
        # Handle flight IDs
        if flight_ids:
            if isinstance(flight_ids, (list, tuple)):
                flight_ids = ','.join(str(f) for f in flight_ids)
            params['flight_ids'] = flight_ids
            
        # Validate at least one type of flight identifier is provided
        if not flights and not flight_ids:
            raise FR24ValidationError("Either flights or flight_ids must be provided")
            
        # Handle dates
        if flight_datetime_from:
            params['flight_datetime_from'] = self._validate_and_format_date(flight_datetime_from)
        if flight_datetime_to:
            params['flight_datetime_to'] = self._validate_and_format_date(flight_datetime_to)
            
        params.update(kwargs)
        response = self._make_request("get", url, headers=self.session.headers, params=params)
        return response.json()

    def get_live_flights_by_registration(self, registration, bounds=None):
        # Get live flights filtered by aircraft registration.
        url = f"https://fr24api.flightradar24.com/api/live/flight-positions/light"
        params = {"registrations": registration}
        if bounds:
            params["bounds"] = bounds
        response = self._make_request("get", url, headers=self.session.headers, params=params)
        return response.json()

    def get_airline_light(self, icao):
        # Get basic airline info by ICAO code.
        url = f"https://fr24api.flightradar24.com/api/static/airlines/{icao}/light"
        response = self._make_request("get", url, headers=self.session.headers)
        return response.json()

    def get_airport_full(self, code):
        # Get detailed airport info by IATA or ICAO code.
        url = f"https://fr24api.flightradar24.com/api/static/airports/{code}/full"
        response = self._make_request("get", url, headers=self.session.headers)
        return response.json()

    def get_flight_positions_light(self, bounds, **kwargs):
        # Get real-time flight positions within specified bounds.
        url = f"https://fr24api.flightradar24.com/api/live/flight-positions/light"
        params = {"bounds": bounds}
        params.update(kwargs)
        response = self._make_request("get", url, headers=self.session.headers, params=params)
        return response.json()

    def get_flight_tracks(self, flight_id):
        # Get flight tracks (ADS-B pings) using the flight ID.
        url = f"https://fr24api.flightradar24.com/api/flight-tracks"
        params = {"flight_id": flight_id}
        response = self._make_request("get", url, headers=self.session.headers, params=params)
        return response.json()

    def enhanced_plot_flight(self, sorted_tracks, flight_id, fig_filename=None, orientation=None, aspect=None, pad_factor=0.12, zoom=None, background=DEFAULT_BASEMAP, flight_number=None, origin=None, destination=None, headline=None, dek=None, source=None, formats=None, in_progress=None):
        """
        Plot the flight path over a basemap and save it to fig_filename.

        Args:
            sorted_tracks: List of track points
            flight_id: Flight identifier
            fig_filename: Output filename for the plot
            orientation: Legacy 'horizontal', 'vertical' or 'auto'; aspect wins
            aspect: Aspect ratio for the finished graphic ('16:9', '3:2', '4:3', '1:1', '9:16')
            pad_factor: Padding around the flight path
            zoom: Zoom level for the basemap (if None, will be automatically determined)
            background: Basemap key ('osm' (default), 'esri-light', 'esri-satellite', 'mapbox-<style>', ...)
            headline, dek, source: Copy overrides for the graphic
            formats: Image formats to write ('png', 'svg', 'pdf'); PNG when omitted
            in_progress: True when the flight hadn't landed, so the end of the line
                is marked as the aircraft still flying rather than as an arrival
        """
        return plot_flight_map(
            sorted_tracks,
            flight_id,
            fig_filename=fig_filename,
            orientation=orientation,
            aspect=aspect,
            pad_factor=pad_factor,
            zoom=zoom,
            background=background,
            flight_number=flight_number,
            origin=origin,
            destination=destination,
            headline=headline,
            dek=dek,
            source=source,
            formats=formats,
            in_progress=in_progress,
            log=self.logger,
        )

    def export_flight_data(self, flight_id, output_dir=None, background=DEFAULT_BASEMAP, orientation=None, aspect=None, timezone=None, flight_number=None, origin=None, destination=None, formats=None, in_progress=None):
        """
        Export flight track data to CSV, GeoJSON (points and line), KML and visualizations.
        Creates a directory named data/flight_id (or specified output_dir) and saves:
          - data.csv: CSV file with flight track points.
          - points.geojson: GeoJSON FeatureCollection of each track point.
          - line.geojson: GeoJSON FeatureCollection with a LineString connecting the points.
          - track.kml: KML file with the flight path.
          - map.png: A map visualization of the flight path.
          - speed.png: A line chart of speed over time.
          - altitude.png: A line chart of altitude over time.

        Each graphic is written once per requested format, so asking for SVG as
        well leaves map.svg beside map.png.

        Args:
            flight_id: Flight identifier
            output_dir: Output directory path
            background: Basemap key ('osm' (default), 'esri-light', 'esri-satellite', 'mapbox-<style>', ...)
            orientation: Legacy 'horizontal', 'vertical' or 'auto'; aspect wins
            aspect: Aspect ratio for every graphic ('16:9', '3:2', '4:3', '1:1', '9:16')
            timezone: IANA zone to convert timestamps to (e.g. 'America/New_York')
            formats: Image formats to write ('png', 'svg', 'pdf'); PNG when omitted
            in_progress: True when the flight hadn't landed at the last fix
        """
        # Fetch flight tracks.
        self.logger.info(f"Fetching flight tracks for flight ID: {flight_id}")
        data = self.get_flight_tracks(flight_id)
        # Determine structure and extract tracks.
        if isinstance(data, list):
            if len(data) == 1 and isinstance(data[0], dict) and "tracks" in data[0]:
                tracks = data[0]["tracks"]
            else:
                tracks = data
        elif isinstance(data, dict):
            tracks = data.get("tracks", [])
        else:
            self.logger.error(f"Unexpected data format for flight ID: {flight_id}")
            raise FR24ValidationError("Unexpected data format")
        
        if not tracks:
            self.logger.warning(f"No flight track data available for flight {flight_id}")
            return

        # Sort tracks by timestamp.
        sorted_tracks = sorted(tracks, key=lambda x: x.get("timestamp", ""))

        # Convert timestamps if a timezone is provided.
        applied_timezone = None
        if timezone:
            try:
                target_tz = ZoneInfo(timezone)
                self.logger.info(f"Converting timestamps to timezone: {timezone}")
                for track in sorted_tracks:
                    if ts_str := track.get("timestamp"):
                        dt_obj = pd.to_datetime(ts_str)
                        if dt_obj.tzinfo is None:
                            dt_obj = dt_obj.tz_localize('UTC')
                        
                        local_dt = dt_obj.astimezone(target_tz)
                        track['timestamp'] = local_dt.isoformat()
                applied_timezone = timezone
            except ZoneInfoNotFoundError:
                self.logger.warning(f"Timezone '{timezone}' not found. Skipping conversion.")
            except Exception as e:
                self.logger.error(f"Error converting timezone: {e}")
        
        # Determine output directory.
        if output_dir is None:
            output_dir = os.path.join("data", flight_id)
        os.makedirs(output_dir, exist_ok=True)
        self.logger.info(f"Exporting flight data to directory: {output_dir}")

        # Export CSV.
        csv_file = os.path.join(output_dir, "data.csv")
        fieldnames = ["timestamp", "lat", "lon", "alt", "gspeed", "vspeed", "track", "squawk", "callsign", "source"]
        with open(csv_file, mode="w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for track in sorted_tracks:
                row = {k: track.get(k, "") for k in fieldnames}
                writer.writerow(row)
        self.logger.info(f"CSV data saved to {csv_file}")

        # Export GeoJSON points.
        points_geojson = {
            "type": "FeatureCollection",
            "features": []
        }
        for track in sorted_tracks:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [track.get("lon"), track.get("lat")]
                },
                "properties": track
            }
            points_geojson["features"].append(feature)
        points_file = os.path.join(output_dir, "points.geojson")
        with open(points_file, "w") as f:
            json.dump(points_geojson, f, indent=2)
        self.logger.info(f"GeoJSON points saved to {points_file}")

        # Export GeoJSON linestring.
        coordinates = []
        for track in sorted_tracks:
            lon = track.get("lon")
            lat = track.get("lat")
            if lon is not None and lat is not None:
                coordinates.append([lon, lat])
        line_geojson = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": coordinates
                },
                "properties": {}
            }]
        }
        line_file = os.path.join(output_dir, "line.geojson")
        with open(line_file, "w") as f:
            json.dump(line_geojson, f, indent=2)
        self.logger.info(f"GeoJSON line saved to {line_file}")

        # Export KML
        kml_content = _create_kml_from_tracks(sorted_tracks, flight_id)
        kml_file = os.path.join(output_dir, "track.kml")
        with open(kml_file, "w") as f:
            f.write(kml_content)
        self.logger.info(f"KML file saved to {kml_file}")

        # Create map visualization
        map_file = os.path.join(output_dir, "map.png")
        self.enhanced_plot_flight(sorted_tracks, flight_id, fig_filename=map_file, background=background, orientation=orientation, aspect=aspect, flight_number=flight_number, origin=origin, destination=destination, formats=formats, in_progress=in_progress)
        
        # Charts have no 'auto' equivalent, so a legacy orientation resolves to a key here.
        chart_aspect = aspect_key(aspect, orientation)

        # Create speed chart
        speed_file = os.path.join(output_dir, "speed.png")
        self._plot_speed_chart(sorted_tracks, flight_id, speed_file, flight_number=flight_number, origin=origin, destination=destination, timezone=applied_timezone, aspect=chart_aspect, formats=formats)
        
        # Create altitude chart
        altitude_file = os.path.join(output_dir, "altitude.png")
        self._plot_altitude_chart(sorted_tracks, flight_id, altitude_file, flight_number=flight_number, origin=origin, destination=destination, timezone=applied_timezone, aspect=chart_aspect, formats=formats)

        return output_dir

    def _plot_speed_chart(self, tracks, flight_id, output_file, flight_number=None, origin=None, destination=None, timezone=None, aspect=None, formats=None):
        """Create a line chart of ground speed over time."""
        plot_speed_chart(
            tracks, flight_id, output_file,
            flight_number=flight_number, origin=origin, destination=destination,
            timezone=timezone, aspect=aspect, formats=formats, log=self.logger,
        )

    def _plot_altitude_chart(self, tracks, flight_id, output_file, flight_number=None, origin=None, destination=None, timezone=None, aspect=None, formats=None):
        """Create a line chart of altitude over time."""
        plot_altitude_chart(
            tracks, flight_id, output_file,
            flight_number=flight_number, origin=origin, destination=destination,
            timezone=timezone, aspect=aspect, formats=formats, log=self.logger,
        )

    def get_flight_ids_by_registration(self, registration, date_from, date_to, offset=0, limit=20, max_pages=5):
        # Get flight instances for a registration within a date range using the summary endpoint.
        url = "https://fr24api.flightradar24.com/api/flight-summary/light"
        params = {
            "registrations": registration,
            "flight_datetime_from": self._validate_and_format_date(date_from),
            "flight_datetime_to": self._validate_and_format_date(date_to),
            "offset": offset,
            "limit": limit
        }
        response = self._make_request("get", url, headers=self.session.headers, params=params)
        return response.json()

    def smart_export_flight(
        self,
        flight_number,
        date,
        output_dir=None,
        background=DEFAULT_BASEMAP,
        orientation=None,
        aspect=None,
        auto_select=None,  # 'latest', 'earliest', or integer index
        summary_mode='full',  # or 'light',
        timezone=None,
        formats=None,
    ):
        """
        Look up a flight by number and date, select the correct segment if multiple, and export data for the selected flight.
        If multiple matches and auto_select is None, returns a list of options for the caller to handle (e.g., for CLI prompt).
        Returns a dict with keys: 'output_dir', 'selected', and 'options' (if multiple).
        """
        # Convert date to full-day range if needed
        if len(date) == 10 and date.count('-') == 2:
            flight_datetime_from = f"{date}T00:00:00Z"
            flight_datetime_to = f"{date}T23:59:59Z"
        else:
            flight_datetime_from = date
            flight_datetime_to = date
        # 1. Fetch flight summary
        if summary_mode == 'full':
            summary = self.get_flight_summary_full(flights=flight_number, flight_datetime_from=flight_datetime_from, flight_datetime_to=flight_datetime_to)
        else:
            summary = self.get_flight_summary_light(flights=flight_number, flight_datetime_from=flight_datetime_from, flight_datetime_to=flight_datetime_to)
        data = summary.get('data', [])
        if not data:
            return {'output_dir': None, 'selected': None, 'options': [], 'error': f"No flights found for {flight_number} on {date}"}

        # 2. Handle single/multiple matches
        if len(data) == 1 or auto_select is not None:
            if len(data) == 1:
                selected = data[0]
            else:
                # auto_select: 'latest', 'earliest', or integer index
                if auto_select == 'latest':
                    selected = max(data, key=lambda x: x.get('datetime_takeoff', '') or x.get('first_seen', ''))
                elif auto_select == 'earliest':
                    selected = min(data, key=lambda x: x.get('datetime_takeoff', '') or x.get('first_seen', ''))
                elif isinstance(auto_select, int) and 0 <= auto_select < len(data):
                    selected = data[auto_select]
                else:
                    return {'output_dir': None, 'selected': None, 'options': data, 'error': 'Invalid auto_select value'}
            # 3. Generate smart output_dir if not provided
            orig = selected.get('orig_icao') or selected.get('origin') or 'ORIG'
            dest = selected.get('dest_icao_actual') or selected.get('dest_icao') or selected.get('destination') or 'DEST'
            date_str = (selected.get('datetime_takeoff') or selected.get('first_seen') or date)[:10]
            flight_id = selected.get('fr24_id') or selected.get('id') or 'UNKNOWNID'
            dep_time = (selected.get('datetime_takeoff') or selected.get('first_seen') or '').replace(':','').replace('-','').replace('T','')[:8]
            if not output_dir:
                # e.g., data/UA2151_2025-04-22_KEWR-KDEN_3a01b036
                safe_flight = str(flight_number).replace('/', '_').replace(' ', '')
                safe_orig = orig.replace('/', '_')
                safe_dest = dest.replace('/', '_')
                output_dir = f"data/{safe_flight}_{date_str}_{safe_orig}-{safe_dest}_{flight_id}"
            # 4. Export
            export_dir = self.export_flight_data(flight_id, output_dir=output_dir, background=background, orientation=orientation, aspect=aspect, timezone=timezone, flight_number=flight_number, origin=orig, destination=dest, formats=formats, in_progress=flight_in_progress(selected))
            return {'output_dir': export_dir, 'selected': selected, 'options': data}
        else:
            # Multiple matches, no auto_select: return options for caller to prompt
            return {'output_dir': None, 'selected': None, 'options': data}