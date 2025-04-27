import os
import csv
import json
import time
import logging
import requests
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.font_manager as fm
import geopandas as gpd
import contextily as ctx
from shapely.geometry import Point, LineString
import pandas as pd
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from .exceptions import (
    FR24Error, FR24AuthenticationError, FR24RateLimitError, 
    FR24NotFoundError, FR24ServerError, FR24ClientError, 
    FR24ValidationError, FR24ConnectionError
)
import matplotlib.dates as mdates
import datetime
import re

# Configure logger
logger = logging.getLogger(__name__)

# Configure default font
def _configure_font():
    """Configure the default font for plots."""
    # Try to find Roboto in system fonts
    roboto_font = None
    for font in fm.findSystemFonts():
        if 'Roboto' in font:
            roboto_font = font
            break
    
    # If Roboto not found, use the default sans-serif font
    if roboto_font:
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Roboto']
    else:
        logger.debug("Using system default sans-serif font")

# Configure font when module is imported
_configure_font()

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

    def enhanced_plot_flight(self, sorted_tracks, flight_id, fig_filename=None, orientation='horizontal', pad_factor=0.2, zoom=None, background='carto'):
        """
        Enhanced plot of flight data using geopandas and contextily.
        Converts the track list into a GeoDataFrame, adds a basemap and plots points and a connecting line.
        
        Args:
            sorted_tracks: List of track points
            flight_id: Flight identifier
            fig_filename: Output filename for the plot
            orientation: Plot orientation ('horizontal', 'vertical', or 'auto'). 
                       'horizontal' uses 16:9 aspect ratio (default)
                       'vertical' uses 9:16 aspect ratio
                       'auto' will choose based on the flight path direction
            pad_factor: Padding around the flight path
            zoom: Zoom level for the basemap (if None, will be automatically determined)
            background: Background map provider ('carto', 'osm', 'stamen', 'esri')
        """
        self.logger.debug(f"Starting enhanced_plot_flight with {len(sorted_tracks)} track points")
        
        # Convert track data to DataFrame then to GeoDataFrame
        df = pd.DataFrame(sorted_tracks)
        if df.empty:
            self.logger.warning("No data available to plot.")
            return
            
        self.logger.debug(f"DataFrame created with columns: {df.columns.tolist()}")
        
        # Create geometry column from lon, lat and set CRS to EPSG:4326.
        try:
            gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs="EPSG:4326")
            self.logger.debug("GeoDataFrame created successfully")
        except Exception as e:
            self.logger.error(f"Error creating GeoDataFrame: {e}")
            return
            
        # Reproject to Web Mercator.
        try:
            gdf_plot = gdf.to_crs(epsg=3857)
            self.logger.debug("Data reprojected to Web Mercator")
        except Exception as e:
            self.logger.error(f"Error reprojecting data: {e}")
            return

        # Determine orientation if 'auto'
        if orientation == 'auto':
            # Get the bounding box
            xmin, ymin, xmax, ymax = gdf_plot.total_bounds
            width = xmax - xmin
            height = ymax - ymin
            # Choose orientation based on which dimension is larger
            orientation = 'horizontal' if width > height else 'vertical'
            self.logger.debug(f"Auto-detected orientation: {orientation}")

        # Set figure size based on orientation
        if orientation == 'vertical':
            figsize = (9, 16)
        else:  # horizontal
            figsize = (16, 9)
        
        # Create figure and axis with appropriate aspect ratio
        fig, ax = plt.subplots(figsize=figsize)
        
        # Plot only the connecting line in orange (#f18851) without any points
        self.logger.debug("Plotting connecting line")
        ax.plot(gdf_plot.geometry.x, gdf_plot.geometry.y, color="#f18851", linewidth=2, solid_capstyle='round', solid_joinstyle='round')
        
        # Expand plot bounds for context.
        try:
            xmin, ymin, xmax, ymax = gdf_plot.total_bounds
            self.logger.debug(f"Plot bounds: xmin={xmin}, ymin={ymin}, xmax={xmax}, ymax={ymax}")
            x_pad = (xmax - xmin) * pad_factor
            y_pad = (ymax - ymin) * pad_factor
            extent = [xmin - x_pad, ymin - y_pad, xmax + x_pad, ymax + y_pad]
            ax.set_xlim(extent[0], extent[2])
            ax.set_ylim(extent[1], extent[3])
            
            # Force aspect ratio to match figure size
            ax.set_aspect('equal')
        except Exception as e:
            self.logger.error(f"Error setting plot bounds: {e}")
            return
        
        # Add a basemap based on the selected provider
        try:
            # If zoom is None, don't pass it to add_basemap
            basemap_kwargs = {'reset_extent': False}
            if zoom is not None:
                basemap_kwargs['zoom'] = zoom
                
            if background.lower() == 'osm':
                ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, **basemap_kwargs)
            elif background.lower() == 'stamen':
                ctx.add_basemap(ax, source=ctx.providers.Stamen.Terrain, **basemap_kwargs)
            elif background.lower() == 'esri':
                ctx.add_basemap(ax, source=ctx.providers.Esri.WorldTopoMap, **basemap_kwargs)
            else:  # default to carto
                ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, **basemap_kwargs)
            self.logger.debug(f"Basemap added with provider: {background}")
        except Exception as e:
            self.logger.error(f"Error adding basemap: {e}")
            return
        
        ax.set_axis_off()
        plt.tight_layout()
        plt.title(f"Flight: {flight_id}")
        
        if fig_filename:
            try:
                os.makedirs(os.path.dirname(fig_filename), exist_ok=True)
                plt.savefig(fig_filename, dpi=300, bbox_inches="tight", pad_inches=0)
                self.logger.info(f"Plot saved as {fig_filename}")
            except Exception as e:
                self.logger.error(f"Error saving plot: {e}")
                return

    def export_flight_data(self, flight_id, output_dir=None, background='carto', orientation='horizontal'):
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
          
        Args:
            flight_id: Flight identifier
            output_dir: Output directory path
            background: Background map provider ('carto', 'osm', 'stamen', 'esri')
            orientation: Plot orientation ('horizontal', 'vertical', or 'auto'). 
                       'horizontal' uses 16:9 aspect ratio (default)
                       'vertical' uses 9:16 aspect ratio
                       'auto' will choose based on the flight path direction
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
        self.enhanced_plot_flight(sorted_tracks, flight_id, fig_filename=map_file, background=background, orientation=orientation)
        
        # Create speed chart
        speed_file = os.path.join(output_dir, "speed.png")
        self._plot_speed_chart(sorted_tracks, flight_id, speed_file)
        
        # Create altitude chart
        altitude_file = os.path.join(output_dir, "altitude.png")
        self._plot_altitude_chart(sorted_tracks, flight_id, altitude_file)

        return output_dir

    def _plot_speed_chart(self, tracks, flight_id, output_file):
        """Create a line chart of speed over time."""
        # Extract timestamps and speeds
        timestamps = []
        speeds = []
        self.logger.debug(f"Processing {len(tracks)} track points for speed chart")
        
        for i, track in enumerate(tracks):
            try:
                self.logger.debug(f"Track point {i}: {track}")
                
                # Skip if timestamp is missing or None
                if 'timestamp' not in track or track['timestamp'] is None:
                    self.logger.debug(f"Skipping track {i}: missing or None timestamp")
                    continue
                    
                timestamp = pd.to_datetime(track['timestamp'])
                
                # Handle missing or None speed values
                if 'gspeed' not in track or track['gspeed'] is None:
                    speed = 0  # Assume zero speed when data is missing
                    self.logger.debug(f"Track {i}: using zero speed for missing data")
                else:
                    speed = float(track['gspeed'])
                
                # Skip only if speed is negative or unreasonably high
                if speed < 0 or speed > 1000:  # 1000 knots is a reasonable upper limit
                    self.logger.debug(f"Skipping track {i}: invalid speed value {speed}")
                    continue
                    
                timestamps.append(timestamp)
                speeds.append(speed)
                self.logger.debug(f"Added track point {i}: timestamp={timestamp}, speed={speed}")
            except (ValueError, TypeError) as e:
                self.logger.debug(f"Skipping track {i}: error processing data - {e}")
                continue

        if not timestamps:
            self.logger.warning("No valid speed data available for plotting")
            return

        self.logger.debug(f"Creating speed chart with {len(timestamps)} points")
        
        # Set style
        plt.style.use('fivethirtyeight')
        
        # Create the plot with larger figure size
        plt.figure(figsize=(16, 9))
        
        # Plot the speed data
        plt.plot(timestamps, speeds, color='#f18851', linewidth=2.5, label='Ground speed')
        
        # Add title and labels with larger font sizes
        plt.title(f"Flight {flight_id} - Ground speed profile", fontsize=16, pad=20)
        plt.xlabel("Time", fontsize=14)
        plt.ylabel("Ground speed (knots)", fontsize=14)
        
        # Customize grid
        plt.grid(True, linestyle='--', alpha=0.5)
        
        # Format x-axis ticks
        plt.xticks(rotation=45)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        
        # Add reference lines for common speed thresholds
        plt.axhline(y=0, color='gray', linestyle=':', alpha=0.5, label='Ground')
        
        # Add legend
        plt.legend(loc='upper right', fontsize=12)
        
        # Adjust layout
        plt.tight_layout()
        
        # Save the plot with higher DPI
        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        plt.close()
        self.logger.info(f"Speed chart saved to {output_file}")

    def _plot_altitude_chart(self, tracks, flight_id, output_file):
        """Create a line chart of altitude over time."""
        # Extract timestamps and altitudes
        timestamps = []
        altitudes = []
        self.logger.debug(f"Processing {len(tracks)} track points for altitude chart")
        
        for i, track in enumerate(tracks):
            try:
                self.logger.debug(f"Track point {i}: {track}")
                
                # Skip if timestamp is missing or None
                if 'timestamp' not in track or track['timestamp'] is None:
                    self.logger.debug(f"Skipping track {i}: missing or None timestamp")
                    continue
                    
                timestamp = pd.to_datetime(track['timestamp'])
                
                # Handle missing or None altitude values
                if 'alt' not in track or track['alt'] is None:
                    alt = 0  # Assume ground level when data is missing
                    self.logger.debug(f"Track {i}: using zero altitude for missing data")
                else:
                    alt = float(track['alt'])
                
                # Skip only if altitude is negative or unreasonably high
                if alt < 0 or alt > 50000:  # 50,000 feet is a reasonable upper limit
                    self.logger.debug(f"Skipping track {i}: invalid altitude value {alt}")
                    continue
                    
                timestamps.append(timestamp)
                altitudes.append(alt)
                self.logger.debug(f"Added track point {i}: timestamp={timestamp}, altitude={alt}")
            except (ValueError, TypeError) as e:
                self.logger.debug(f"Skipping track {i}: error processing data - {e}")
                continue

        if not timestamps:
            self.logger.warning("No valid altitude data available for plotting")
            return

        self.logger.debug(f"Creating altitude chart with {len(timestamps)} points")
        
        # Set style
        plt.style.use('fivethirtyeight')
        
        # Create the plot with larger figure size
        plt.figure(figsize=(16, 9))
        
        # Plot the altitude data
        plt.plot(timestamps, altitudes, color='#f18851', linewidth=2.5, label='Altitude')
        
        # Add title and labels with larger font sizes
        plt.title(f"Flight {flight_id} - Altitude profile", fontsize=16, pad=20)
        plt.xlabel("Time", fontsize=14)
        plt.ylabel("Altitude (feet)", fontsize=14)
        
        # Customize grid
        plt.grid(True, linestyle='--', alpha=0.5)
        
        # Format x-axis ticks
        plt.xticks(rotation=45)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        
        # Add reference lines for common altitude thresholds
        plt.axhline(y=30000, color='gray', linestyle=':', alpha=0.5, label='30,000 ft')
        plt.axhline(y=10000, color='gray', linestyle=':', alpha=0.5, label='10,000 ft')
        plt.axhline(y=0, color='gray', linestyle=':', alpha=0.5, label='Ground')
        
        # Add legend
        plt.legend(loc='upper right', fontsize=12)
        
        # Adjust layout
        plt.tight_layout()
        
        # Save the plot with higher DPI
        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        plt.close()
        self.logger.info(f"Altitude chart saved to {output_file}")

    def get_flight_ids_by_registration(self, registration, date_from, date_to, offset=0, limit=20, max_pages=5):
        # Get flight IDs for an aircraft registration within a date range.
        url = f"https://fr24api.flightradar24.com/api/flight-ids"
        params = {
            "registration": registration,
            "date_from": self._validate_and_format_date(date_from),
            "date_to": self._validate_and_format_date(date_to),
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
        background='carto',
        orientation='horizontal',
        auto_select=None,  # 'latest', 'earliest', or integer index
        summary_mode='full',  # or 'light'
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
            export_dir = self.export_flight_data(flight_id, output_dir=output_dir, background=background, orientation=orientation)
            return {'output_dir': export_dir, 'selected': selected, 'options': data}
        else:
            # Multiple matches, no auto_select: return options for caller to prompt
            return {'output_dir': None, 'selected': None, 'options': data}