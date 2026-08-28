# Enhanced visualizations

Pyfr24 generates publication-ready visualizations with professional styling and customization options.

## Graphic structure

Maps and charts share one layout: a bold headline, a lighter dek carrying the
date and tracked duration, the graphic itself, then a source line. All of it sits
inside the requested aspect ratio, so the file you get is ready to place.

```
Altitude of AA3202 from KMIA to KLAX
Nov. 2, 2025 · 7 hr 16 min tracked

  [ chart ]

Source: Flightradar24. Times in Pacific time.
```

Headlines, deks and source lines are generated from the flight data, and each
can be overridden:

```python
api.enhanced_plot_flight(
    tracks, "39bebe6e",
    fig_filename="map.png",
    headline="The flight turned back over the Atlantic",
    dek="Nov. 2, 2025",
    source="Source: Flightradar24; basemap by Esri",
)
```

### Chart styling

- **Typography**: CNN Sans Display where installed, falling back to Roboto, Inter and the system sans-serif
- **Dates**: AP style, so "Nov. 2, 2025" and "March 2, 2025"
- **Time axis**: interval chosen from flight duration to land near five labels, so they never collide
- **Units on the top tick only**: `35,000 feet` at the top, bare numbers below
- **Honest baseline**: altitude and speed both start at a real zero
- **Timezone**: named in the source line rather than floating over the plot

## Map backgrounds

### Available backgrounds

None of these need an API key:

| Background | Description | Best for |
|------------|-------------|----------|
| `osm` | OpenStreetMap standard (default) | General purpose; labels cities and states at national zooms |
| `esri-light` | Esri light gray canvas | A quieter frame where the route carries the map |
| `esri-dark` | Esri dark gray canvas | High-contrast presentations |
| `esri-street` | Esri World Street Map | Street-level context |
| `esri-topo` | Esri World Topographic | Terrain and topographic features |
| `esri-satellite` | Esri World Imagery | Satellite photography |
| `esri-natgeo` | Esri National Geographic | Reference-style physical geography |
| `opentopo` | OpenTopoMap | Hillshaded terrain |

Mapbox styles are available with your own token:

```bash
export MAPBOX_TOKEN="pk.your_token"
pyfr24 smart-export --flight DL562 --date 2025-08-02 --background mapbox-light
```

Mapbox style IDs carry a version suffix, so the plain name you'd expect,
`light`, is really `light-v11`. Pyfr24 accepts the short name and fills in the
current version:

| Short name | Style ID |
|------------|----------|
| `mapbox-light` | `mapbox/light-v11` |
| `mapbox-dark` | `mapbox/dark-v11` |
| `mapbox-streets` | `mapbox/streets-v12` |
| `mapbox-outdoors` | `mapbox/outdoors-v12` |
| `mapbox-satellite` | `mapbox/satellite-v9` |
| `mapbox-satellite-streets` | `mapbox/satellite-streets-v12` |
| `mapbox-navigation-day` | `mapbox/navigation-day-v1` |
| `mapbox-navigation-night` | `mapbox/navigation-night-v1` |

A versioned ID passes through untouched, so `mapbox-light-v11` still works and
lets you pin a version Mapbox has since superseded. To use a style of your own,
give the full `owner/styleid`, as in `mapbox-yourname/cl9xk2p00000`.

### When a basemap fails

Tile servers only fail when the tiles are requested, so a mistyped style, a
revoked token or an outage surfaces mid-render. Rather than saving a map with
nothing behind the route, pyfr24 logs the error, retries with the default
OpenStreetMap layer and rewrites the source line to credit the basemap you
actually got.

### CARTO backgrounds were removed

CARTO withdrew anonymous access to its basemaps, and requests without a key now
return tiles watermarked "API key required." Passing `carto-light` or
`carto-dark` logs a warning and falls back to the nearest Esri equivalent.

### Usage examples

```bash
# Default light background
pyfr24 smart-export --flight DL562 --date 2025-08-02

# Satellite imagery for geographic context
pyfr24 smart-export --flight DL562 --date 2025-08-02 --background esri-satellite

# Dark canvas for presentations
pyfr24 smart-export --flight DL562 --date 2025-08-02 --background esri-dark
```

## Aspect ratios

Every graphic in an export is rendered at the same ratio, and the saved image
matches it exactly. The map extent expands to fill the frame, so a north-south
route and an east-west route produce images of identical size.

| Aspect | Ratio |
|--------|-------|
| `16:9` | Default |
| `3:2` | Standard photo ratio |
| `4:3` | Squarer frame |
| `1:1` | Square, for social |
| `9:16` | Vertical, for mobile and social |

```bash
pyfr24 smart-export --flight DL562 --date 2025-08-02 --aspect 3:2
```

The older `--orientation horizontal|vertical|auto` flag still works and maps to
`16:9` and `9:16`. `--aspect` takes precedence when both are given.

## Timezone conversion

Convert all timestamps from UTC to local time zones for easier analysis.

### Supported timezones

Any valid timezone identifier from the IANA timezone database:

- **US timezones**: `America/New_York`, `America/Chicago`, `America/Denver`, `America/Los_Angeles`
- **European timezones**: `Europe/London`, `Europe/Paris`, `Europe/Berlin`
- **Other regions**: `Asia/Tokyo`, `Australia/Sydney`, etc.

### Features

- **Automatic DST handling**: Correctly handles Daylight Saving Time transitions
- **Chart timezone indicators**: Names the zone in the source line (e.g., "Times in Eastern time")
- **Readable timestamps**: Formats times as "August 2, 2025, at 10:38 a.m. ET"
- **ISO timestamp conversion**: All data files use converted timestamps

### Usage examples

```bash
# Convert to Eastern Time
pyfr24 smart-export --flight DL562 --date 2025-08-02 --timezone "America/New_York"

# Convert to Pacific Time  
pyfr24 smart-export --flight DL562 --date 2025-08-02 --timezone "America/Los_Angeles"

# Convert to London time
pyfr24 smart-export --flight DL562 --date 2025-08-02 --timezone "Europe/London"
```

## Output files

Each export creates publication-ready files:

### Visual outputs

- **`map.png`**: Flight path visualization with enhanced backgrounds
- **`speed.png`**: Professional speed profile chart
- **`altitude.png`**: Professional altitude profile chart

### Data outputs

- **`toplines.json`**: Summary with readable timestamps
- **`data.csv`**: Complete track data with timezone conversion
- **`points.geojson`**: Track points for GIS applications
- **`line.geojson`**: Flight path as LineString
- **`track.kml`**: Google Earth compatible format

## Complete example

```bash
# Publication-ready export
pyfr24 smart-export \
    --flight DL562 \
    --date 2025-08-02 \
    --timezone "America/New_York" \
    --background esri-satellite \
    --aspect 3:2 \
    --auto-select latest
```

This creates:
- A map with a satellite background, framed to exactly 3:2
- Speed and altitude charts at the same ratio, labeled in Eastern time
- All data converted to Eastern time
- Readable timestamps in the toplines summary