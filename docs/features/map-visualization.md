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
- A light gray border, matching the chart gridlines, so the map reads as a panel
- Type in CNN Sans Display where installed, falling back to Roboto, Inter, then the system sans-serif
- Basemap credit carried in the source line, so the tile provider is attributed
- Equal aspect in Web Mercator, so distances aren't distorted
- Saved at 200 DPI by default, adjustable with `dpi`

## Origin and destination

Both ends of the track are marked with a dot and labeled with the airport code
passed as `origin` and `destination`. These sit at the first and last fix, which
is near the runway rather than the terminal, and a code the export doesn't know
leaves a bare dot. Pass `endpoints=False` to `plot_flight_map` to suppress them.

Labels sit under their dot rather than beside it: most routes run east to west,
and a label set alongside lands on the line. Near the foot of the panel a label
moves above its dot, and near the left or right edge it hugs that edge instead of
centering, so it stays inside the frame.

## Ends that aren't airports

An airport code is a claim about where the aircraft got to, and a track only
supports it when the track reached the ground. Two common cases don't: a flight
still in the air when it was exported, and one whose receivers gave out before
it landed. Above 5,000 feet, then, the end of the line is drawn as an arrowhead
turned the way the aircraft was last heading, and labeled for what it is:

- **In flight**, when the flight hadn't landed. `smart-export` reads this from
  the summary record; pass `in_progress=True` to `plot_flight_map` to set it
  yourself. The dek also picks up "still in the air".
- **Last contact**, when the track ends in the air but the flight is over. This
  is the default for a track whose status isn't known.
- **First contact**, for a track picked up mid-air, at the start of the line.

Most exports are unaffected — a flight tracked to the gate reports zero feet at
its last fix and keeps its airport code.

## Gaps in coverage

Receivers lose aircraft, especially over open ocean, and joining across the hole
draws a path nothing reported. Pyfr24 lifts the line instead, on the map and on
both charts, so an Auckland-to-Los Angeles flight reads as the fragments that
were actually tracked.

What counts as a gap scales with the flight, since ping cadence varies by region:
the threshold is twelve times the track's own median interval, with a floor of
five minutes. A break also has to cover ground, so an aircraft sitting at a gate
between pings stays one line rather than fragmenting into dots. Pass
`gap_seconds` to set the interval yourself.

## Flights across the date line

A Tokyo-to-Los Angeles route runs east through 180 degrees of longitude and out
the other side, where a naive reading of the coordinates sends it back across
Asia, Europe and the Atlantic. Pyfr24 unwraps longitude so the path stays
continuous, which puts the map's extent past the edge of the single world tile
servers publish; the basemap is then fetched a world at a time and composited, so
a Pacific crossing is drawn over the Pacific.

## Additional visualizations

Each export also writes a ground speed chart and an altitude chart, styled to
match the map and rendered at the same aspect ratio. Both label their units on
the top axis tick and name the timezone in the source line.

## Output files

- `map.png`: Flight path over the basemap
- `speed.png`: Ground speed profile
- `altitude.png`: Altitude profile

Pass `formats` to write more than PNG. Each graphic is written once per format,
so `formats=('png', 'svg')` leaves `map.svg` beside `map.png`.

```python
api.export_flight_data("39bebe6e", formats=('png', 'svg'))
```

SVG and PDF keep the route, the border and the chrome as vectors, and leave type
as live text rather than outlines, so an editor can restyle or retype a label in
Illustrator. The basemap is raster wherever it comes from, so it travels as an
embedded image.
