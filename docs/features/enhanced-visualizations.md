# Enhanced visualizations

Pyfr24 generates publication-ready visualizations with professional styling and customization options.

## Professional chart design

### Chart styling features

- **Clean typography**: Headlines and subheads with proper spacing and font hierarchy
- **Smart time formatting**: Human-readable time labels (11:30 AM instead of 11:30:00)
- **Intelligent intervals**: 30-minute ticks for short flights, 1-hour for long flights
- **Number formatting**: Comma separators for altitude values (35,000 instead of 35000)
- **Date formatting**: Human-readable dates (August 2, 2025 instead of August 02, 2025)
- **Unit display**: Clear indication of units (knots/feet) in chart headlines
- **Timezone awareness**: Shows timezone when conversion is applied
- **Minimal design**: Removed unnecessary reference lines and legends

### Chart types

**Speed charts** display ground speed profiles over time with:
- Orange line plotting speed in knots
- Professional headline structure showing flight details
- Smart time intervals based on flight duration
- Clear indication of timezone when converted

**Altitude charts** show altitude profiles with:
- Clean altitude progression in feet
- Comma-separated altitude values for readability
- Same professional styling as speed charts
- Clear indication of cruise altitude phases

## Map backgrounds

Choose from multiple high-quality map providers:

### Available backgrounds

| Background | Description | Best for |
|------------|-------------|----------|
| `carto-light` | Clean CartoDB light theme (default) | General purpose, high readability |
| `carto-dark` | CartoDB dark theme | Modern, high-contrast presentations |
| `osm` | OpenStreetMap standard | Detailed street-level information |
| `esri-topo` | ESRI World Topographic | Terrain and topographic features |
| `esri-satellite` | ESRI World Imagery | Satellite photography |

### Usage examples

```bash
# Default light background
pyfr24 smart-export --flight DL562 --date 2025-08-02

# Satellite imagery for geographic context
pyfr24 smart-export --flight DL562 --date 2025-08-02 --background esri-satellite

# Dark theme for presentations
pyfr24 smart-export --flight DL562 --date 2025-08-02 --background carto-dark
```

## Timezone conversion

Convert all timestamps from UTC to local time zones for easier analysis.

### Supported timezones

Any valid timezone identifier from the IANA timezone database:

- **US timezones**: `America/New_York`, `America/Chicago`, `America/Denver`, `America/Los_Angeles`
- **European timezones**: `Europe/London`, `Europe/Paris`, `Europe/Berlin`
- **Other regions**: `Asia/Tokyo`, `Australia/Sydney`, etc.

### Features

- **Automatic DST handling**: Correctly handles Daylight Saving Time transitions
- **Chart timezone indicators**: Shows timezone abbreviation on charts (e.g., "Eastern Time")
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
# Professional export with all enhancements
pyfr24 smart-export \
    --flight DL562 \
    --date 2025-08-02 \
    --timezone "America/New_York" \
    --background esri-satellite \
    --auto-select latest
```

This creates:
- Map with satellite background showing flight path
- Speed/altitude charts in Eastern Time with professional styling
- All data converted to Eastern Time
- Readable timestamps in toplines summary