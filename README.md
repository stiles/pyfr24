# Pyfr24

[![Documentation Status](https://readthedocs.org/projects/pyfr24/badge/?version=latest)](https://pyfr24.readthedocs.io/en/latest/?badge=latest)

A Python client for the [Flightradar24 API](https://fr24api.flightradar24.com/) that provides an interface to fetch, plot and analyze flight data. The package includes both a Python API and a command-line interface for accessing flight data.

**Full documentation:** [https://pyfr24.readthedocs.io/](https://pyfr24.readthedocs.io/)

## Installation

```bash
# Install from PyPI
pip install pyfr24

# Or from source
git clone https://github.com/stiles/pyfr24.git
cd pyfr24
pip install -e .
```

## Basic usage

### Python API

```python
from pyfr24 import FR24API

# Initialize the client
api = FR24API("your_api_token")

# Get flight tracks for a specific flight ID
tracks = api.get_flight_tracks("39bebe6e")

# Export flight data
output_dir = api.export_flight_data(
    "39bebe6e",
    background='osm',        # OpenStreetMap background
    orientation='horizontal'  # 16:9 aspect ratio
)
```

**Full Python docs:** [https://pyfr24.readthedocs.io/en/latest/usage/api/](https://pyfr24.readthedocs.io/en/latest/usage/api/)

### Command-line interface

```bash
# Export flight data
pyfr24 export-flight --flight-id 39a84c3c --output-dir data/flight_39a84c3c

# Get live flights for an aircraft registration
pyfr24 live-flights --registration N12345

# Get flight positions within a bounding box (Los Angeles area)
pyfr24 flight-positions --bounds "33.5,-118.8,34.5,-117.5"
```

**Full CLI reference:** [https://pyfr24.readthedocs.io/en/latest/usage/cli/](https://pyfr24.readthedocs.io/en/latest/usage/cli/)

## API token

Your Flightradar24 API token can be provided:

1. Via environment variable:
   ```bash
   export FLIGHTRADAR_API_KEY="your_api_token"
   ```

2. As a command-line argument:
   ```bash
   pyfr24 --token "your_api_token" flight-summary --flight BA123
   ```

3. Through an interactive prompt when no token is provided

## Features

- Flight data retrieval (live flights, historical tracks and flight info)
- Data export in multiple formats (CSV, GeoJSON and KML)
- Map visualizations with multiple background options
- Speed and altitude profile charts
- Error handling and logging
- Testing

## Contributing

Contributions are welcome. Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass with `python run_tests.py`
5. Submit a pull request

## License

This project is licensed under the MIT License.
