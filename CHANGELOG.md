# Changelog

## [Unreleased]

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