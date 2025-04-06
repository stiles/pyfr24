import os
import json
from pyfr24 import FR24API
import pandas as pd

def main():
    # Read API token from environment.
    token = os.environ.get("FLIGHTRADAR_API_KEY")
    if not token:
        raise ValueError("FLIGHTRADAR_API_KEY environment variable not set.")
    
    api = FR24API(token)
    
    # Example A: Lookup live flights for a specific aircraft registration.
    # live_flights = api.get_live_flights_by_registration("N458WN")
    # print("Live Flights:")
    # print(json.dumps(live_flights, indent=2))
    
    # # Example B: Lookup basic flight summary for flight EK184 within a datetime range.
    # summary_light = api.get_flight_summary_light(
    #     flights="KE11",
    #     flight_datetime_from="2025-02-14T01:17:14",
    #     flight_datetime_to="2025-02-28T13:17:14"
    # )
    # print("Flight summary (light):")
    # print(json.dumps(summary_light, indent=2))
    
    # Example C: Get flight track details for a specific flight.
    # tracks = api.get_flight_tracks("39c5ea46")
    # print("Flight tracks:")
    # print(json.dumps(tracks, indent=2))

    # Example D: Export flight data to CSV and GeoJSON.
    flight_id = "39c59014"
    output_directory = api.export_flight_data(flight_id)
    print(f"Flight data exported to directory: {output_directory}")

if __name__ == "__main__":
    main()