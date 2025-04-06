import os
import csv
import json
import requests
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import geopandas as gpd
import contextily as ctx
from shapely.geometry import Point, LineString
import pandas as pd

class FR24API:
    def __init__(self, token):
        # Set the base URL and headers with your API token.
        self.base_url = "https://fr24api.flightradar24.com"
        self.headers = {
            "Accept": "application/json",
            "Accept-Version": "v1",
            "Authorization": f"Bearer {token}"
        }
    
    def get_live_flights_by_registration(self, registration, bounds=None):
        # Get live flights filtered by aircraft registration.
        url = f"{self.base_url}/api/live/flight-positions/light"
        params = {"registrations": registration}
        if bounds:
            params["bounds"] = bounds
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_airline_light(self, icao):
        # Get basic airline info by ICAO code.
        url = f"{self.base_url}/api/static/airlines/{icao}/light"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_airport_full(self, code):
        # Get detailed airport info by IATA or ICAO code.
        url = f"{self.base_url}/api/static/airports/{code}/full"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_flight_positions_light(self, bounds, **kwargs):
        # Get real-time flight positions within specified bounds.
        url = f"{self.base_url}/api/live/flight-positions/light"
        params = {"bounds": bounds}
        params.update(kwargs)
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_flight_tracks(self, flight_id):
        # Get flight tracks (ADS-B pings) using the flight ID.
        url = f"{self.base_url}/api/flight-tracks"
        params = {"flight_id": flight_id}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def enhanced_plot_flight(self, sorted_tracks, flight_id, fig_filename=None, figsize=(10,10), pad_factor=0.2, zoom=None):
        """
        Enhanced plot of flight data using geopandas and contextily.
        Converts the track list into a GeoDataFrame, adds a basemap and plots points and a connecting line.
        """
        # Convert track data to DataFrame then to GeoDataFrame
        df = pd.DataFrame(sorted_tracks)
        if df.empty:
            print("No data available to plot.")
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
        # ax.legend()
        plt.tight_layout()
        plt.title(f"Flight: {flight_id}")
        
        if fig_filename:
            os.makedirs(os.path.dirname(fig_filename), exist_ok=True)
            plt.savefig(fig_filename, dpi=300, bbox_inches="tight")
            print(f"Plot saved as {fig_filename}")

    def export_flight_data(self, flight_id, output_dir=None):
        """
        Export flight track data to CSV, GeoJSON (points and line) and an enhanced plot.
        Creates a directory named after the flight_id (or specified output_dir) and saves:
          - data.csv: CSV file with flight track points.
          - points.geojson: GeoJSON FeatureCollection of each track point.
          - line.geojson: GeoJSON FeatureCollection with a LineString connecting the points.
          - plot.png: An enhanced map plot of the flight path.
        """
        # Fetch flight tracks.
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
            raise ValueError("Unexpected data format")
        
        if not tracks:
            print("No flight track data available for flight", flight_id)
            return

        # Sort tracks by timestamp.
        sorted_tracks = sorted(tracks, key=lambda x: x.get("timestamp", ""))
        
        # Determine output directory.
        if output_dir is None:
            output_dir = flight_id
        os.makedirs(output_dir, exist_ok=True)

        # Export CSV.
        csv_file = os.path.join(output_dir, "data.csv")
        fieldnames = ["timestamp", "lat", "lon", "alt", "gspeed", "vspeed", "track", "squawk", "callsign", "source"]
        with open(csv_file, mode="w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for track in sorted_tracks:
                row = {k: track.get(k, "") for k in fieldnames}
                writer.writerow(row)
        print(f"CSV data saved to {csv_file}")

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
        print(f"GeoJSON points saved to {points_file}")

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
        print(f"GeoJSON line saved to {line_file}")

        # Create an enhanced plot.
        plot_file = os.path.join(output_dir, "plot.png")
        self.enhanced_plot_flight(sorted_tracks, flight_id, fig_filename=plot_file)

        return output_dir