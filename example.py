import os
import json
from pyfr24 import FR24API

def main():
    # Read API token from environment.
    token = os.environ.get("FLIGHTRADAR_API_KEY")
    if not token:
        raise ValueError("FLIGHTRADAR_API_KEY environment variable not set.")
    
    api = FR24API(token)
    
    # Example A: Lookup live flights for a specific aircraft registration.
    live_flights = api.get_live_flights_by_registration("HL7637")
    print("Live Flights:")
    print(json.dumps(live_flights, indent=2))
    
    # Example B: Lookup basic flight summary for flight EK184 within a datetime range.
    summary_light = api.get_flight_summary_light(
        flights="KE11",
        flight_datetime_from="2025-02-14T01:17:14",
        flight_datetime_to="2025-02-28T13:17:14"
    )
    print("Flight summary (light):")
    print(json.dumps(summary_light, indent=2))
    
    # Example C: Get flight track details for a specific flight.
    tracks = api.get_flight_tracks("39bebe6e")
    print("Flight tracks:")
    print(json.dumps(tracks, indent=2))

if __name__ == "__main__":
    main()
