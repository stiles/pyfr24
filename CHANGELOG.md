# Changelog

## [Unreleased]

### Added
- `--format` flag and `formats` argument, taking a comma-separated list of `png` (default), `svg` and `pdf`. Each graphic is written once per format, so `--format png,svg` leaves `map.svg` beside `map.png`. SVG keeps the route, the chrome and the type as vectors for editing in Illustrator, with the type left as live text rather than outlines; the basemap rides along as an embedded raster, since that's what tiles are.
- Origin and destination are marked on the map with a dot and their airport code. Labels sit under the dot, since most routes run east to west and a label set alongside lands on the line, and they move above the dot or hug the panel edge where they'd otherwise overflow. These are the first and last fix, which is close to the runway rather than the terminal.
- `in_progress` argument to `plot_flight_map`, `enhanced_plot_flight` and `export_flight_data`, set from the summary record by `smart-export`, which distinguishes an aircraft still flying from one whose track merely ran out.
- `toplines.json` carries `in_progress`, plus `last_position_time` and `last_position_time_readable`.
- A real export is committed under `examples/`: the map, both charts and `toplines.json` from a San Francisco to New York flight that held at 39,000 feet south of Buffalo, so the output can be seen without installing or holding an API token. The data files and SVGs are left out, since `points.geojson` and `map.svg` alone would add 1.3 MB. `examples/README.md` works through why the dip under that hold is mostly a lost tailwind rather than braking.
- The map is bordered in the same light gray as the chart gridlines, so it reads as a panel instead of bleeding into the page, and a map and a chart of the same flight sit together.

### Changed
- Deks spell out the tracked duration: "4 hours, 2 minutes tracked" rather than "4 hr 2 min tracked", with singulars handled so an hour and a minute don't come out plural.
- Dropped `geopandas` and `shapely` from the dependencies. Both were there for a single coordinate transform, which the antimeridian fix had to replace anyway, and one of them drags in GDAL. `numpy` is now declared instead: `viz` imports it directly and it had been arriving only as a transitive dependency of matplotlib and pandas.
- The version is defined once, in `pyfr24/__init__.py`, and `setup.py` parses it from there rather than carrying a second copy. Two hand-maintained literals is what let 0.2.0 ship reporting itself as 1.0.0. `publish.sh` now bumps a single file, and a test asserts the packaged version matches `pyfr24.__version__`.
- `python_requires` is now `>=3.9`. The package imports `zoneinfo` for timezone conversion, which is standard library only from 3.9, so the advertised 3.8 support never worked. The CI matrix drops 3.8 and adds 3.12 and 3.13.
- Publishing to PyPI happens once, in the release workflow. `publish.sh` uploaded with twine and then created a GitHub release that triggered a second upload, so every Publish run failed with "400 File already exists" after the package had already gone out.
- Tests that call the live API are marked `integration` and deselected in CI, so the suite no longer depends on a given flight having operated on the day it runs.

### Fixed
- Flights that cross the antimeridian are drawn across the Pacific rather than the long way around the world (#2). Longitude is unwrapped so the path stays continuous past 180 degrees, and the extent that produces is wider than the one world tile servers publish, so the basemap is now fetched a world at a time and composited. Contextily can't do this itself: it hands the bounds to mercantile, which clamps them, and reports success after rendering nothing past the world's edge. The projection is also worked out directly instead of through a CRS transform, which folds longitude back inside 180 and undoes the unwrapping.
- Maps and charts break where ADS-B coverage stops instead of ruling a straight line through the hole (#3). An Auckland-to-Los Angeles flight loses coverage over the South Pacific for hours, which the altitude chart drew as a slow, steady climb that never happened. The threshold scales with each flight's own median ping interval rather than being fixed, since cadence varies by region, and a break also has to cover ground, so an aircraft sitting at a gate between pings stays one line rather than fragmenting into dots.
- A missing altitude or speed reading is plotted as missing rather than as zero. Substituting zero drew a cliff to sea level in the middle of a cruise.
- A track that stops in the air is no longer labeled with the destination airport. A flight caught mid-air ends wherever the aircraft happened to be — DL691 was drawn with a dot and "KJFK" at 39,000 feet over Pennsylvania, two hundred miles short — and receivers routinely lose an aircraft before it lands. Above 5,000 feet the end of the line becomes an arrowhead turned the way the aircraft was heading, labeled "In flight" when the API says the flight hadn't landed and "Last contact" when the track simply ran out; the dek says "still in the air" for a flight in progress. Of 181 local exports, 42 ended at cruise altitude, so roughly one in four carried the wrong label.
- A landing time now settles whether a flight is still airborne, ahead of the `flight_ended` flag. That flag marks a record as closed out rather than a flight as over, and Flightradar24 leaves it false for a while after touchdown: DL691 on Aug. 28, 2026 read `flight_ended: false` next to a landing time of 02:10 UTC, which would have had a parked aircraft reported as flying and its arrival time thrown away.
- `toplines.json` no longer reports an arrival time for a flight that hadn't landed. `arrival_time` fell back to the moment the aircraft was last seen, which for a flight in progress is a point over open country at cruise. It's now null, and the last-seen time is carried as `last_position_time`.
- A single implausible reading is dropped rather than drawn. NZ6 reported 30 knots at 35,000 feet between two readings near 500, which put a cliff to the floor of the speed chart; recovering from it would have taken 0.8 g. A reading goes only when the readings either side agree with each other and it departs from both by more than 200 knots or 5,000 feet, so a real and violent change, which plays out over several pings, is kept. Thirteen percent of local exports had at least one.
- The speed chart notes when much of a track was fixed by multilateration, whose speeds are inferred from signal timing at several receivers and wobble by hundreds of knots. QR739 had 847 such fixes out of 2,229, and no point-by-point filter can rescue that; the graphic now says the speeds are estimated instead.
- `tests/` was listed in `.gitignore`, so only the handful of files committed before that line was added were ever in the repository or run by CI. New tests were silently untracked.

## [0.2.1] - 2026-08-28

### Changed
- `osm` is now the default basemap, replacing `esri-light`. OpenStreetMap labels cities and states at the zooms a cross-country route sits at, where the Esri gray canvas drops them, so a map reads without extra annotation. `esri-light` remains available for a quieter frame.
- OpenStreetMap is credited as "OpenStreetMap contributors" in the source line, the attribution its license asks for.

### Fixed
- Mapbox backgrounds returned a 404 and rendered a bare route with no basemap. Mapbox style IDs carry a version suffix, so `--background mapbox-light` was requesting the style `mapbox/light`, which doesn't exist. Short names now resolve to the current version (`light` to `light-v11`, `streets` to `streets-v12` and so on); versioned IDs and custom `owner/styleid` styles still pass through untouched.
- A basemap that fails at tile-request time now falls back to the default rather than saving a map with nothing behind the route, and the source line is rewritten to credit the basemap actually drawn.
- Corrected `__version__`, which reported 1.0.0 in the 0.2.0 release.

## [0.2.0] - 2026-08-28

### Added
- `--aspect` flag and `aspect` argument for `16:9` (default), `3:2`, `4:3`, `1:1` and `9:16`. The saved file matches the ratio exactly, and the map extent expands to fill the frame, so output size no longer varies with the direction of the route.
- Maps and charts are laid out as finished graphics: bold headline, dek carrying an AP-style date and tracked duration, then a source line crediting Flightradar24 and the basemap. All three can be overridden with `headline`, `dek` and `source`.
- Basemap options `esri-light` (new default), `esri-dark`, `esri-street`, `esri-natgeo` and `opentopo`, none of which need an API key.
- Mapbox backgrounds via `--background mapbox-<style>`, reading `MAPBOX_TOKEN` or `MAPBOX_ACCESS_TOKEN`.
- Type follows the house style guide: CNN Sans Display where installed, falling back to Roboto, Inter and the system sans-serif.

### Removed
- The `carto-light` and `carto-dark` backgrounds. CARTO withdrew anonymous access and now serves tiles watermarked "API key required." Both keys warn and fall back to the nearest Esri layer rather than failing.

### Changed
- Moved map and chart rendering out of `client.py` into a new `pyfr24/viz.py` module. The speed and altitude charts now share one `plot_series_chart` function instead of duplicating ~150 lines each. `FR24API` methods keep their existing signatures.

### Fixed
- OpenStreetMap backgrounds rendered an "Access blocked" placeholder. Contextily identifies itself with a random hex string, which violates the OSM tile usage policy, so the tile server returned the notice image with a 200 status. Pyfr24 now sends an identifying user agent.
- Maps ignored the requested orientation. `set_aspect('equal')` combined with a tight bounding box cropped the canvas to the data, and `reset_extent=False` let contextily widen the axes to the tile boundary, so a Miami-to-Los Angeles route came out 2.88:1 and a Bellingham-to-Los Angeles route 0.46:1.
- Timezone label on speed and altitude charts rendered as "Time ()" for UTC data. The label now uses the requested IANA zone, falling back to the timestamp's abbreviation or UTC offset, and sits below the axis instead of overlapping the plotted line.
- Overlapping x-axis time labels on flights of roughly 4 to 8 hours. Tick spacing is now chosen from the flight duration to target about five labels, rather than switching between fixed 30-minute and hourly steps at an 8-hour cutoff.
- Map figures were never closed, leaking them across batch exports.

## [0.1.10] - 2025-10-12

### Added
- `--version` flag to CLI to display current package version

### Fixed
- **Critical bug fix**: `flight-ids` command now works correctly
  - Was calling non-existent `/api/flight-ids` endpoint (returned 404)
  - Now uses `/api/flight-summary/light` with `registrations` parameter
  - Successfully retrieves all flight instances for a given aircraft registration and date range
- Fixed undefined `labels` argument in `smart-export` interactive selection that could cause AttributeError
- Improved error handling for flight lookup by registration

## [0.1.9] - 2025-08-02

## [0.1.8] - 2025-08-02

### Added
- `--timezone` flag to `export-flight` and `smart-export` commands to convert all output timestamps to a specified time zone.
- `departure_time_readable` and `arrival_time_readable` fields in `toplines.json` for easier-to-read timestamps.
- Enhanced map backgrounds with new options: `carto-light`, `carto-dark`, `osm`, `esri-topo`, and `esri-satellite`.
- Improved map titles showing flight number and route (e.g., "Flight: DL562  Departure: KSEA  Destination: KATL") instead of just flight ID.
- Professional chart design for speed and altitude outputs:
  - Clean headline/subhead structure with proper typography and spacing
  - Smart time intervals (30-minute for short flights, 1-hour for long flights)
  - Human-readable time labels (11:30 AM instead of 11:30:00)
  - Comma separators for altitude values (35,000 instead of 35000)
  - Human-readable dates in chart titles (August 2, 2025 instead of August 02, 2025)
  - Units displayed in chart headlines (knots/feet) for clarity
  - Timezone indicators on charts when timezone conversion is used
  - Removed unnecessary reference lines and legends for cleaner appearance
  - Publication-ready layout with professional spacing and alignment

## [0.1.7] - 2025-04-26

### Added
- `smart-export` CLI command for interactive export by flight number and date.
- Automatic output directory naming for exports.
- `toplines.json` summary file in each export directory.
- Progress messages for summary, track fetching, and export steps.

### Fixed
- Correct date range handling for summary queries.

### Improved
- User feedback and workflow for CLI exports.

## [0.1.6] - 2025-04-18

### Added
- Enhanced documentation with flight identifier examples
  - Added visual guide for flight numbers, callsigns, and FR24 IDs
  - Updated API documentation with working examples
  - Added image support with glightbox plugin
  - Improved CLI documentation with real-world examples

### Changed
- Improved logging configuration
  - Removed duplicate logging messages
  - Simplified console output format
  - Changed default log level to WARNING
  - Added detailed logging format for file output
- Updated Jinja2 dependency to >=3.1.6 for security fixes

### Fixed
- Fixed font warning message in visualization code
- Improved error handling in client initialization

## [0.1.4] - 2025-04-14

### Added
- Map visualization enhancements:
  - Customizable orientation options (16:9 horizontal, 9:16 vertical, or auto-detect)
  - Improved flight path styling with clean orange line (#f18851)
  - Adjusted figure dimensions for better display
- Added Read the Docs documentation setup
  - Configuration files for automatic builds
  - Initial documentation structure
  - API reference framework

### Changed
- Updated map output to use 16:9 aspect ratio by default
- Improved CLI help text for visualization options
- Enhanced README with comprehensive examples for map customization 