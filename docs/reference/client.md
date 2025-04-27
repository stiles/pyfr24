# Client API Reference

## FR24API Class

The main class for interacting with the Flightradar24 API.

### Constructor

```python
FR24API(token=None)
```

**Parameters:**

- `token` (str, optional): API token. If not provided, will try to get from environment variables `FR24_API_TOKEN` or `FLIGHTRADAR_API_KEY`.

### Methods

#### Flight Data

##### get_flight_summary_light
```python
get_flight_summary_light(flights, flight_datetime_from, flight_datetime_to, **kwargs)
```
Get basic flight summary information.

**Parameters:**

- `flights` (str): Flight number or call sign
- `flight_datetime_from` (str): Start datetime in ISO format
- `flight_datetime_to` (str): End datetime in ISO format
- `**kwargs`: Additional parameters to pass to the API

##### get_flight_summary_full
```python
get_flight_summary_full(flights, flight_datetime_from, flight_datetime_to, **kwargs)
```
Get detailed flight summary information.

**Parameters:**

- `flights` (str): Flight number or call sign
- `flight_datetime_from` (str): Start datetime in ISO format
- `flight_datetime_to` (str): End datetime in ISO format
- `**kwargs`: Additional parameters to pass to the API

##### get_flight_tracks
```python
get_flight_tracks(flight_id)
```
Get flight tracks (ADS-B pings) using the flight ID.

**Parameters:**

- `flight_id` (str): Flightradar24 flight ID

##### get_live_flights_by_registration
```python
get_live_flights_by_registration(registration, bounds=None)
```
Get live flights filtered by aircraft registration.

**Parameters:**

- `registration` (str): Aircraft registration number
- `bounds` (str, optional): Geographic bounds to filter results

#### Data Export

##### export_flight_data
```python
export_flight_data(flight_id, output_dir=None, background='carto', orientation='horizontal')
```
Export flight track data to multiple formats and create visualizations.

**Parameters:**

- `flight_id` (str): Flightradar24 flight ID
- `output_dir` (str, optional): Output directory path
- `background` (str, optional): Background map provider ('carto', 'osm', 'stamen', 'esri')
- `orientation` (str, optional): Plot orientation ('horizontal', 'vertical', 'auto')

**Returns:**

- str: Path to the output directory

#### Airline and Airport Information

##### get_airline_light
```python
get_airline_light(icao)
```
Get basic airline info by ICAO code.

**Parameters:**

- `icao` (str): Airline ICAO code

##### get_airport_full
```python
get_airport_full(code)
```
Get detailed airport info by IATA or ICAO code.

**Parameters:**

- `code` (str): Airport IATA or ICAO code

#### Flight Positions and IDs

##### get_flight_positions_light
```python
get_flight_positions_light(bounds, **kwargs)
```
Get real-time flight positions within specified bounds.

**Parameters:**

- `bounds` (str): Geographic bounds in format "lat1,lon1,lat2,lon2"
- `**kwargs`: Additional parameters to pass to the API

##### get_flight_ids_by_registration
```python
get_flight_ids_by_registration(registration, date_from, date_to, offset=0, limit=20, max_pages=5)
```
Get all flight IDs for a specific aircraft registration within a date range.

**Parameters:**

- `registration` (str): Aircraft registration number
- `date_from` (str): Start date in ISO format
- `date_to` (str): End date in ISO format
- `offset` (int, optional): Starting offset for pagination
- `limit` (int, optional): Number of results per page
- `max_pages` (int, optional): Maximum number of pages to fetch

**Returns:**

- list: List of flight IDs (fr24_id)

### Error Handling

The client includes comprehensive error handling with custom exception classes:

```python
try:
    api = FR24API(token)
    data = api.get_flight_tracks(flight_id)
except FR24AuthenticationError:
    print("Authentication failed")
except FR24NotFoundError:
    print("Flight not found")
except FR24RateLimitError:
    print("Rate limit exceeded")
except FR24Error as e:
    print(f"API error: {e}")
```

### Logging

The client includes built-in logging that can be configured:

```python
import logging
from pyfr24 import configure_logging

configure_logging(
    level=logging.DEBUG,
    log_file="pyfr24.log",
    log_format="%(asctime)s - %(levelname)s - %(message)s"
) 