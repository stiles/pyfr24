# Pyfr24

Pyfr24 is a Python client for the [Flightradar24 API](https://fr24api.flightradar24.com/). This package allows you to fetch live flight data, flight summaries and flight tracks. The API requires a subscription key so you must have access to the Flightradar24 API.

## Installation

Clone the repository and install the package in editable mode. Pyfr24 requires Python 3 and the following dependency:
- requests

To install, run:
```bash
pip install -e .
```

## How to use

First, set the environment variable `FLIGHTRADAR_API_KEY` with your subscription key. For example:
```bash
export FLIGHTRADAR_API_KEY="your_subscription_key"
```

Then, import and use the package in your project:
```python
import os
import json
from pyfr24 import FR24API

# Get the API token from the environment
token = os.environ.get("FLIGHTRADAR_API_KEY")
if not token:
    raise ValueError("FLIGHTRADAR_API_KEY environment variable not set.")

# Initialize the API client.
api = FR24API(token)

# Example a: Get live flights for a specific aircraft registration.
live_flights = api.get_live_flights_by_registration("HL7637")
print(json.dumps(live_flights, indent=2))

# Example b: Get basic airline information by ICAO code.
# US carrier codes: https://aspm.faa.gov/aspmhelp/index/ASQP___Carrier_Codes_And_Names.html
airline_info = api.get_airline_light("AAL")
print(json.dumps(airline_info, indent=2))

# Example c: Get flight tracks (historical or live) for a specific flight based on the FR24 flight ID
# LA County Sheriff helicopter on April 5, 2025: https://www.flightradar24.com/N956LA/39c32d71
tracks = api.get_flight_tracks("39bebe6e")
print(json.dumps(tracks, indent=2))
```

You can also fetch detailed flight summaries and full airport data using the other available methods.

## Contributing

Contributions are welcome. Please fork the repository and submit a pull request. Make sure to add tests for your changes and run tests with:
```bash
pytest tests/
```

## License

This project is licensed under the MIT license.