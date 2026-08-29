# Pyfr24 development plan

This document lists planned features for the `pyfr24` tool.

## Feature roadmap

### In progress

- [ ] **Follow-ups from the visual outputs work**
    - [ ] Snap the origin and destination markers to the airports rather than the first and last fix. Tracking starts and stops near the runway, so a dot can sit a mile or two off, and on a tight zoom that reads as an error. Needs the airport coordinates from the dataset below, so it's blocked on that.
    - [ ] Two endpoint labels can still collide where a flight starts and ends near the same place, as on a diversion that returns to its origin. Placement is per-label today, with no awareness of what else is on the map.
    - [ ] A route with long sparse stretches can produce a very wide frame, because the extent still fits every fix and the aspect ratio then dictates the rest. Auckland to Los Angeles ends up showing Asia to South America. Worth deciding whether the frame should follow the tracked segments instead.
    - [ ] Endpoint labels are drawn with a white halo for legibility over a satellite basemap, and a path effect forces matplotlib to write them into SVG as outlined glyphs rather than live text. The headline, dek and source line are unaffected. A designer can't retype "In flight" without redrawing it, which sits awkwardly against the promise that SVG type stays editable. A background box would keep the text live but looks heavier.
    - [ ] A track can also carry a bad *position*, which would show as a zigzag rather than a cliff. The despiking is one-dimensional and only guards the value series, so the map is still exposed. Nothing in the local exports showed it, so this is untested speculation rather than a known defect.
    - [ ] Where a whole track is multilaterated, the speed chart now carries a note, but the line is still a mess of 200-knot swings. Worth deciding whether to smooth it, plot speed from successive positions instead of the reported field, or not draw the chart at all.
    - [ ] With `in_progress` known, the map could also show where the flight was *going*: a hollow marker at the scheduled destination, so a reader sees both the aircraft and the airport it hadn't reached. Blocked on the airport dataset below.
    - [ ] `in_progress` in `toplines.json` follows the summary record. Reading the landing time ahead of `flight_ended` fixed the common case, but a record briefly carries neither, between touchdown and the landing time being written, and an export caught in that window still writes `in_progress: true` for an aircraft on the ground. The map ignores it, because it can see the last fix; the JSON can't, since `export_flight_data` returns only its output directory. Worth passing the resolved status back out.

### Planned

- [ ] **Mapbox support**
    - [ ] Add a command to upload flight paths to Mapbox.
    - [ ] Read Mapbox API keys from the environment.

- [ ] **Easier flight lookup**
    - [ ] Add a `lookup` command to find all flight IDs from a flight number and date.

- [ ] **Better `--help` output**

    This is a limitation of the library, not of how we're using it. `cli.py` is
    built on argparse, which renders monochrome help and offers no styling hooks.
    Compare `mound`, which uses Typer and gets colored, paneled help for free.

    - [ ] Decide between two paths. `rich-argparse` is a drop-in `formatter_class` that colors the existing parsers with a one-line change and no restructuring. Migrating to Typer or Click is a rewrite of `cli.py`, but brings grouped options, better errors and shell completion.
    - [ ] Print help when `pyfr24` is run bare, instead of an error. Typer does this with `no_args_is_help=True`; argparse needs it wired by hand.
    - [ ] Stop repeating shared flags. `--background`, `--aspect`, `--orientation` and `--timezone` are defined separately on `export-flight` and `smart-export`, so their help text can drift apart. argparse parent parsers fix this; mound does it with shared `Annotated` option types.
    - [ ] Add examples to each subcommand's help, so `pyfr24 smart-export --help` shows a working invocation rather than only a flag list.

- [ ] **Flight path analysis**
    - [ ] Calculate flight stats like distance, duration, and max altitude.
    - [ ] Flag unusual events like rapid altitude changes.

- [ ] **API caching**
    - [ ] Cache API requests to speed up the tool and reduce errors.

- [ ] **Human names in viz and topline outputs**

    Headlines currently surface raw ICAO codes, so a reader sees "Flight path of
    DL2061 from KSNA to KMSP" and has to already know the airports. The target
    reads "Flight path of DL2061 from KSNA (Santa Ana, California) to KMSP
    (Minneapolis-St. Paul)".

    - [ ] Find an open airport dataset keyed on ICAO, with IATA alongside it. OurAirports publishes a public-domain CSV covering the world; the `airportsdata` package bundles a similar set for offline use. Prefer something vendored so an export doesn't depend on a second network call at render time.
    - [ ] Decide what to show. The full name ("John Wayne Airport") is often longer and less useful than the city ("Santa Ana, California"), and the two diverge for airports named after a different place than the one they serve.
    - [ ] Handle headline length. `_draw_chrome` places the headline with `fig.text` and doesn't wrap, so a long route will run past the frame. Either wrap, shrink, or fall back to bare codes past a character count.
    - [ ] Airlines: "DL2061" should be able to read "Delta Air Lines flight 2061". Same lookup problem, different table.
    - [ ] Carry the resolved names into `toplines.json` too, not just the graphics.

### Project maintenance

- [ ] Keep the version number and `CHANGELOG.md` updated.
- [ ] Keep the ReadTheDocs website in sync with new features.

## Completed

- [x] **Better visual outputs**
    - SVG and PDF output alongside PNG, via `--format png,svg`. Type is written as live text rather than outlines, so a label can be restyled in Illustrator instead of nudged around as paths.
    - Origin and destination marked with a dot and labeled with their airport code, placed under the dot so an east-west route doesn't run through the label.
    - Maps and charts break where ADS-B coverage stops (#3). The threshold scales with each flight's own median ping cadence, and a break has to cover ground, so an aircraft parked at a gate between pings stays one line.
    - A missing altitude or speed reading is plotted as missing rather than as zero, which used to draw a cliff to sea level mid-cruise.
    - Flights across the antimeridian are drawn over the Pacific rather than the long way around the world (#2). Longitude is unwrapped, and because the resulting extent is wider than the single world tile servers publish, the basemap is fetched a world at a time and composited. Contextily can't do this: it hands the bounds to mercantile, which clamps them, then reports success having rendered nothing past the edge.
    - The map is bordered in the same light gray as the chart gridlines, so it reads as a panel.
    - Deks spell out the tracked duration, with singulars handled.
    - Dropped `geopandas` and `shapely`, which existed for the one coordinate transform the antimeridian fix had to replace.

- [x] **Graphics that don't claim more than the data shows**

    Both defects here were found by reading finished graphics rather than by
    testing, and both were the same mistake: the graphic asserting something
    the track couldn't support.

    - A track that ends above 5,000 feet no longer gets the destination airport code. DL691 was drawn with a dot labeled "KJFK" while still at 39,000 feet over Pennsylvania. The end is now an arrowhead turned the way the aircraft was heading, labeled "In flight" when the API says the flight hadn't landed and "Last contact" when the track just ran out. Of 181 local exports, 42 ended at cruise altitude, so about one in four carried the wrong label.
    - `toplines.json` no longer reports an arrival time for a flight that hadn't landed; `arrival_time` was falling back to the last-seen moment. It's null now, with the last-seen time carried as `last_position_time` and an `in_progress` flag alongside.
    - A single implausible reading is dropped rather than drawn. NZ6 reported 30 knots at 35,000 feet between two readings near 500. A reading goes only when its neighbors agree with each other and it departs from both by more than 200 knots or 5,000 feet, so a real emergency descent, which plays out over several pings, survives.
    - The speed chart notes when a track is heavily multilaterated, since speeds inferred from signal timing swing by hundreds of knots and no point-by-point filter fixes that.

- [x] **More CLI examples in the README and docs**
    - Worked examples for a flight from the news by number and date, one flight at several aspect ratios, a Mapbox background with `MAPBOX_TOKEN`, converting to a local timezone, and finding every flight an aircraft flew.
    - Each shows what lands in the output directory, not just the command. Every subcommand already had at least one example, so the gap was scenarios rather than coverage.

- [x] **Time zone conversion**
    - Convert flight times from UTC to a local time zone.
    - Improve the `toplines.json` output to include human-readable date strings.

- [x] **Enhanced map backgrounds**
    - Key-free options from Esri, OpenStreetMap and OpenTopoMap, plus Mapbox with a user token.
    - Dropped the CARTO backgrounds once CARTO began requiring an API key.
    - Fixed the OSM user agent, which the tile server was blocking.

- [x] **Consistent framing**
    - Selectable aspect ratios (16:9, 3:2, 4:3, 1:1, 9:16) that the saved file matches exactly.
    - Map extent fits the frame rather than the frame fitting the data.

- [x] **Production-ready graphic layout**
    - Headline, dek and source line around every map and chart, all overridable.
    - House typography and palette, AP-style dates, units on the top axis tick.

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
