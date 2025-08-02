# CLI Reference

## Global Options

These options are available for all commands:

```bash
-t, --token TEXT        API token (can also be set via FLIGHTRADAR_API_KEY env var)
-l, --log-level TEXT    Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
-f, --log-file TEXT     Log file path
-o, --output TEXT       Output file path (JSON)
--help                  Show help message and exit
```

## Commands

### flight-summary

Get flight summary information.

```bash
pyfr24 flight-summary [OPTIONS]

Options:
  -F, --flight TEXT          Flight number or call sign [required]
  -f, --from-date TEXT       Start date (YYYY-MM-DD or ISO datetime) [required]
  -t, --to-date TEXT         End date (YYYY-MM-DD or ISO datetime) [required]
  -o, --output TEXT          Output file path (JSON)
```

### live-flights

Get live flights for an aircraft registration.

```bash
pyfr24 live-flights [OPTIONS]

Options:
  -R, --registration TEXT    Aircraft registration [required]
  -b, --bounds TEXT         Geographic bounds (lat1,lon1,lat2,lon2)
  -o, --output TEXT         Output file path (JSON)
```

### flight-tracks

Get flight tracks by ID.

```bash
pyfr24 flight-tracks [OPTIONS]

Options:
  -i, --flight-id TEXT      Flight ID [required]
  -o, --output TEXT        Output file path (JSON)
```

### export-flight

Export flight data to multiple formats.

```bash
pyfr24 export-flight [OPTIONS]

Options:
  -i, --flight-id TEXT       Flight ID [required]
  -o, --output-dir TEXT     Output directory path
  --background TEXT         Background map provider (carto-light, carto-dark, osm, esri-topo, esri-satellite)
  --orientation TEXT        Plot orientation (horizontal, vertical, auto)
  --timezone TEXT           Convert timestamps to specified timezone (e.g., America/New_York)
```

### smart-export

Interactive export by flight number and date with automatic flight selection.

```bash
pyfr24 smart-export [OPTIONS]

Options:
  --flight TEXT             Flight number or callsign [required]
  --date TEXT              Date (YYYY-MM-DD) [required]  
  -o, --output-dir TEXT    Output directory path
  --background TEXT        Background map provider (carto-light, carto-dark, osm, esri-topo, esri-satellite)
  --orientation TEXT       Plot orientation (horizontal, vertical, auto)
  --timezone TEXT          Convert timestamps to specified timezone (e.g., America/New_York)
  --auto-select TEXT       Auto-select flight (latest, earliest, or index number)
```

### airline-info

Get airline information.

```bash
pyfr24 airline-info [OPTIONS]

Options:
  -i, --icao TEXT          Airline ICAO code [required]
  -o, --output TEXT        Output file path (JSON)
```

### airport-info

Get airport information.

```bash
pyfr24 airport-info [OPTIONS]

Options:
  -c, --code TEXT          Airport IATA or ICAO code [required]
  -o, --output TEXT        Output file path (JSON)
```

### flight-positions

Get flight positions within a bounding box.

```bash
pyfr24 flight-positions [OPTIONS]

Options:
  -b, --bounds TEXT        Geographic bounds (lat1,lon1,lat2,lon2) [required]
  -o, --output TEXT        Output file path (JSON)
```

### flight-ids

Get flight IDs for an aircraft registration.

```bash
pyfr24 flight-ids [OPTIONS]

Options:
  -R, --registration TEXT   Aircraft registration [required]
  -f, --from-date TEXT     Start date (YYYY-MM-DD) [required]
  -t, --to-date TEXT       End date (YYYY-MM-DD) [required]
  -o, --output TEXT        Output file path (JSON)
```

## Examples

### Flight Summary
```bash
# Basic usage
pyfr24 flight-summary -F AA123 -f "2023-01-01" -t "2023-01-01"

# Save to file
pyfr24 flight-summary -F AA123 -f "2023-01-01" -t "2023-01-01" -o summary.json
```

### Export Flight Data
```bash
# Basic export
pyfr24 export-flight -i 39a84c3c -o data/flight_39a84c3c

# With timezone conversion and enhanced map background
pyfr24 export-flight -i 39a84c3c \
    --background esri-satellite \
    --timezone "America/New_York" \
    --output-dir data/flight_39a84c3c

# With custom background and orientation
pyfr24 export-flight -i 39a84c3c \
    --background carto-dark \
    --orientation vertical \
    --output-dir data/flight_39a84c3c
```

### Live Flights
```bash
# Get live flights for an aircraft
pyfr24 live-flights -R N12345

# Within geographic bounds
pyfr24 live-flights -R N12345 -b "33.5,-118.8,34.5,-117.5"
```

### Flight IDs
```bash
# Get flight IDs and save to file
pyfr24 flight-ids -R N216MH \
    -f "2025-01-01" \
    -t "2025-04-10" \
    -o flight_ids.json
```

### Smart Export
```bash
# Interactive export by flight number and date
pyfr24 smart-export --flight DL562 --date 2025-08-02

# With timezone conversion to Eastern Time
pyfr24 smart-export --flight DL562 --date 2025-08-02 \
    --timezone "America/New_York"

# With satellite background and auto-select latest flight
pyfr24 smart-export --flight DL562 --date 2025-08-02 \
    --background esri-satellite \
    --auto-select latest \
    --timezone "America/New_York"
``` 