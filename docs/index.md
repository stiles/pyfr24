# Pyfr24 documentation

Welcome to the Pyfr24 documentation This Python package provides a simple interface to the Flightradar24 API, allowing you to fetch, plot and analyze flight data.

## Features

- **Flight data retrieval**: Access live flights, historical tracks and detailed flight information
- **Data export**: Export flight data in multiple formats (CSV, GeoJSON and KML)
- **Map visualization**: Generate flight path visualizations with customizable:
    - Background maps (CartoDB, OpenStreetMap, Stamen, ESRI)
    - Orientation (16:9 horizontal, 9:16 vertical or auto-detect)
    - High-quality output (300 DPI)
- **Flight analysis**: Create speed and altitude profile charts
- **Command-line interface**: Quick access to all features without writing code
- **Error handling**: Robust error handling and logging
- **API token management**: Flexible API token configuration

## Quick links

- [Installation guide](installation.md)
- [Quick start guide](usage/quickstart.md)
- [CLI reference](usage/cli.md)
- [Python API reference](usage/api.md)
- [Example usage](usage/examples.md)

## Requirements

- Python 3.8+
- Flightradar24 API subscription
- Required Python packages:
    - requests
    - geopandas
    - contextily
    - matplotlib
    - shapely
    - pandas

## Installation

```bash
pip install pyfr24
```

Or install directly from the repository:

```bash
git clone https://github.com/stiles/pyfr24.git
cd pyfr24
pip install -e .
```

## Basic usage

```python
from pyfr24 import FR24API

# Initialize the client
api = FR24API("your_api_token")

# Export flight data with custom settings
output_dir = api.export_flight_data(
    "39bebe6e",
    background='osm',        # Use OpenStreetMap background
    orientation='horizontal' # 16:9 aspect ratio (default)
)

# The output directory will contain:
# - data.csv: CSV of flight track points
# - points.geojson: GeoJSON of track points
# - line.geojson: GeoJSON LineString
# - track.kml: KML flight path
# - map.png: Map visualization
# - speed.png: Speed profile chart
# - altitude.png: Altitude profile chart
```

Or use the command-line interface:

```bash
# Export flight data with custom visualization
pyfr24 export-flight --flight-id 39bebe6e \
                     --background osm \
                     --orientation horizontal

# Get live flights for an aircraft
pyfr24 live-flights --registration N12345

# Get flight tracks
pyfr24 flight-tracks --flight-id 39a84c3c
```

For more detailed information, check out the [quick start guide](usage/quickstart.md). 