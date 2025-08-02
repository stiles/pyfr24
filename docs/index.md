# Pyfr24 documentation

Welcome to the Pyfr24 documentation. This Python package provides an interface to the Flightradar24 API for fetching, plotting and analyzing flight data.

## Features

- **Flight data retrieval**: Access live flights, historical tracks and flight information
- **Data export**: Export flight data in multiple formats (CSV, GeoJSON and KML)
- **Enhanced visualizations**: Publication-ready charts and maps with:
    - Professional chart design with clean typography and smart formatting
    - Multiple map backgrounds (CartoDB, OpenStreetMap, ESRI satellite/topo)
    - Timezone conversion with automatic DST handling
    - Human-readable time labels and date formatting
    - Orientation options (16:9 horizontal, 9:16 vertical or auto-detect)
    - High-quality output (300 DPI)
- **Flight analysis**: Create speed and altitude profile charts
- **Command-line interface**: Access features without writing code
- **Error handling**: Handle errors and log events
- **API token management**: Configure API tokens

## Quick links

- [Installation guide](installation.md)
- [Quick start guide](usage/quickstart.md)
- [Enhanced visualizations](features/enhanced-visualizations.md)
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

# Export flight data with enhanced features
output_dir = api.export_flight_data(
    "39bebe6e",
    background='esri-satellite',  # Satellite background
    orientation='horizontal',     # 16:9 aspect ratio (default)
    timezone='America/New_York'   # Convert to Eastern Time
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
# Export with enhanced features
pyfr24 smart-export --flight DL562 --date 2025-08-02 \
                    --background esri-satellite \
                    --timezone "America/New_York"

# Get live flights for an aircraft
pyfr24 live-flights --registration N12345

# Get flight tracks
pyfr24 flight-tracks --flight-id 39a84c3c
```

For more information, check out the [quick start guide](usage/quickstart.md). 