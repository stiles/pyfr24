# Map visualization

Pyfr24 draws the flight path over a tiled basemap and frames it to a fixed
aspect ratio, so exports drop straight into a graphic.

## Background maps

The default is `osm`, which labels cities and states at the zooms a
cross-country route sits at, so the map reads without extra annotation. Use
`esri-light` for a quieter canvas that lets the route carry the map. See
[enhanced visualizations](enhanced-visualizations.md) for the full list.

```python
api.export_flight_data("39bebe6e", background='osm')             # default
api.export_flight_data("39bebe6e", background='esri-light')      # Esri light gray canvas
api.export_flight_data("39bebe6e", background='esri-satellite')  # Esri World Imagery
api.export_flight_data("39bebe6e", background='mapbox-dark')     # needs MAPBOX_TOKEN
```

None of the Esri, OpenStreetMap or OpenTopoMap options need a key. The CARTO
backgrounds were removed once CARTO began requiring one; passing `carto-light`
or `carto-dark` warns and falls back to Esri.

## Aspect ratio

Pass `aspect` to fix the shape of the finished graphic: `16:9` (default), `3:2`,
`4:3`, `1:1` or `9:16`. The map extent grows to fill the frame, so the output
size doesn't change with the direction of the route.

```python
api.export_flight_data("39bebe6e", aspect='3:2')
api.export_flight_data("39bebe6e", aspect='9:16')
```

The older `orientation` argument still works: `horizontal` is `16:9`, `vertical`
is `9:16`, and `auto` picks between them from the shape of the track. `aspect`
wins when both are passed.

## Visual style

- Orange route line (`#F18851`) over a muted basemap
- Headline, dek and source line laid out around the map inside the requested ratio
- Type in CNN Sans Display where installed, falling back to Roboto, Inter, then the system sans-serif
- Basemap credit carried in the source line, so the tile provider is attributed
- Equal aspect in Web Mercator, so distances aren't distorted
- Saved at 200 DPI by default, adjustable with `dpi`

## Additional visualizations

Each export also writes a ground speed chart and an altitude chart, styled to
match the map and rendered at the same aspect ratio. Both label their units on
the top axis tick and name the timezone in the source line.

## Output files

- `map.png`: Flight path over the basemap
- `speed.png`: Ground speed profile
- `altitude.png`: Altitude profile
