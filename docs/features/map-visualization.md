# Map Visualization Features

Pyfr24 provides powerful flight path visualization capabilities with customizable options.

## Background Map Options

Choose from multiple background map providers:

- **CartoDB Positron** (default): Clean, light gray basemap
- **OpenStreetMap**: Detailed street and terrain data
- **Stamen Terrain**: Beautiful terrain visualization
- **ESRI World TopoMap**: Topographic mapping

Example usage:
```python
# Using different background maps
api.export_flight_data("39bebe6e", background='osm')    # OpenStreetMap
api.export_flight_data("39bebe6e", background='stamen') # Stamen Terrain
api.export_flight_data("39bebe6e", background='esri')   # ESRI World TopoMap
# Default is CartoDB Positron (light gray)
```

## Map Orientation

Three orientation options to best display your flight path:

- **Horizontal** (16:9): Default, ideal for east-west flights
- **Vertical** (9:16): Better for north-south flights
- **Auto**: Automatically selects based on flight path direction

Example usage:
```python
# Using different orientations
api.export_flight_data("39bebe6e", orientation='horizontal') # 16:9
api.export_flight_data("39bebe6e", orientation='vertical')   # 9:16
api.export_flight_data("39bebe6e", orientation='auto')      # Auto-detect
```

## Visual Style

The flight path visualization includes:

- Orange flight path line (#f18851) for high visibility
- Clean, modern styling
- High-quality output (300 DPI)
- Automatic zoom level adjustment
- Padding around the flight path for context
- Equal aspect ratio for accurate distance representation

## Additional Visualizations

Along with the map, the export includes:

### Speed Chart
- Ground speed over time
- Clear time axis with formatted timestamps
- Reference lines for common speed thresholds
- Orange line color matching the map visualization

### Altitude Chart
- Altitude profile over time
- Reference lines at key altitudes (ground, 10,000ft, 30,000ft)
- Matching style with speed chart
- Clear altitude scale in feet

## Combining Options

You can combine different options for the perfect visualization:

```python
output_dir = api.export_flight_data(
    "39bebe6e",
    background='osm',       # Use OpenStreetMap background
    orientation='vertical'  # 9:16 aspect ratio for north-south flights
)
```

## Output Files

The visualization export creates:

- `map.png`: Flight path visualization
- `speed.png`: Speed profile chart
- `altitude.png`: Altitude profile chart

All images are generated at 300 DPI for high-quality output. 