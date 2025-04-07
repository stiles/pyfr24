import os
import json
import logging
from pyfr24 import FR24API, configure_logging, FR24Error, FR24AuthenticationError, FR24NotFoundError

def main():
    # Configure logging
    configure_logging(level=logging.INFO, log_file="example.log")
    
    # Read API token from environment.
    token = os.environ.get("FLIGHTRADAR_API_KEY")
    if not token:
        raise ValueError("FLIGHTRADAR_API_KEY environment variable not set.")
    
    api = FR24API(token)
    
    # Example A: Lookup live flights for a specific aircraft registration.
    try:
        live_flights = api.get_live_flights_by_registration("N458WN")
        print("Live Flights:")
        print(json.dumps(live_flights, indent=2))
    except FR24NotFoundError:
        print("No live flights found for registration N458WN")
    except FR24Error as e:
        print(f"Error fetching live flights: {e}")
    
    # Example B: Lookup a flight summary for an aircraft within a datetime range.
    try:
        summary_light = api.get_flight_summary_full(
            flights="DO61",
            flight_datetime_from="2025-03-28T00:00:00",
            flight_datetime_to="2025-03-28T23:59:59",
        )
        print("Flight summary (full):")
        print(json.dumps(summary_light, indent=2))
    except FR24NotFoundError:
        print("No flight summary found for DO61")
    except FR24Error as e:
        print(f"Error fetching flight summary: {e}")
    
    # Example C: Get flight track details for a specific flight.
    try:
        tracks = api.get_flight_tracks("39a8364d")
        print("Flight tracks:")
        print(json.dumps(tracks, indent=2))
    except FR24NotFoundError:
        print("No flight tracks found for flight ID 39a8364d")
    except FR24Error as e:
        print(f"Error fetching flight tracks: {e}")

    # Example D: Export flight data to CSV and GeoJSON.
    try:
        flight_id = "39a8364d"
        output_directory = api.export_flight_data(flight_id)
        print(f"Flight data exported to directory: {output_directory}")
    except FR24NotFoundError:
        print("No flight data found for flight ID 39a8364d")
    except FR24Error as e:
        print(f"Error exporting flight data: {e}")

if __name__ == "__main__":
    main()