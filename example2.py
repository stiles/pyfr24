import os
import json
from pyfr24 import FR24API

def analyze_crash_flight(api, flight_id):
    """
    Retrieve and analyze flight track data for an incident.
    This reconstructs the flight's descent profile by sorting
    the ADS-B pings and printing key parameters.
    """
    try:
        # Get the flight tracks for the given flight ID.
        data = api.get_flight_tracks(flight_id)
    except Exception as e:
        print(f"Error retrieving flight tracks: {e}")
        return

    # Determine the structure of the response and extract the tracks.
    if isinstance(data, list):
        # If we got a list with a single dict that contains 'tracks', use that.
        if len(data) == 1 and isinstance(data[0], dict) and "tracks" in data[0]:
            tracks = data[0]["tracks"]
        else:
            tracks = data
    elif isinstance(data, dict):
        tracks = data.get("tracks", [])
    else:
        print("Unexpected data format")
        return

    if not tracks:
        print("No flight track data available for this flight.")
        return

    # Sort the tracks by timestamp using safe retrieval.
    sorted_tracks = sorted(tracks, key=lambda x: x.get("timestamp", ""))

    print("Reconstructed flight path data:")
    for point in sorted_tracks:
        timestamp = point.get("timestamp", "N/A")
        lat = point.get("lat", "N/A")
        lon = point.get("lon", "N/A")
        alt = point.get("alt", "N/A")
        speed = point.get("gspeed", "N/A")
        print(f"Time: {timestamp}, Lat: {lat}, Lon: {lon}, Alt: {alt} ft, Speed: {speed} knots")

    return sorted_tracks

if __name__ == "__main__":
    # Retrieve the API token from the environment variable.
    token = os.environ.get("FLIGHTRADAR_API_KEY")
    if not token:
        raise ValueError("FLIGHTRADAR_API_KEY environment variable not set.")

    # Initialize the FR24 API client.
    api = FR24API(token)

    # Example flight ID for a crash investigation use case.
    flight_id = "34242a02"

    # Analyze the flight to reconstruct the descent path.
    analyze_crash_flight(api, flight_id)