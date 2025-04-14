# Flight Data Features

Pyfr24 provides comprehensive access to Flightradar24's flight data through several methods.

## Live Flight Tracking

Get real-time information about flights currently in the air:

```python
# Get live flights for a specific aircraft
live_flights = api.get_live_flights_by_registration("N458WN")

# Get flights within a geographic area
positions = api.get_flight_positions_light("33.5,-118.8,34.5,-117.5")
```

## Historical Flight Data

Access historical flight information:

```python
# Get flight summary for a specific flight number
summary = api.get_flight_summary_full(
    flights="AA123",
    flight_datetime_from="2023-01-01T00:00:00Z",
    flight_datetime_to="2023-01-01T23:59:59Z"
)

# Get flight tracks using flight ID
tracks = api.get_flight_tracks("39bebe6e")

# Get all flight IDs for an aircraft registration
flight_ids = api.get_flight_ids_by_registration(
    registration="N216MH",
    date_from="2025-01-01",
    date_to="2025-04-10"
)
```

## Flight Track Data

Flight track data includes:

- Timestamp
- Latitude and longitude
- Altitude
- Ground speed
- Vertical speed
- Track/heading
- Squawk code
- Callsign
- Data source

## Airline and Airport Information

Get information about airlines and airports:

```python
# Get airline information
airline = api.get_airline_light("AAL")

# Get airport information
airport = api.get_airport_full("LHR")
```

## Data Formats

Flight data can be accessed in multiple formats:

- JSON (API responses)
- CSV (exported track points)
- GeoJSON (points and lines)
- KML (flight paths)

## Error Handling

The API includes comprehensive error handling:

- Authentication errors
- Rate limit handling
- Not found errors
- Server errors
- Network errors

Example error handling:

```python
try:
    tracks = api.get_flight_tracks(flight_id)
except FR24NotFoundError:
    print(f"No data found for flight {flight_id}")
except FR24RateLimitError:
    print("Rate limit exceeded")
except FR24Error as e:
    print(f"API error: {e}")
``` 