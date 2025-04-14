# Pyfr24

Pyfr24 is a Python client for the [Flightradar24 API](https://fr24api.flightradar24.com/). This package provides a simple interface to fetch, plot and analyze flight data, including live flights, historical tracks and detailed flight information. With Pyfr24, you can easily investigate incidents, export flight data in multiple formats (CSV, GeoJSON, KML) and generate quick flight path plots. The package includes both a Python API and a command-line interface for quick access to flight data without writing code. The API requires a Flightradar24 subscription.

## Features

- Flight data retrieval
- Live flight tracking
- Flight track history
- Airline and airport information
- Export flight data to CSV, GeoJSON, KML and plot
- Error handling and logging
- Command-line interface
- Customizable map visualization:
  - Multiple background options (CartoDB, OpenStreetMap, Stamen, ESRI)
  - Flexible orientation options:
    - Horizontal (16:9) - Default, ideal for east-west flights
    - Vertical (9:16) - Better for north-south flights
    - Auto - Automatically selects based on flight path direction
  - High-quality output (300 DPI)
  - Clean, modern styling with orange flight path

## Installation

Clone the repository and install the package in editable mode. Pyfr24 requires Python 3 and the following dependencies:
- requests
- geopandas
- contextily
- matplotlib
- shapely
- pandas

To install, run:
```bash
pip install -e .
```

Or install directly from PyPI:
```bash
pip install pyfr24
```

## How to use

### API Token

You can provide your Flightradar24 API token in one of three ways:

1. **Command line argument** (easiest for one-time use):
```bash
pyfr24 --token "your_api_token" flight-summary --flight BA123 --from-date "2023-01-01T00:00:00Z" --to-date "2023-01-01T23:59:59Z"
```

2. **Environment variable** (good for repeated use):
```bash
export FLIGHTRADAR_API_KEY="your_api_token"
pyfr24 flight-summary --flight BA123 --from-date "2023-01-01T00:00:00Z" --to-date "2023-01-01T23:59:59Z"
```

3. **Interactive prompt** (when no token is provided):
```bash
pyfr24 flight-summary --flight BA123 --from-date "2023-01-01T00:00:00Z" --to-date "2023-01-01T23:59:59Z"
Please enter your Flightradar24 API token: your_api_token
```

### Using the Python API

Import and use the package in your project:
```python
import os
import json
from pyfr24 import FR24API, configure_logging

# Configure logging (optional)
configure_logging(level=logging.INFO, log_file="pyfr24.log")

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

# Example D: Export flight data.
# This creates a directory named after the flight ID containing:
#   - data.csv: CSV of flight track points
#   - points.geojson: GeoJSON of track points
#   - line.geojson: GeoJSON LineString connecting the points
#   - track.kml: Flight path in KML format
#   - map.png: Map visualization of the flight path (16:9 by default)
#   - speed.png: Line chart of speed over time
#   - altitude.png: Line chart of altitude over time
output_dir = api.export_flight_data("39bebe6e")
print(f"Flight data exported to directory: {output_dir}")

# Export with different background maps
output_dir = api.export_flight_data("39bebe6e", background='osm')  # OpenStreetMap
output_dir = api.export_flight_data("39bebe6e", background='stamen')  # Stamen Terrain
output_dir = api.export_flight_data("39bebe6e", background='esri')  # ESRI World TopoMap
# Default is CartoDB Positron (light gray)

# Export with different map orientations
output_dir = api.export_flight_data("39bebe6e", orientation='horizontal')  # 16:9 aspect ratio (default)
output_dir = api.export_flight_data("39bebe6e", orientation='vertical')    # 9:16 aspect ratio
output_dir = api.export_flight_data("39bebe6e", orientation='auto')       # Choose based on flight path

# Combine background and orientation options
output_dir = api.export_flight_data(
    "39bebe6e",
    background='osm',       # Use OpenStreetMap background
    orientation='vertical'  # 9:16 aspect ratio for north-south flights
)

# Get airline information
airline = api.get_airline_info("BAW")

# Get airport information
airport = api.get_airport_info("LHR")
```
You can also fetch detailed flight summaries and full airport data using the other available methods.

### Using the command-line interface

Pyfr24 provides a command-line interface for quick access to the API. All commands support both long and short option forms:

```bash
# Get flight summary
pyfr24 flight-summary -F AA123 -f "2023-01-01" -t "2023-01-01"
# or
pyfr24 flight-summary --flight AA123 --from-date "2023-01-01" --to-date "2023-01-01"

# Get live flights for an aircraft
pyfr24 live-flights -R N12345
# or
pyfr24 live-flights --registration N12345

# Get flight tracks
pyfr24 flight-tracks -i 39a84c3c
# or
pyfr24 flight-tracks --flight-id 39a84c3c

# Export flight data
pyfr24 export-flight -i 39a84c3c -o data/flight_39a84c3c
# or
pyfr24 export-flight --flight-id 39a84c3c --output-dir data/flight_39a84c3c

# Export with different background maps
pyfr24 export-flight -i 39a84c3c --background osm  # OpenStreetMap
pyfr24 export-flight -i 39a84c3c --background stamen  # Stamen Terrain
pyfr24 export-flight -i 39a84c3c --background esri  # ESRI World TopoMap
# Default is CartoDB Positron (light gray)

# Export with different map orientations
pyfr24 export-flight -i 39a84c3c --orientation horizontal  # 16:9 aspect ratio (default)
pyfr24 export-flight -i 39a84c3c --orientation vertical    # 9:16 aspect ratio
pyfr24 export-flight -i 39a84c3c --orientation auto       # Choose based on flight path

# Combine background and orientation options
pyfr24 export-flight -i 39a84c3c \
    --background osm \
    --orientation vertical \
    --output-dir data/flight_39a84c3c

# Get airline information
pyfr24 airline-info -i AAL
# or
pyfr24 airline-info --icao AAL

# Get airport information
pyfr24 airport-info -c JFK
# or
pyfr24 airport-info --code JFK

# Get flight positions within a bounding box (Los Angeles area)
pyfr24 flight-positions -b "33.5,-118.8,34.5,-117.5"
# or
pyfr24 flight-positions --bounds "33.5,-118.8,34.5,-117.5"

# Get flight IDs for an aircraft registration
pyfr24 flight-ids -R N216MH -f "2025-01-01" -t "2025-04-10"
# or
pyfr24 flight-ids --registration N216MH --from-date "2025-01-01" --to-date "2025-04-10"
# Save results to a file
pyfr24 flight-ids -R N216MH -f "2025-01-01" -t "2025-04-10" -o flight_ids.json
```

Common options available for all commands:
- `-t, --token`: API token (can also be set via FLIGHTRADAR_API_KEY env var)
- `-l, --log-level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `-f, --log-file`: Log file path
- `-o, --output`: Output file path (JSON)

For more options and detailed help, use:
```bash
pyfr24 --help
pyfr24 flight-summary --help
```

## Error handling

The client includes robust error handling with custom exception classes:

```python
from pyfr24 import FR24API, FR24AuthenticationError, FR24NotFoundError

try:
    api = FR24API("your_token")
    data = api.get_flight_summary_light(
        flights="AA123",
        flight_datetime_from="2023-01-01T00:00:00Z",
        flight_datetime_to="2023-01-01T23:59:59Z"
    )
except FR24AuthenticationError as e:
    print(f"Authentication error: {e}")
except FR24NotFoundError as e:
    print(f"Flight not found: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Logging

The client includes a logging configuration that can be customized:

```python
import logging
from pyfr24 import configure_logging

# Configure logging with default settings
configure_logging()

# Configure logging with custom settings
configure_logging(
    level=logging.DEBUG,
    log_file="pyfr24.log",
    log_format="%(asctime)s - %(levelname)s - %(message)s"
)
```

## Case study: incident investigation

Imagine you receive word that a Delta flight, DL2983, took off from DCA and came close to a military jet, D061, flying near the airport. Later, you learn it was actually an American Eagle flight, AA5308, that had a closer call. You can use Pyfr24 to investigate this incident by comparing flight summaries and tracking data. 

For each reported flight, you can:

- Retrieve the flight summary to obtain the internal fr24_id for each flight and aircraft.
- Export the flight tracks (CSV, GeoJSON and a quick plot for reference) for further analysis. The export functionality automatically saves files under a directory structure of the form data/flight_id.
- Compare the exported maps and data to determine which flight path came closest to the military jet.

Here's an example script for such an scenario:

``` python
import os
import json
from pyfr24 import FR24API, configure_logging

# Configure logging
configure_logging(level=logging.INFO, log_file="investigation.log")

def investigate_incident(api, flight_ids, date_from, date_to):
    """
    For each flight (by reported flight number or call sign),
    retrieve the flight summary, extract the internal "fr24_id" and
    then export flight track data using that ID.
    
    Returns a dictionary mapping each original flight ID to a list
    of results containing the internal fr24_id, summary details and export directory.
    """
    results = {}
    for fid in flight_ids:
        print(f"\nProcessing flight: {fid}")
        try:
            summary = api.get_flight_summary_full(
                flights=fid, 
                flight_datetime_from=date_from, 
                flight_datetime_to=date_to
            )
            print(f"Summary for {fid}:")
            print(json.dumps(summary, indent=2))
        except Exception as e:
            print(f"Error fetching summary for {fid}: {e}")
            continue

        data = summary.get("data", [])
        if not data:
            print(f"No summary data returned for flight {fid}")
            continue

        results[fid] = []
        # Process each summary entry (if more than one, there might be multiple segments)
        for entry in data:
            internal_id = entry.get("fr24_id")
            if not internal_id:
                print(f"No fr24_id found in summary entry: {entry}")
                continue
            try:
                # Create an output directory named using both the reported flight and its internal ID.
                export_dir = api.export_flight_data(internal_id, output_dir=f"data/{fid}_{internal_id}")
                print(f"Flight tracks for {fid} (internal id: {internal_id}) exported to: {export_dir}")
                results[fid].append({
                    "fr24_id": internal_id,
                    "summary": entry,
                    "export_dir": export_dir
                })
            except Exception as e:
                print(f"Error exporting flight tracks for {fid} (internal id: {internal_id}): {e}")
    return results

if __name__ == "__main__":
    token = os.environ.get("FLIGHTRADAR_API_KEY")
    if not token:
        raise ValueError("FLIGHTRADAR_API_KEY environment variable not set.")
    
    api = FR24API(token)
    
    # Flight numbers/callsigns from the scenario.
    flight_ids = ["DL2983", "DO61", "AA5308"]
    # Define a time window covering the incident.
    date_from = "2025-03-28T12:15:01Z"
    date_to   = "2025-03-28T23:18:01Z"
    
    investigation_results = investigate_incident(api, flight_ids, date_from, date_to)
    print("\nInvestigation results:")
    print(json.dumps(investigation_results, indent=2))

    # Save the investigation results to a JSON file.
    results_file = "investigation_results.json"
    with open(results_file, "w") as f:
        json.dump(investigation_results, f, indent=2)
    print(f"Investigation results saved to {results_file}")
```

## Testing

The package includes a comprehensive test suite. To run the tests:

```bash
# From the project root
python run_tests.py
```

## Roadmap

This project is under development. Some features to tackle next: 

- **More API coverage**  
  Add support for more endpoints such as full flight positions, flight counts, historical endpoints and usage statistics

- **Add asynchronous support**  
  Provide async methods using asyncio so users can integrate the client in asynchronous applications

- **Caching and rate limit handling**  
  Add caching support to reduce redundant API calls and build in rate limit awareness to prevent overuse

- **Better docs**  
  Improve docs with more examples and an API reference

## Contributing

Contributions are welcome. Please fork the repository and submit a pull request. Make sure to add tests for your changes and run tests with:
```bash
python run_tests.py
```

## License

This project is licensed under the MIT License.
