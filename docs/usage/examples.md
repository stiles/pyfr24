# Examples

## Case Study: Incident Investigation

This example shows how to investigate a potential incident involving multiple flights near an airport.

```python
import os
import json
import logging
from pyfr24 import FR24API, configure_logging

def investigate_incident(api, flight_ids, date_from, date_to):
    """
    For each flight (by reported flight number or call sign),
    retrieve the flight summary, extract the internal "fr24_id" and
    then export flight track data using that ID.
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
                # Export flight data with both reported flight ID and internal ID
                export_dir = api.export_flight_data(
                    internal_id, 
                    output_dir=f"data/{fid}_{internal_id}"
                )
                print(f"Flight tracks exported to: {export_dir}")
                results[fid].append({
                    "fr24_id": internal_id,
                    "summary": entry,
                    "export_dir": export_dir
                })
            except Exception as e:
                print(f"Error exporting tracks for {fid}: {e}")
    return results

if __name__ == "__main__":
    # Configure logging
    configure_logging(level=logging.INFO, log_file="investigation.log")
    
    token = os.environ.get("FLIGHTRADAR_API_KEY")
    if not token:
        raise ValueError("FLIGHTRADAR_API_KEY environment variable not set.")
    
    api = FR24API(token)
    
    # Flight numbers/callsigns to investigate
    flight_ids = ["DL2983", "DO61", "AA5308"]
    # Time window for the incident
    date_from = "2025-03-28T12:15:01Z"
    date_to   = "2025-03-28T23:18:01Z"
    
    results = investigate_incident(api, flight_ids, date_from, date_to)
    
    # Save investigation results
    with open("investigation_results.json", "w") as f:
        json.dump(results, f, indent=2)
```

## Basic Data Collection

This example shows how to collect basic flight data:

```python
import os
import json
from pyfr24 import FR24API, configure_logging

# Configure logging
configure_logging(level=logging.INFO, log_file="example.log")

token = os.environ.get("FLIGHTRADAR_API_KEY")
api = FR24API(token)

# Get live flights for an aircraft
live_flights = api.get_live_flights_by_registration("N458WN")
print("Live Flights:", json.dumps(live_flights, indent=2))

# Get flight summary
summary = api.get_flight_summary_full(
    flights="DO61",
    flight_datetime_from="2025-03-28T00:00:00",
    flight_datetime_to="2025-03-28T23:59:59",
)
print("Flight summary:", json.dumps(summary, indent=2))

# Get and export flight tracks
flight_id = "39a8364d"
tracks = api.get_flight_tracks(flight_id)
print("Flight tracks:", json.dumps(tracks, indent=2))

# Export flight data with visualizations
output_directory = api.export_flight_data(
    flight_id,
    background='osm',  # Use OpenStreetMap background
    orientation='auto'  # Auto-detect best orientation
)
print(f"Flight data exported to: {output_directory}")
```

## Error Handling Example

This example demonstrates proper error handling:

```python
from pyfr24 import (
    FR24API, FR24Error, FR24AuthenticationError, 
    FR24NotFoundError, FR24RateLimitError
)

def safe_get_flight_data(api, flight_id):
    try:
        # Try to get flight tracks
        tracks = api.get_flight_tracks(flight_id)
        
        # Export the data if tracks were found
        output_dir = api.export_flight_data(
            flight_id,
            background='carto',
            orientation='auto'
        )
        return {"success": True, "data": tracks, "output_dir": output_dir}
        
    except FR24AuthenticationError:
        return {"success": False, "error": "Invalid API token"}
        
    except FR24NotFoundError:
        return {"success": False, "error": f"No data found for flight {flight_id}"}
        
    except FR24RateLimitError:
        return {"success": False, "error": "Rate limit exceeded"}
        
    except FR24Error as e:
        return {"success": False, "error": str(e)}
        
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

# Usage
api = FR24API(os.environ.get("FLIGHTRADAR_API_KEY"))
result = safe_get_flight_data(api, "39a8364d")

if result["success"]:
    print(f"Data exported to: {result['output_dir']}")
else:
    print(f"Error: {result['error']}")
``` 