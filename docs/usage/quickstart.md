# Quick Start Guide

This guide will help you get started with Pyfr24 quickly.

## API Token Setup

Before using Pyfr24, you'll need a Flightradar24 API token. You can provide your token in one of three ways:

1. **Command line argument**:
```bash
pyfr24 --token "your_api_token" flight-summary --flight BA123
```

2. **Environment variable**:
```bash
export FLIGHTRADAR_API_KEY="your_api_token"
pyfr24 flight-summary --flight BA123
```

3. **Interactive prompt**:
```bash
pyfr24 flight-summary --flight BA123
Please enter your Flightradar24 API token: your_api_token
```

## Basic Usage

### Using the CLI

Get flight summary:
```bash
pyfr24 flight-summary -F AA123 -f "2023-01-01" -t "2023-01-01"
```

Export flight data:
```bash
pyfr24 export-flight -i 39a84c3c -o data/flight_39a84c3c
```

### Using the Python API

```python
import os
from pyfr24 import FR24API

# Initialize the API client
token = os.environ.get("FLIGHTRADAR_API_KEY")
api = FR24API(token)

# Get live flights for a specific aircraft
live_flights = api.get_live_flights_by_registration("HL7637")

# Export flight data
output_dir = api.export_flight_data("39a84c3c")
print(f"Flight data exported to directory: {output_dir}")
```

For more detailed examples and features, check out the [Examples](examples.md) section. 