# Pyfr24

Pyfr24 is a simple Python client for the [Flightradar24 API](https://fr24api.flightradar24.com/). This package allows you to fetch, plot and store live flight data, flight summaries and past flight tracks. The API requires a subscription.

## Installation

Clone the repository and install the package in editable mode. Pyfr24 requires Python 3 and the following dependencies:
- requests
- pandas
- geopandas
- contextily

To install, run:
```bash
pip install -e .
```

## How to use

First, set the environment variable `FLIGHTRADAR_API_KEY` with your subscription key. For example:
```bash
export FLIGHTRADAR_API_KEY="your_subscription_key"
```

Then, import and use the package in your project:
```python
import os
import json
from pyfr24 import FR24API

# Get the API token from the environment
token = os.environ.get("FLIGHTRADAR_API_KEY")
if not token:
    raise ValueError("FLIGHTRADAR_API_KEY environment variable not set.")

# Initialize the API client.
api = FR24API(token)

# Example a: Get live flights for a specific aircraft registration.
live_flights = api.get_live_flights_by_registration("HL7637")
print(json.dumps(live_flights, indent=2))

# Example b: Get basic airline information by ICAO code.
airline_info = api.get_airline_light("AAL")
print(json.dumps(airline_info, indent=2))

# Example c: Get flight tracks for a specific flight based on the FR24 flight ID.
tracks = api.get_flight_tracks("39bebe6e")
print(json.dumps(tracks, indent=2))

# Example d: Export flight data.
# This creates a directory named after the flight ID containing:
#   - data.csv: CSV of flight track points
#   - points.geojson: GeoJSON of track points
#   - line.geojson: GeoJSON LineString connecting the points
#   - plot.png: An enhanced map plot of the flight path
output_dir = api.export_flight_data("39bebe6e")
print(f"Flight data exported to directory: {output_dir}")
```
You can also fetch detailed flight summaries and full airport data using the other available methods.

## Roadmap

This project is new and under development. Some features to tackle next: 

- **More API coverage**  
  Add support for more endpoints such as full flight positions, flight counts, historical endpoints and usage statistics

- **Improve error handling**  
  Enhance exception handling and logging and add support for retries in case of transient errors

- **Add asynchronous support**  
  Provide async methods using asyncio so users can integrate the client in asynchronous applications

- **Add a CLI tool**  
  Create a command-line interface for quick access to API functions without writing code

- **Better docs**  
  Improve docs with more examples and an API reference

- **Caching and rate limit handling**  
  Add caching support to reduce redundant API calls and build in rate limit awareness to prevent overuse

## Contributing

Contributions are welcome. Please fork the repository and submit a pull request. Make sure to add tests for your changes and run tests with:
```bash
pytest tests/
```

## License

This project is licensed under the Creative Commons license.