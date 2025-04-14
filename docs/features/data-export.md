# Data Export Features

Pyfr24 can export flight data in multiple formats, making it easy to analyze flight data in your preferred tools.

## Export Formats

### CSV Format
The `data.csv` file contains track points with:
```csv
timestamp,lat,lon,alt,gspeed,vspeed,track,squawk,callsign,source
2023-01-01T12:00:00Z,51.4775,-0.4614,1200,150,0,90,7000,BA123,ADS-B
```

### GeoJSON Format
Two GeoJSON files are created:

1. `points.geojson`: Each track point as a Feature
```json
{
  "type": "FeatureCollection",
  "features": [{
    "type": "Feature",
    "geometry": {
      "type": "Point",
      "coordinates": [-0.4614, 51.4775]
    },
    "properties": {
      "timestamp": "2023-01-01T12:00:00Z",
      "alt": 1200,
      "gspeed": 150
    }
  }]
}
```

2. `line.geojson`: Complete flight path as a LineString
```json
{
  "type": "FeatureCollection",
  "features": [{
    "type": "Feature",
    "geometry": {
      "type": "LineString",
      "coordinates": [
        [-0.4614, 51.4775],
        [-0.4620, 51.4780]
      ]
    }
  }]
}
```

### KML Format
The `track.kml` file contains the flight path suitable for Google Earth:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>flight_id</name>
    <Placemark>
      <LineString>
        <coordinates>
          -0.4614,51.4775,1200
          -0.4620,51.4780,1300
        </coordinates>
      </LineString>
    </Placemark>
  </Document>
</kml>
```

### Visualizations
Three visualization files are created:

- `map.png`: Flight path map visualization
- `speed.png`: Ground speed over time chart
- `altitude.png`: Altitude profile chart

## Using the Export Feature

### Basic Export
```python
output_dir = api.export_flight_data("39bebe6e")
```

### Customized Export
```python
output_dir = api.export_flight_data(
    "39bebe6e",
    output_dir="custom/path",
    background='osm',
    orientation='auto'
)
```

### CLI Export
```bash
# Basic export
pyfr24 export-flight -i 39a84c3c -o data/flight_39a84c3c

# With custom background
pyfr24 export-flight -i 39a84c3c --background osm --output-dir data/flight_39a84c3c
```

## Output Directory Structure

The export creates a directory with all files:
```
data/flight_id/
├── data.csv
├── points.geojson
├── line.geojson
├── track.kml
├── map.png
├── speed.png
└── altitude.png
```

## Data Processing

The export process includes:

1. Fetching raw flight tracks
2. Sorting by timestamp
3. Filtering invalid data points
4. Converting coordinates
5. Generating visualizations
6. Saving in multiple formats

## Error Handling

The export handles various edge cases:

- Missing data points
- Invalid coordinates
- Missing timestamps
- Ground operations (zero altitude/speed)
- Network errors
- File system errors 