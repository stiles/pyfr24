# Examples

This page provides usage examples to help you get the most out of Pyfr24.

## Basic data retrieval

### Getting flight tracks

```python
from pyfr24 import FR24API

api = FR24API("your_api_token")

# Get flight tracks by ID
tracks = api.get_flight_tracks("39bebe6e")
print(f"Found {len(tracks)} track points")

# Print the first track point
if tracks:
    print(tracks[0])
```

### Finding live flights

```python
from pyfr24 import FR24API

api = FR24API("your_api_token")

# Find live flights for an aircraft registration
flights = api.get_live_flights_by_registration("N12345")
for flight in flights.get("data", []):
    print(f"Flight {flight.get('callsign')} at position: {flight.get('lat')}, {flight.get('lon')}")
```

## Data export examples

### Export with custom settings

```python
from pyfr24 import FR24API

api = FR24API("your_api_token")

# Export with custom background and orientation
output_dir = api.export_flight_data(
    "39bebe6e",
    background='osm',        # OpenStreetMap
    orientation='vertical',  # 9:16 aspect ratio
    output_dir="custom_export"
)

print(f"Data exported to {output_dir}")
```

### Batch export multiple flights

```python
import os
from pyfr24 import FR24API

api = FR24API("your_api_token")

# List of flight IDs to export
flight_ids = ["39bebe6e", "39a84c3c", "39b845d8"]

for flight_id in flight_ids:
    try:
        output_dir = api.export_flight_data(
            flight_id,
            output_dir=f"batch_export/{flight_id}"
        )
        print(f"Exported {flight_id} to {output_dir}")
    except Exception as e:
        print(f"Error exporting {flight_id}: {e}")
```

## Case study: incident investigation

This example shows how to investigate flight incidents by retrieving and comparing flight data.

```python
import os
import json
import logging
from pyfr24 import FR24API, configure_logging

# Configure logging
configure_logging(level=logging.INFO, log_file="investigation.log")

def investigate_incident(api, flight_ids, date_from, date_to):
    """
    For each flight number or call sign, retrieve the flight summary, 
    extract the internal fr24_id and export flight track data.
    
    Returns a dictionary mapping each original flight ID to results
    containing the internal fr24_id, summary details and export directory.
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
        # Process each summary entry
        for entry in data:
            internal_id = entry.get("fr24_id")
            if not internal_id:
                print(f"No fr24_id found in summary entry: {entry}")
                continue
            try:
                # Create an output directory named using both identifiers
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
    
    # Flight numbers/callsigns from the scenario
    flight_ids = ["DL2983", "DO61", "AA5308"]
    # Define a time window covering the incident
    date_from = "2025-03-28T12:15:01Z"
    date_to   = "2025-03-28T23:18:01Z"
    
    results = investigate_incident(api, flight_ids, date_from, date_to)
    print("\nInvestigation results:")
    print(json.dumps(results, indent=2))

    # Save the investigation results to a JSON file
    with open("investigation_results.json", "w") as f:
        json.dump(results, f, indent=2)
```

## Basic data collection

This example shows how to retrieve and save flight information using the CLI.

```bash
#!/bin/bash

# Set your token as an environment variable
export FLIGHTRADAR_API_KEY="your_api_token"

# Create output directory
mkdir -p data

# Get flight summary for a specific flight
pyfr24 flight-summary --flight BA123 --from-date "2023-01-01" --to-date "2023-01-01" --output data/ba123_summary.json

# Check if the command was successful
if [ $? -eq 0 ]; then
    echo "Flight summary saved to data/ba123_summary.json"
    
    # Extract flight ID from the summary using jq (if available)
    if command -v jq &> /dev/null; then
        flight_id=$(jq -r '.data[0].fr24_id // empty' data/ba123_summary.json)
        
        if [ ! -z "$flight_id" ]; then
            echo "Found flight ID: $flight_id"
            
            # Export flight data using the extracted ID
            pyfr24 export-flight --flight-id "$flight_id" --output-dir "data/flight_$flight_id"
            echo "Flight data exported to data/flight_$flight_id"
        else
            echo "No flight ID found in summary"
        fi
    else
        echo "jq not found, skipping automatic ID extraction"
    fi
else
    echo "Error: $result['error']"
fi 