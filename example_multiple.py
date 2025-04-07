import os
import json
import logging
from pyfr24 import FR24API, configure_logging, FR24Error, FR24NotFoundError

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
        except FR24NotFoundError:
            print(f"No flight summary found for {fid}")
            continue
        except FR24Error as e:
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
            except FR24NotFoundError:
                print(f"No flight tracks found for {fid} (internal id: {internal_id})")
            except FR24Error as e:
                print(f"Error exporting flight tracks for {fid} (internal id: {internal_id}): {e}")
    return results

if __name__ == "__main__":
    # Configure logging
    configure_logging(level=logging.INFO, log_file="investigation.log")
    
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