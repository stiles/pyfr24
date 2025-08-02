# Pyfr24 development plan

This document lists planned features for the `pyfr24` tool.

## Feature roadmap

### In progress

- [ ] **Better visual outputs**
    - [ ] Export visuals to SVG format for editing in Illustrator.

### Planned

- [ ] **Mapbox support**
    - [ ] Add a command to upload flight paths to Mapbox.
    - [ ] Read Mapbox API keys from the environment.

- [ ] **Easier flight lookup**
    - [ ] Add a `lookup` command to find all flight IDs from a flight number and date.

- [ ] **Flight path analysis**
    - [ ] Calculate flight stats like distance, duration, and max altitude.
    - [ ] Flag unusual events like rapid altitude changes.

- [ ] **API caching**
    - [ ] Cache API requests to speed up the tool and reduce errors.

- [ ] **Human names in viz and topline outputs**
    - [ ] Figure out lookups for airlines "DL256" should be "Delta Airlines flight 256"
    - [ ] Figure out lookups for airports "KATL" should be "Hartsfield–Jackson Atlanta International Airport"

### Project maintenance

- [ ] Keep the version number and `CHANGELOG.md` updated.
- [ ] Keep the ReadTheDocs website in sync with new features.
- [ ] Update `README.md` to document new map background options and timezone conversion features.
- [ ] Update ReadTheDocs CLI and API documentation with new flags and parameters.

## Completed

- [x] **Time zone conversion**
    - Convert flight times from UTC to a local time zone.
    - Improve the `toplines.json` output to include human-readable date strings.

- [x] **Enhanced map backgrounds**
    - Add multiple map background options: `carto-light`, `carto-dark`, `osm`, `esri-topo`, and `esri-satellite`.
    - Improve map titles to show flight number and route instead of just flight ID.

- [x] **Professional chart design**
    - Clean headline/subhead structure with proper typography and spacing.
    - Smart time intervals (30-minute for short flights, 1-hour for long flights).
    - Human-readable time labels (11:30 AM instead of 11:30:00).
    - Comma separators for altitude values (35,000 instead of 35000).
    - Human-readable dates in chart titles (August 2, 2025 instead of August 02, 2025).
    - Units displayed in chart headlines (knots/feet) for clarity.
    - Timezone indicators on charts when timezone conversion is used.
    - Removed unnecessary reference lines and legends for cleaner appearance.
    - Publication-ready layout with professional spacing and alignment. 
