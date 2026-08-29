# CLI reference

The Pyfr24 command-line interface provides quick access to all features without writing code.

## Common options

These options are available for all commands:

- `-t, --token`: API token (can also be set via FLIGHTRADAR_API_KEY env var)
- `-l, --log-level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `-f, --log-file`: Log file path
- `-o, --output`: Output file path (JSON)
- `--version`: Print the installed version and exit

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
pyfr24 export-flight -i 39a84c3c --background osm            # OpenStreetMap (default)
pyfr24 export-flight -i 39a84c3c --background esri-light     # Esri light gray canvas
pyfr24 export-flight -i 39a84c3c --background esri-dark      # Esri dark gray canvas
pyfr24 export-flight -i 39a84c3c --background esri-topo      # Esri World TopoMap
pyfr24 export-flight -i 39a84c3c --background esri-satellite # Esri World Imagery
MAPBOX_TOKEN="pk.your_token" pyfr24 export-flight -i 39a84c3c --background mapbox-light

# At different aspect ratios
pyfr24 export-flight -i 39a84c3c --aspect 16:9  # default
pyfr24 export-flight -i 39a84c3c --aspect 3:2
pyfr24 export-flight -i 39a84c3c --aspect 1:1
pyfr24 export-flight -i 39a84c3c --aspect 9:16

# With timezone conversion
pyfr24 export-flight -i 39a84c3c --timezone "America/New_York"      # Eastern time
pyfr24 export-flight -i 39a84c3c --timezone "America/Los_Angeles"   # Pacific time
pyfr24 export-flight -i 39a84c3c --timezone "Europe/London"         # GMT/BST

# In more than one image format
pyfr24 export-flight -i 39a84c3c --format png,svg   # SVG alongside PNG, for Illustrator
pyfr24 export-flight -i 39a84c3c --format svg       # SVG only
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
- `--background`: Map background (osm (default), esri-light, esri-dark, esri-street, esri-topo, esri-satellite, esri-natgeo, opentopo, or mapbox-&lt;style&gt;)
- `--aspect`: Aspect ratio for the map and charts (16:9, 3:2, 4:3, 1:1, 9:16)
- `--orientation`: Legacy orientation (horizontal, vertical, auto); `--aspect` wins
- `--format`: Image formats to write, comma separated (png (default), svg, pdf)
- `--timezone`: Convert timestamps to specified timezone (e.g., America/New_York)
- `--auto-select`: For scripting (e.g., `latest`, `earliest`, or index)

**Toplines summary example:**
```json
{
  "flight_number": "UA2151",
  "flight_id": "3a01b036",
  "date": "2025-04-22",
  "origin": "KEWR",
  "destination": "KDEN",
  "in_progress": false,
  "departure_time": "2025-04-22T14:48:36Z",
  "arrival_time": "2025-04-22T18:53:23Z",
  "departure_time_readable": "April 22, 2025, at 2:48 p.m. UTC",
  "arrival_time_readable": "April 22, 2025, at 6:53 p.m. UTC",
  "last_position_time": "2025-04-22T18:53:23Z",
  "last_position_time_readable": "April 22, 2025, at 6:53 p.m. UTC",
  "registration": "N28457",
  "aircraft_type": "B739"
}
```

**With timezone conversion (--timezone "America/New_York"):**
```json
{
  "flight_number": "UA2151",
  "flight_id": "3a01b036",
  "date": "2025-04-22",
  "origin": "KEWR",
  "destination": "KDEN",
  "in_progress": false,
  "departure_time": "2025-04-22T10:48:36-04:00",
  "arrival_time": "2025-04-22T14:53:23-04:00",
  "departure_time_readable": "April 22, 2025, at 10:48 a.m. ET",
  "arrival_time_readable": "April 22, 2025, at 2:53 p.m. ET",
  "last_position_time": "2025-04-22T14:53:23-04:00",
  "last_position_time_readable": "April 22, 2025, at 2:53 p.m. ET",
  "registration": "N28457",
  "aircraft_type": "B739"
}
```

### Exporting a flight that's still in the air

A flight caught mid-air has no arrival time, so `arrival_time` is null and
`in_progress` is true. The moment the aircraft was last seen is carried as
`last_position_time`, which is a position report rather than an arrival:

```json
{
  "flight_number": "DL691",
  "origin": "KSFO",
  "destination": "KJFK",
  "in_progress": true,
  "departure_time": "2026-08-28T13:08:39-07:00",
  "arrival_time": null,
  "arrival_time_readable": null,
  "last_position_time": "2026-08-28T18:43:52-07:00",
  "last_position_time_readable": "August 28, 2026, at 6:43 p.m. PT"
}
```

The map matches: the end of the route is an arrowhead labeled "In flight"
instead of a dot labeled `KJFK`, and the dek says "still in the air."

## Worked examples

### A flight in the news, by number and date

You have a flight number from a wire story and nothing else. `smart-export` does
the lookup, the disambiguation and the export in one step:

```bash
pyfr24 smart-export --flight NZ6 --date 2026-08-27 \
                    --timezone "America/Los_Angeles" \
                    --background esri-satellite \
                    --format png,svg
```

What lands in `data/NZ6_2026-08-27_NZAA-KLAX_41601381/`:

```
data.csv          644 track points, timestamps in Pacific time
points.geojson    the same points, for QGIS or Mapbox
line.geojson      the path as a LineString
track.kml         the path for Google Earth
map.png           Auckland to Los Angeles over satellite imagery, 16:9
map.svg           the same map with editable type and a vector route
speed.png         ground speed over the flight
speed.svg
altitude.png      altitude over the flight
altitude.svg
toplines.json     flight ID, route, aircraft, departure and arrival times
```

The route crosses the date line, and coverage over the South Pacific is patchy,
so the map shows the fragments that were tracked rather than a line drawn through
the gaps.

For a flight with full coverage instead, the graphics and `toplines.json` from a
San Francisco to New York export are committed in the repository under
[`examples/`](https://github.com/stiles/pyfr24/tree/main/examples), so you can
see real output without running anything. That one holds at 39,000 feet south of
Buffalo, which makes a useful lesson in reading a ground speed chart.

### The same flight at several aspect ratios

Each pass rewrites the same graphics at a different shape. Give each its own
directory or the second export overwrites the first:

```bash
for shape in 16:9 3:2 1:1 9:16; do
  pyfr24 smart-export --flight UA2151 --date 2025-04-22 \
                      --aspect "$shape" \
                      --auto-select latest \
                      --output-dir "data/UA2151_${shape/:/x}"
done
```

That leaves `data/UA2151_16x9`, `data/UA2151_3x2`, `data/UA2151_1x1` and
`data/UA2151_9x16`, each holding a map and two charts framed to that ratio, at
exactly that ratio.

### A Mapbox background with your own token

```bash
export MAPBOX_TOKEN="pk.your_token"
pyfr24 smart-export --flight DL562 --date 2025-08-02 --background mapbox-dark
```

Without `MAPBOX_TOKEN` set, pyfr24 warns and falls back to OpenStreetMap rather
than saving a map with nothing behind the route. `MAPBOX_ACCESS_TOKEN` works too.

### Converting to local time

Timestamps arrive in UTC. Converting them changes the data files, the chart axes
and the `toplines.json` summary together, and the charts name the zone in the
source line so a reader isn't guessing:

```bash
pyfr24 smart-export --flight AA100 --date 2025-11-02 --timezone "Europe/London"
```

### Every flight an aircraft flew

Two steps: find the flights, then export the one you want. `flight-ids` returns
complete records, not just IDs, so the second call is often unnecessary:

```bash
pyfr24 flight-ids -R N216MH -f "2025-01-01" -t "2025-01-14" -o n216mh.json
pyfr24 export-flight -i 39a84c3c -o data/n216mh_39a84c3c --format png,svg
```

The API caps a summary query at 14 days, so a longer span has to be requested in
windows.

## Getting help

For detailed help on any command:
```bash
pyfr24 --help
pyfr24 <command> --help
```