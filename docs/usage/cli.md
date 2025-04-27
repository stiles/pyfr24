# CLI reference

The Pyfr24 command-line interface provides quick access to all features without writing code.

## Common options

These options are available for all commands:

- `-t, --token`: API token (can also be set via FLIGHTRADAR_API_KEY env var)
- `-l, --log-level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `-f, --log-file`: Log file path
- `-o, --output`: Output file path (JSON)

## Available commands

### Flight summary

Get flight summary information:
```bash
# Short form
pyfr24 flight-summary -F F94371 -f "2025-04-18" -t "2025-04-18"

# Long form
pyfr24 flight-summary --flight F94371 --from-date "2025-04-18" --to-date "2025-04-18"

# Example response:
{
  "data": [
    {
      "fr24_id": "39f406c4",
      "flight": "F94371",
      "callsign": "FFT4371",
      "operating_as": "FFT",
      "painted_as": "FFT",
      "type": "A20N",
      "reg": "N390FR",
      "orig_icao": "KDEN",
      "datetime_takeoff": "2025-04-18T16:25:31Z",
      "dest_icao": "KSNA",
      "dest_icao_actual": "KSNA",
      "datetime_landed": "2025-04-18T18:26:53Z",
      "hex": "A48356",
      "first_seen": "2025-04-18T16:05:23Z",
      "last_seen": "2025-04-18T18:27:52Z",
      "flight_ended": false
    }
  ]
}
```

### Live flights

Get live flights for an aircraft registration:
```bash
# Short form
pyfr24 live-flights -R N12345

# Long form
pyfr24 live-flights --registration N12345
```

### Flight tracks

Get flight tracks by ID:
```bash
# Short form
pyfr24 flight-tracks -i 39a84c3c

# Long form
pyfr24 flight-tracks --flight-id 39a84c3c
```

### Export flight data

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

### Airline information

Get airline information by ICAO code:
```bash
# Short form
pyfr24 airline-info -i AAL

# Long form
pyfr24 airline-info --icao AAL
```

### Airport information

Get airport information by code:
```bash
# Short form
pyfr24 airport-info -c JFK

# Long form
pyfr24 airport-info --code JFK
```

### Flight positions

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

### Smart export

The `smart-export` command lets you export all data for a flight by flight number and date, with interactive selection if there are multiple matches.

**Example:**
```bash
pyfr24 smart-export --flight UA2151 --date 2025-04-22
```

- If multiple flights are found, you'll see a summary and be prompted to select.
- The output directory is named automatically for clarity.
- A `toplines.json` file is created with a summary of the exported flight.

**Arguments:**

- `--flight` (required): Flight number or callsign
- `--date` (required): Date (YYYY-MM-DD)
- `--output-dir`: Custom output directory (optional)
- `--background`, `--orientation`: Map/chart options (optional)
- `--auto-select`: For scripting (e.g., `latest`, `earliest`, or index)

**Toplines summary example:**
```json
{
  "flight_number": "UA2151",
  "flight_id": "3a01b036",
  "date": "2025-04-22",
  "origin": "KEWR",
  "destination": "KDEN",
  "departure_time": "2025-04-22T14:48:36Z",
  "arrival_time": "2025-04-22T18:53:23Z",
  "registration": "N28457",
  "aircraft_type": "B739"
}
```

## Getting help

For detailed help on any command:
```bash
pyfr24 --help
pyfr24 <command> --help
```