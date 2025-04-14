# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.4] - 2024-03-14

### Added
- Support for different background map providers (CartoDB, OpenStreetMap, Stamen, ESRI)
- Speed and altitude profile charts
- Auto-orientation detection for flight path maps
- Improved error handling for missing data points
- Debug logging for track point processing

### Changed
- Renamed plot.png to map.png for clarity
- Updated flight path color to orange (#f18851)
- Improved chart styling and readability
- Enhanced error messages for API errors

### Fixed
- Handling of None values in track data
- Chart generation for ground operations
- Memory usage in large dataset processing

## [0.1.3] - 2024-03-01

### Added
- Support for flight ID lookup by registration
- Pagination for flight history queries
- Rate limit handling with exponential backoff
- Custom exceptions for better error handling

### Changed
- Improved logging configuration
- Enhanced documentation
- Better validation for input parameters

### Fixed
- Token validation issues
- Date format handling
- Geographic coordinate validation

## [0.1.2] - 2024-02-15

### Added
- Export to multiple formats (CSV, GeoJSON, KML)
- Flight path visualization
- Command-line interface
- Basic logging support

### Changed
- Restructured API client
- Updated dependencies
- Improved error messages

### Fixed
- Authentication handling
- File path issues
- Data format inconsistencies

## [0.1.1] - 2024-02-01

### Added
- Basic API client functionality
- Flight data retrieval
- Simple error handling
- Initial documentation

### Changed
- Package structure
- API endpoint handling
- Response parsing

## [0.1.0] - 2024-01-15

### Added
- Initial release
- Basic project structure
- Core API client
- Simple examples 