# CLI Reference

The Pyfr24 command-line interface provides quick access to all features without writing code.

## Common Options

These options are available for all commands:

- `-t, --token`: API token (can also be set via FLIGHTRADAR_API_KEY env var)
- `-l, --log-level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `-f, --log-file`: Log file path
- `-o, --output`: Output file path (JSON)

## Available Commands

### Flight Summary

Get flight summary information:
```bash
# Short form
pyfr24 flight-summary -F AA123 -f "2023-01-01" -t "2023-01-01"

# Long form
pyfr24 flight-summary --flight AA123 --from-date "2023-01-01" --to-date "2023-01-01"
```

### Live Flights

Get live flights for an aircraft registration:
```bash
# Short form
pyfr24 live-flights -R N12345

# Long form
pyfr24 live-flights --registration N12345
```

### Flight Tracks

Get flight tracks by ID:
```bash
# Short form
pyfr24 flight-tracks -i 39a84c3c

# Long form
pyfr24 flight-tracks --flight-id 39a84c3c
```

### Export Flight Data

Export flight data with various options:
```bash
# Basic export
pyfr24 export-flight -i 39a84c3c -o data/flight_39a84c3c

# With different background maps
pyfr24 export-flight -i 39a84c3c --background osm  # OpenStreetMap
pyfr24 export-flight -i 39a84c3c --background stamen  # Stamen Terrain
pyfr24 export-flight -i 39a84c3c --background esri  # ESRI World TopoMap

# With different orientations
pyfr24 export-flight -i 39a84c3c --orientation horizontal  # 16:9 aspect ratio
pyfr24 export-flight -i 39a84c3c --orientation vertical    # 9:16 aspect ratio
pyfr24 export-flight -i 39a84c3c --orientation auto       # Auto-detect
```

### Airline Information

Get airline information by ICAO code:
```bash
# Short form
pyfr24 airline-info -i AAL

# Long form
pyfr24 airline-info --icao AAL
```

### Airport Information

Get airport information by code:
```bash
# Short form
pyfr24 airport-info -c JFK

# Long form
pyfr24 airport-info --code JFK
```

### Flight Positions

Get flight positions within a bounding box:
```bash
# Short form
pyfr24 flight-positions -b "33.5,-118.8,34.5,-117.5"

# Long form
pyfr24 flight-positions --bounds "33.5,-118.8,34.5,-117.5"
```

### Flight IDs

Get flight IDs for an aircraft registration:
```bash
# Basic usage
pyfr24 flight-ids -R N216MH -f "2025-01-01" -t "2025-04-10"

# Save results to file
pyfr24 flight-ids -R N216MH -f "2025-01-01" -t "2025-04-10" -o flight_ids.json
```

## Getting Help

For detailed help on any command:
```bash
pyfr24 --help
pyfr24 <command> --help
``` 