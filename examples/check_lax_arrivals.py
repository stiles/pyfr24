#!/usr/bin/env python3
"""
Check which LAX arrivals passed over Lennox Middle School.

This script:
1. Tries to fetch LAX arrivals from FR24's public API
2. Falls back to hardcoded list if blocked
3. For each flight, gets track data and checks proximity to Lennox HS
"""

import os
import sys
import requests
import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json

from pyfr24 import FR24API, configure_logging
import logging

# Lennox Middle School location
LENNOX_MS = {
    'lat': 33.935972,
    'lon': -118.366503,
    'radius_nm': 4.0
}

# Hardcoded fallback list from FR24 website (Nov 2, 2025, 8:20-10:15am PT)
FALLBACK_CALLSIGNS = [
    "UA5897", "EJA506", "DL3979", "KE17", "UA4649", "UA5390", "UA6960", "AA1660",
    "QT7086", "AA779", "DL1216", "WN2159", "AA6198", "AA6290", "AS2075", "AA2211",
    "DL306", "DL2085", "AA3122", "AA6479", "DL996", "AA1663", "DL1087", "DL2337",
    "DL4106", "DL3515", "DL2947", "F92445", "UA2113", "UA2434", "UA357", "DL2110",
    "AA2690", "AA6191", "MU583", "UA306", "DL3852", "UA2600", "WN1718", "WN3057",
    "K4235", "AS1316", "B6801", "CX884", "UA754", "AA6420", "AS2441", "UA2602",
    "AA6462", "AA4885", "UA5408", "DL538", "F94233", "UA2150", "TN8", "DL891",
    "WN188", "Y41712", "LXJ580", "AA979", "AA171", "F92341", "AA2970", "AS3366",
    "AS3480", "UA4650", "AA598", "AA772", "B6287", "UA1346", "JL62", "UA1638",
    "UA5542", "DL479", "NK153", "AM646", "DL484", "TN102", "AA878", "AS3304",
    "SIS94", "AS581", "AS2163", "JL16", "NH6", "UA2361", "DL898", "DL1421",
    "WN3570", "AA1928", "CA987", "DL462", "UA1220", "WN3875", "WN4122", "DL1628",
    "F81888", "WN1739", "AA4907", "DL450", "G4283", "AA3202"
]


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in nautical miles."""
    R = 3440.065  # Earth radius in nautical miles
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def try_fetch_lax_arrivals(date_str, time_from, time_to):
    """
    Try to fetch LAX arrivals from FR24's public API.
    Returns list of flight numbers or None if blocked.
    """
    print("\n🔍 Attempting to fetch LAX arrivals from FR24 API...")
    
    try:
        # Convert to timestamp
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        tz = ZoneInfo('America/Los_Angeles')
        dt_local = dt.replace(tzinfo=tz)
        timestamp = int(dt_local.timestamp())
        
        # Try the public endpoint (similar to what the website uses)
        url = "https://api.flightradar24.com/common/v1/airport.json"
        params = {
            'code': 'LAX',
            'plugin[]': '',
            'plugin-setting[schedule][mode]': 'arrivals',
            'plugin-setting[schedule][timestamp]': timestamp,
            'page': -4,
            'limit': 100,
            'fleet': ''
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Try to extract flight data
            schedule_data = data.get('result', {}).get('response', {}).get('airport', {}).get('pluginData', {}).get('schedule', {}).get('arrivals', {}).get('data', [])
            
            if schedule_data:
                flights = []
                for flight in schedule_data:
                    flight_num = flight.get('flight', {}).get('identification', {}).get('number', {}).get('default')
                    if flight_num:
                        flights.append(flight_num)
                
                if flights:
                    print(f"✅ Successfully fetched {len(flights)} arrivals from API")
                    return flights
        
        print(f"⚠️  API returned status {response.status_code}, using fallback list")
        return None
        
    except Exception as e:
        print(f"⚠️  Could not fetch from API ({e}), using fallback list")
        return None


def check_flight_overhead(api, flight_num, date_str, location, time_window_utc):
    """Check if a flight passed over the location during the specified time window."""
    try:
        # Look up flight using smart_export (without actually exporting)
        result = api.smart_export_flight(
            flight_number=flight_num,
            date=date_str,
            auto_select='latest'
        )
        
        if not result.get('selected'):
            return None
        
        flight_id = result['selected'].get('fr24_id') or result['selected'].get('id')
        
        # Get tracks
        tracks_response = api.get_flight_tracks(flight_id)
        
        # Parse tracks
        if isinstance(tracks_response, list):
            tracks = tracks_response[0].get('tracks', []) if tracks_response else []
        elif isinstance(tracks_response, dict):
            tracks = tracks_response.get('tracks', [])
        else:
            tracks = []
        
        if not tracks:
            return None
        
        # Filter tracks to only those within time window
        from datetime import datetime
        window_start = datetime.fromisoformat(time_window_utc[0].replace('Z', '+00:00'))
        window_end = datetime.fromisoformat(time_window_utc[1].replace('Z', '+00:00'))
        
        tracks_in_window = []
        for track in tracks:
            timestamp = track.get('timestamp')
            if timestamp:
                try:
                    track_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    if window_start <= track_time <= window_end:
                        tracks_in_window.append(track)
                except:
                    pass
        
        if not tracks_in_window:
            return None
        
        # Find closest approach during the time window
        min_distance = float('inf')
        closest_point = None
        
        for track in tracks_in_window:
            lat = track.get('lat')
            lon = track.get('lon')
            if lat and lon:
                dist = haversine_distance(location['lat'], location['lon'], lat, lon)
                if dist < min_distance:
                    min_distance = dist
                    closest_point = track
        
        # Return if within radius
        if min_distance < location['radius_nm']:
            return {
                'flight': flight_num,
                'flight_id': flight_id,
                'distance_nm': round(min_distance, 2),
                'closest_point': closest_point,
                'altitude_ft': closest_point.get('alt'),
                'time': closest_point.get('timestamp'),
                'total_tracks': len(tracks),
                'tracks_in_window': len(tracks_in_window)
            }
        
        return None
        
    except Exception as e:
        # Don't print errors for flights not found (expected for some)
        if "No flights found" not in str(e):
            print(f"  ⚠️  {flight_num}: {e}")
        return None


def main():
    print("="*80)
    print("LAX Arrivals Overhead Checker")
    print("="*80)
    print(f"Location: Lennox Middle School")
    print(f"Coordinates: {LENNOX_MS['lat']}, {LENNOX_MS['lon']}")
    print(f"Search radius: {LENNOX_MS['radius_nm']} nautical miles")
    print(f"Date: November 2, 2025, 8:20am - 10:15am PT")
    print("="*80)
    
    # Get API token
    token = os.getenv('FLIGHTRADAR_API_KEY')
    if not token:
        print("\n❌ Error: Set FLIGHTRADAR_API_KEY environment variable")
        sys.exit(1)
    
    configure_logging(level=logging.WARNING)
    api = FR24API(token)
    
    # Historical data - use the hardcoded list from FR24 website
    date_str = "2025-11-02"
    time_from = "08:20:00"
    time_to = "10:15:00"
    
    # For historical data, we need to use the list you got from the FR24 website
    # The API only returns current/live arrivals, not historical ones
    print(f"\n📋 Using historical arrival list ({len(FALLBACK_CALLSIGNS)} flights)")
    print("   (Historical data from FR24 website for Nov 2, 2025, 8:20-10:15am PT)")
    flight_numbers = FALLBACK_CALLSIGNS
    
    # Uncomment this to try fetching current arrivals instead:
    # flight_numbers = try_fetch_lax_arrivals(date_str, time_from, time_to)
    # if not flight_numbers:
    #     flight_numbers = FALLBACK_CALLSIGNS
    
    # Define time window in UTC
    # 8:20am PT = 16:20 UTC, 10:15am PT = 18:15 UTC (PST is UTC-8)
    time_window_utc = ("2025-11-02T16:20:00Z", "2025-11-02T18:15:00Z")
    
    print(f"\n⏰ Time window: {time_from} - {time_to} PT")
    print(f"   (UTC: {time_window_utc[0]} - {time_window_utc[1]})")
    
    # Check each flight
    print(f"\n🔍 Checking {len(flight_numbers)} flights...")
    print("(This may take a while - checking each flight's track data)\n")
    
    overhead_flights = []
    checked = 0
    
    for i, flight_num in enumerate(flight_numbers, 1):
        print(f"[{i}/{len(flight_numbers)}] {flight_num}...", end=' ', flush=True)
        
        result = check_flight_overhead(api, flight_num, date_str, LENNOX_MS, time_window_utc)
        checked += 1
        
        if result:
            overhead_flights.append(result)
            print(f"✓ OVERHEAD ({result['distance_nm']} nm at {result['altitude_ft']} ft, {result['tracks_in_window']}/{result['total_tracks']} points in window)")
        else:
            print("✗")
    
    # Summary
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print(f"Flights checked: {checked}")
    print(f"Passed overhead: {len(overhead_flights)}")
    
    if overhead_flights:
        print(f"\nFlights that passed within {LENNOX_MS['radius_nm']} nm of Lennox HS:")
        print("-" * 80)
        
        # Sort by time
        for flight in sorted(overhead_flights, key=lambda x: x['time']):
            # Convert UTC to PT for display
            from datetime import datetime
            from zoneinfo import ZoneInfo
            utc_time = datetime.fromisoformat(flight['time'].replace('Z', '+00:00'))
            pt_time = utc_time.astimezone(ZoneInfo('America/Los_Angeles'))
            time_str = pt_time.strftime('%I:%M:%S %p PT')
            
            print(f"  {flight['flight']:8s}  {flight['distance_nm']:5.2f} nm  "
                  f"{flight['altitude_ft']:6.0f} ft  {time_str}  "
                  f"({flight['tracks_in_window']} points)")
        
        # Save results
        output_file = 'LENNOX_MS_overflights.json'
        with open(output_file, 'w') as f:
            json.dump(overhead_flights, f, indent=2)
        print(f"\n💾 Results saved to: {output_file}")
        
        # Suggest next steps
        print(f"\n📊 To export full data for these flights, run:")
        print(f"   pyfr24 smart-export --flight FLIGHT_NUM --date {date_str} \\")
        print(f"       --timezone America/Los_Angeles --background esri-satellite")
    else:
        print("\n⚠️  No flights found within the search radius.")
        print("   Try increasing --radius or check the date/time window.")


if __name__ == '__main__':
    main()

