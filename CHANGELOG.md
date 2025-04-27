# Changelog

## [0.1.7] - 2024-06-26

### Added
- `smart-export` CLI command for interactive export by flight number and date.
- Automatic output directory naming for exports.
- `toplines.json` summary file in each export directory.
- Progress messages for summary, track fetching, and export steps.

### Fixed
- Correct date range handling for summary queries.

### Improved
- User feedback and workflow for CLI exports.

## [0.1.6] - 2024-04-18

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

## [0.1.4] - 2024-04-14

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