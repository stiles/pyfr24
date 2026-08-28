# Changelog

## [Unreleased]

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