# Examples

## A real export

`DL691_2026-08-28_KSFO-KJFK_4166af99/` holds the graphics from one actual run,
so you can see what pyfr24 produces without installing it first. The command
that made them:

```bash
pyfr24 smart-export --flight DL691 --date 2026-08-28 \
                    --timezone "America/Los_Angeles" \
                    --background osm \
                    --format png,svg
```

Delta 691, San Francisco to New York on a Boeing 767, tracked gate to gate over
1,706 ADS-B fixes.

| File | What it shows |
|------|---------------|
| `map.png` | The route over OpenStreetMap, framed to 16:9 |
| `speed.png` | Ground speed, labeled in Pacific time |
| `altitude.png` | Altitude, with the step climbs across the country |
| `toplines.json` | Flight ID, route, aircraft, departure and arrival times |

A run writes more than this. `data.csv`, `points.geojson`, `line.geojson` and
`track.kml` sit alongside the graphics, and `--format png,svg` adds an SVG of
each. Those are left out here to keep the repository light: the three PNGs come
to 700 KB on their own, and `points.geojson` and `map.svg` add 1.3 MB between
them. Run the command above for the full set.

### The hold south of Buffalo

This flight was chosen because something happened. Between 6:08 and 6:17 p.m.
Pacific the aircraft flew a complete circle at 39,000 feet over the New
York-Pennsylvania line, about 80 miles south of Buffalo, then carried on to JFK.
The map shows the loop; the speed chart shows a sharp dip underneath it.

The dip is worth reading carefully, and it's a good illustration of why the
chart is labeled *ground* speed. At its fastest in the turn the aircraft was
making 517 knots on a heading of 051, and at its slowest 372 knots on 236 —
headings 175 degrees apart. Constant airspeed in a wind produces exactly that:
the numbers imply about 444 knots through the air and a 72-knot tailwind the
aircraft gave up when it turned back into it. So the 145-knot drop is mostly the
wind, not braking. An aircraft in a hold does slow down, but nowhere near what
this chart appears to show.

Nothing in the flight was lost to missing coverage, which is the
straightforward case. For a route that loses its receivers over open ocean, a
flight still in the air when you export it, or one that crosses the date line,
see the
[map visualization docs](https://pyfr24.readthedocs.io/en/latest/features/map-visualization/).

## Scripts

- `check_lax_arrivals.py` finds which LAX arrivals passed within four nautical
  miles of Lennox Middle School, the shape of an aircraft-noise question. It
  writes `LENNOX_MS_overflights.json`.
