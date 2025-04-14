# Quick start guide

This guide provides a basic introduction to using Pyfr24 for accessing flight data.

## Installation

```bash
pip install pyfr24
```

## API token setup

Before using Pyfr24, you'll need a Flightradar24 API token. You can provide it in one of three ways:

1. Environment variable:
```bash
export FLIGHTRADAR_API_KEY="your_api_token"
```

2. Command-line argument:
```bash
pyfr24 --token "your_api_token" flight-summary --flight BA123
```

3. Interactive prompt (when no token is provided)

## Basic examples

### Python API

```python
import os
from pyfr24 import FR24API

# Get token from environment
token = os.environ.get("FLIGHTRADAR_API_KEY")
api = FR24API(token)

# Get live flights for an aircraft
live_flights = api.get_live_flights_by_registration("N12345")

# Get flight tracks
tracks = api.get_flight_tracks("39bebe6e")

# Export flight data
output_dir = api.export_flight_data(
    "39bebe6e",
    background='osm',
    orientation='horizontal'
)
print(f"Data exported to: {output_dir}")
```

### Command-line interface

```bash
# Get flight summary
pyfr24 flight-summary --flight AA123 --from-date "2023-01-01" --to-date "2023-01-01"

# Export flight data
pyfr24 export-flight --flight-id 39bebe6e --output-dir flight_data

# Get live flights
pyfr24 live-flights --registration N12345
```

## Next steps

- Explore the [Python API reference](api.md) for more details on available methods
- Check the [CLI reference](cli.md) for all command-line options
- Look at [examples](examples.md) for more advanced usage scenarios 