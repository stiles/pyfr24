import os
import csv
import json
import time
import logging
import requests
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
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

# Configure logger
logger = logging.getLogger(__name__)

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
    def __init__(self, token, max_retries=3, retry_backoff_factor=0.5):
        # Set the base URL and headers with your API token.
        self.base_url = "https://fr24api.flightradar24.com"
        self.headers = {
            "Accept": "application/json",
            "Accept-Version": "v1",
            "Authorization": f"Bearer {token}"
        }
        
        # Configure retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=retry_backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        logger.info("FR24API client initialized")

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
            logger.debug(f"Making {method.upper()} request to {url}")
            response = self.session.request(method, url, **kwargs)
            
            # Handle different HTTP status codes
            if response.status_code == 401:
                logger.error("Authentication failed")
                raise FR24AuthenticationError("Authentication failed. Check your API token.")
            elif response.status_code == 403:
                logger.error("Access forbidden")
                raise FR24AuthenticationError("Access forbidden. Check your API token permissions.")
            elif response.status_code == 404:
                logger.error(f"Resource not found: {url}")
                raise FR24NotFoundError(f"Resource not found: {url}")
            elif response.status_code == 429:
                logger.error("Rate limit exceeded")
                raise FR24RateLimitError("Rate limit exceeded. Try again later.")
            elif response.status_code >= 500:
                logger.error(f"Server error: {response.status_code}")
                raise FR24ServerError(f"Server error: {response.status_code}")
            elif response.status_code >= 400:
                logger.error(f"Client error: {response.status_code}")
                raise FR24ClientError(f"Client error: {response.status_code}")
            
            response.raise_for_status()
            return response
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise FR24ConnectionError(f"Connection error: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise FR24Error(f"Request error: {e}")

    def get_flight_summary_light(self, flights, flight_datetime_from, flight_datetime_to, **kwargs):
        # Get basic flight summary information.
        url = f"{self.base_url}/api/flight-summary/light"
        params = {
            "flights": flights,
            "flight_datetime_from": flight_datetime_from,
            "flight_datetime_to": flight_datetime_to
        }
        params.update(kwargs)
        response = self._make_request("get", url, headers=self.headers, params=params)
        return response.json()

    def get_flight_summary_full(self, flights, flight_datetime_from, flight_datetime_to, **kwargs):
        # Get detailed flight summary information.
        url = f"{self.base_url}/api/flight-summary/full"
        params = {
            "flights": flights,
            "flight_datetime_from": flight_datetime_from,
            "flight_datetime_to": flight_datetime_to
        }
        params.update(kwargs)
        response = self._make_request("get", url, headers=self.headers, params=params)
        return response.json()

    def get_live_flights_by_registration(self, registration, bounds=None):
        # Get live flights filtered by aircraft registration.
        url = f"{self.base_url}/api/live/flight-positions/light"
        params = {"registrations": registration}
        if bounds:
            params["bounds"] = bounds
        response = self._make_request("get", url, headers=self.headers, params=params)
        return response.json()

    def get_airline_light(self, icao):
        # Get basic airline info by ICAO code.
        url = f"{self.base_url}/api/static/airlines/{icao}/light"
        response = self._make_request("get", url, headers=self.headers)
        return response.json()

    def get_airport_full(self, code):
        # Get detailed airport info by IATA or ICAO code.
        url = f"{self.base_url}/api/static/airports/{code}/full"
        response = self._make_request("get", url, headers=self.headers)
        return response.json()

    def get_flight_positions_light(self, bounds, **kwargs):
        # Get real-time flight positions within specified bounds.
        url = f"{self.base_url}/api/live/flight-positions/light"
        params = {"bounds": bounds}
        params.update(kwargs)
        response = self._make_request("get", url, headers=self.headers, params=params)
        return response.json()

    def get_flight_tracks(self, flight_id):
        # Get flight tracks (ADS-B pings) using the flight ID.
        url = f"{self.base_url}/api/flight-tracks"
        params = {"flight_id": flight_id}
        response = self._make_request("get", url, headers=self.headers, params=params)
        return response.json()

    def enhanced_plot_flight(self, sorted_tracks, flight_id, fig_filename=None, figsize=(10,10), pad_factor=0.2, zoom=None):
        """
        Enhanced plot of flight data using geopandas and contextily.
        Converts the track list into a GeoDataFrame, adds a basemap and plots points and a connecting line.
        """
        # Convert track data to DataFrame then to GeoDataFrame
        df = pd.DataFrame(sorted_tracks)
        if df.empty:
            logger.warning("No data available to plot.")
            return
        # Create geometry column from lon, lat and set CRS to EPSG:4326.
        gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs="EPSG:4326")
        # For a single flight, add a constant flight_leg column.
        gdf["flight_leg"] = "flight1"
        # Reproject to Web Mercator.
        gdf_plot = gdf.to_crs(epsg=3857)
        
        # Create figure and axis.
        fig, ax = plt.subplots(figsize=figsize)
        
        # Use a colormap for the flight leg.
        unique_legs = gdf_plot["flight_leg"].unique()
        cmap = plt.get_cmap("tab10", len(unique_legs))
        norm = mcolors.Normalize(vmin=0, vmax=len(unique_legs))
        colors = {leg: cmap(norm(i)) for i, leg in enumerate(unique_legs)}
        
        # Plot points per flight leg.
        for leg, group in gdf_plot.groupby("flight_leg"):
            group.plot(ax=ax, marker="o", color=colors[leg], markersize=5, label=leg)
        
        # Plot a connecting line.
        ax.plot(gdf_plot.geometry.x, gdf_plot.geometry.y, color="black", linewidth=2, label="Flight path")
        
        # Expand plot bounds for context.
        xmin, ymin, xmax, ymax = gdf_plot.total_bounds
        x_pad = (xmax - xmin) * pad_factor
        y_pad = (ymax - ymin) * pad_factor
        extent = [xmin - x_pad, ymin - y_pad, xmax + x_pad, ymax + y_pad]
        ax.set_xlim(extent[0], extent[2])
        ax.set_ylim(extent[1], extent[3])
        
        # Add a basemap.
        if zoom is not None:
            ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, zoom=zoom, reset_extent=False)
        else:
            ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, reset_extent=False)
        
        ax.set_axis_off()
        plt.tight_layout()
        plt.title(f"Flight: {flight_id}")
        
        if fig_filename:
            os.makedirs(os.path.dirname(fig_filename), exist_ok=True)
            plt.savefig(fig_filename, dpi=300, bbox_inches="tight")
            logger.info(f"Plot saved as {fig_filename}")

    def export_flight_data(self, flight_id, output_dir=None):
        """
        Export flight track data to CSV, GeoJSON (points and line), KML and an enhanced plot.
        Creates a directory named data/flight_id (or specified output_dir) and saves:
          - data.csv: CSV file with flight track points.
          - points.geojson: GeoJSON FeatureCollection of each track point.
          - line.geojson: GeoJSON FeatureCollection with a LineString connecting the points.
          - track.kml: KML file with the flight path.
          - plot.png: An enhanced map plot of the flight path.
        """
        # Fetch flight tracks.
        logger.info(f"Fetching flight tracks for flight ID: {flight_id}")
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
            logger.error(f"Unexpected data format for flight ID: {flight_id}")
            raise FR24ValidationError("Unexpected data format")
        
        if not tracks:
            logger.warning(f"No flight track data available for flight {flight_id}")
            return

        # Sort tracks by timestamp.
        sorted_tracks = sorted(tracks, key=lambda x: x.get("timestamp", ""))
        
        # Determine output directory.
        if output_dir is None:
            output_dir = os.path.join("data", flight_id)
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Exporting flight data to directory: {output_dir}")

        # Export CSV.
        csv_file = os.path.join(output_dir, "data.csv")
        fieldnames = ["timestamp", "lat", "lon", "alt", "gspeed", "vspeed", "track", "squawk", "callsign", "source"]
        with open(csv_file, mode="w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for track in sorted_tracks:
                row = {k: track.get(k, "") for k in fieldnames}
                writer.writerow(row)
        logger.info(f"CSV data saved to {csv_file}")

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
        logger.info(f"GeoJSON points saved to {points_file}")

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
        logger.info(f"GeoJSON line saved to {line_file}")

        # Export KML
        kml_content = _create_kml_from_tracks(sorted_tracks, flight_id)
        kml_file = os.path.join(output_dir, "track.kml")
        with open(kml_file, "w") as f:
            f.write(kml_content)
        logger.info(f"KML file saved to {kml_file}")

        # Create an enhanced plot.
        plot_file = os.path.join(output_dir, "plot.png")
        self.enhanced_plot_flight(sorted_tracks, flight_id, fig_filename=plot_file)

        return output_dir