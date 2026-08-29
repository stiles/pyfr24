"""Plotting helpers for flight track data.

All map and chart rendering lives here so the API client stays focused on
talking to Flightradar24.

Graphics are laid out on a points grid where one point equals one pixel of the
design, then scaled up at save time. Type sizes therefore match a style guide
written in pixels, and the saved image keeps the requested aspect ratio exactly.
"""

import logging
import math
import os
import re
import statistics

import contextily as ctx
import contextily.tile
import matplotlib.dates as mdates
import matplotlib.patheffects as patheffects
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import xyzservices

logger = logging.getLogger(__name__)

try:
    from importlib.metadata import version

    _VERSION = version("pyfr24")
except Exception:
    _VERSION = "dev"

# OpenStreetMap serves a "blocked" placeholder image, with a 200 status, to
# clients that don't identify themselves under its tile usage policy.
# Contextily's default agent is a random hex string, which trips this.
contextily.tile.USER_AGENT = f"pyfr24/{_VERSION} (+https://github.com/stiles/pyfr24)"

COLOR_TEXT = "#262626"
COLOR_MUTED = "#8e8e8e"
COLOR_AXIS = "#A6A6A6"
COLOR_GRID = "#ececec"
COLOR_BASELINE = "#bcbcbc"
COLOR_BACKGROUND = "#FEFEFE"
COLOR_ROUTE = "#F18851"

FONT_STACK = ["CNN Sans Display", "Roboto", "Inter", "Helvetica Neue", "Arial", "DejaVu Sans"]

SIZE_HEADLINE = 18
SIZE_DEK = 15
SIZE_SOURCE = 12
SIZE_AXIS = 12
SIZE_LABEL = 12

# Layout constants, in points. The board width is the CMS maximum.
BOARD_WIDTH = 780
PAD = 14
GAP_HEADLINE_TO_DEK = 30
GAP_DEK_TO_PLOT = 25
GAP_PLOT_TO_SOURCE = 8
LINE_HEIGHT = 1.25

# Endpoint dot area in points squared, and the gap to its label in points. An
# arrowhead stands in for the dot where the aircraft flew on past the data, and
# reads better a little larger.
ENDPOINT_AREA = 44
ARROW_AREA = 115
LABEL_OFFSET = 10

# A track that stops above this altitude didn't stop at an airport. Receivers
# routinely lose an aircraft while it's still hundreds of miles out, and the
# last fix of a flight that hasn't landed yet is wherever it happened to be, so
# putting the destination code there claims an arrival the data doesn't show.
AIRBORNE_ALTITUDE_FT = 5000

# Formats matplotlib can write that are worth offering. SVG keeps the route,
# the type and the chrome as vectors for editing in Illustrator; the basemap
# is raster wherever it comes from, so it rides along as an embedded image.
OUTPUT_FORMATS = ('png', 'svg', 'pdf')
DEFAULT_OUTPUT_FORMATS = ('png',)

EARTH_RADIUS_M = 6378137.0

# EPSG:3857 runs this many meters either side of the prime meridian. A path
# across the antimeridian runs past that edge, which the tile servers know
# nothing about, so the basemap has to repeat the world to cover it.
WORLD_HALF_WIDTH = math.pi * EARTH_RADIUS_M

# Web Mercator can't represent the poles.
MAX_MERCATOR_LATITUDE = 85.051129

# A track breaks where the receivers lost the aircraft, and joining across the
# hole invents a path that was never reported. Ping cadence varies by region,
# so the threshold scales with each flight's own median interval rather than
# being fixed. Pings from an aircraft that hasn't moved are the other case,
# and an aircraft parked at a gate shouldn't fragment into dots, so a break
# also has to cover ground.
GAP_FLOOR_SECONDS = 300
GAP_CADENCE_MULTIPLE = 12
GAP_MIN_KM = 2.0

# A transponder now and then reports one reading no aircraft could have
# produced: 30 knots at 35,000 feet, say, between two readings near 500. Drawn,
# it puts a cliff on the chart that never happened. A real change, however
# violent, plays out over several pings and leaves the readings either side of
# it disagreeing with each other, so an isolated reading whose neighbors agree
# is the one kind it's safe to drop. Per field: how far a reading has to depart
# from its neighbors, and how closely those neighbors have to agree.
SPIKE_LIMITS = {
    'gspeed': (200, 30),
    'alt': (5000, 2000),
}

# Multilateration times a signal at several receivers to work out where an
# aircraft is, so speed derived from it jitters in a way an ADS-B reading
# doesn't. Past this share of the fixes, the chart says so rather than passing
# the wobble off as flying.
MLAT_NOTE_SHARE = 0.1
MLAT_NOTE = "Some speeds are estimated, not reported by the aircraft."

ASPECT_RATIOS = {
    '16:9': 16 / 9,
    '3:2': 3 / 2,
    '4:3': 4 / 3,
    '1:1': 1.0,
    '9:16': 9 / 16,
}

ORIENTATION_ASPECTS = {'horizontal': '16:9', 'vertical': '9:16'}

# Esri publishes a dark canvas, but xyzservices doesn't carry it.
ESRI_DARK_CANVAS = xyzservices.TileProvider(
    name='Esri.WorldDarkGrayCanvas',
    url='https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
    attribution='Tiles (C) Esri',
    max_zoom=16,
)

# Keys map to a provider and the short credit used in the source line.
BASEMAPS = {
    'osm': ('OpenStreetMap.Mapnik', 'OpenStreetMap contributors'),
    'esri-light': ('Esri.WorldGrayCanvas', 'Esri'),
    'esri-dark': (ESRI_DARK_CANVAS, 'Esri'),
    'esri-street': ('Esri.WorldStreetMap', 'Esri'),
    'esri-topo': ('Esri.WorldTopoMap', 'Esri'),
    'esri-satellite': ('Esri.WorldImagery', 'Esri'),
    'esri-natgeo': ('Esri.NatGeoWorldMap', 'Esri'),
    'opentopo': ('OpenTopoMap', 'OpenTopoMap'),
}

# CARTO withdrew anonymous basemap access; their tiles now return watermarked
# "API key required" images.
RETIRED_BASEMAPS = {'carto': 'esri-light', 'carto-light': 'esri-light', 'carto-dark': 'esri-dark'}

# OSM labels cities and states at national zooms, which the Esri gray canvas
# drops, so a cross-country route stays readable without extra annotation.
DEFAULT_BASEMAP = 'osm'

# Mapbox style IDs carry a version suffix, so 'mapbox-light' has to become
# 'light-v11' rather than 'light', which 404s.
MAPBOX_STYLE_ALIASES = {
    'light': 'light-v11',
    'dark': 'dark-v11',
    'streets': 'streets-v12',
    'outdoors': 'outdoors-v12',
    'satellite': 'satellite-v9',
    'satellite-streets': 'satellite-streets-v12',
    'navigation-day': 'navigation-day-v1',
    'navigation-night': 'navigation-night-v1',
}
DEFAULT_MAPBOX_STYLE = 'light'

NAMED_TIMEZONES = {
    'America/New_York': 'Eastern time',
    'America/Chicago': 'Central time',
    'America/Denver': 'Mountain time',
    'America/Phoenix': 'Mountain time',
    'America/Los_Angeles': 'Pacific time',
    'America/Anchorage': 'Alaska time',
    'Pacific/Honolulu': 'Hawaii time',
}

# AP style abbreviates all months except March through July.
AP_MONTHS = {
    1: 'Jan.', 2: 'Feb.', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
    7: 'July', 8: 'Aug.', 9: 'Sept.', 10: 'Oct.', 11: 'Nov.', 12: 'Dec.',
}

# Tick spacings in minutes, coarsening as flight duration grows.
TICK_STEPS_MINUTES = [5, 10, 15, 30, 60, 90, 120, 180, 360, 720, 1440]
TARGET_TICK_COUNT = 5


def configure_style():
    """Apply the house typography and colors to matplotlib's defaults."""
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.sans-serif': FONT_STACK,
        'text.color': COLOR_TEXT,
        'figure.facecolor': COLOR_BACKGROUND,
        'axes.facecolor': COLOR_BACKGROUND,
        'savefig.facecolor': COLOR_BACKGROUND,
        'xtick.color': COLOR_AXIS,
        'ytick.color': COLOR_AXIS,
        'xtick.labelsize': SIZE_AXIS,
        'ytick.labelsize': SIZE_AXIS,
        'grid.color': COLOR_GRID,
        'grid.linewidth': 1,
        'axes.edgecolor': COLOR_GRID,
        'axes.linewidth': 0.5,
        # Keep SVG type as text rather than outlines, so an editor can restyle
        # or retype a label instead of nudging paths around.
        'svg.fonttype': 'none',
    })


configure_style()


def format_ap_date(value):
    """Format a date AP style, e.g. 'Aug. 28, 2026'."""
    return f"{AP_MONTHS[value.month]} {value.day}, {value.year}"


def _plural(count, noun):
    """Return the count and its noun, pluralized to match."""
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def _format_duration(start, end):
    """Return a duration like '2 hours, 51 minutes', or None if it isn't meaningful."""
    minutes = int(round((end - start).total_seconds() / 60))
    if minutes <= 0:
        return None

    hours, minutes = divmod(minutes, 60)
    parts = []
    if hours:
        parts.append(_plural(hours, 'hour'))
    if minutes:
        parts.append(_plural(minutes, 'minute'))
    return ', '.join(parts)


def _timezone_label(timestamps, timezone=None):
    """Return a human-readable timezone label, or None for naive timestamps.

    Track timestamps round-trip through ISO strings, which reduces a named zone
    to a fixed offset, so the caller's zone name wins when it's available.
    """
    if not timestamps:
        return None

    first = timestamps[0]
    tz = getattr(first, 'tz', None)
    if tz is None:
        return None

    name = timezone or str(tz)
    if name in NAMED_TIMEZONES:
        return NAMED_TIMEZONES[name]

    # strftime gives 'UTC', 'EDT' and so on for named zones, but a numeric
    # offset like '+0900' for fixed-offset ones.
    abbreviation = first.strftime('%Z')
    if abbreviation and not abbreviation[0].isdigit() and abbreviation[0] not in '+-':
        return abbreviation

    offset = first.strftime('%z')
    return f"UTC{offset[:3]}:{offset[3:]}" if offset else None


def aspect_key(aspect=None, orientation=None):
    """Pick an aspect key from an explicit aspect or a legacy orientation.

    'auto' has no fixed key, since it depends on the data; the map resolves it.
    """
    return aspect or ORIENTATION_ASPECTS.get(orientation) or '16:9'


def resolve_aspect(aspect=None, orientation=None, bounds=None):
    """Resolve an aspect key to a width/height ratio.

    `aspect` wins when given. Otherwise `orientation` maps to a ratio, with
    'auto' choosing landscape or portrait from the shape of the data.
    """
    if aspect:
        if aspect in ASPECT_RATIOS:
            return ASPECT_RATIOS[aspect]
        if ':' in str(aspect):
            try:
                w, h = (float(part) for part in str(aspect).split(':'))
                if w > 0 and h > 0:
                    return w / h
            except ValueError:
                pass
        logger.warning(f"Unknown aspect '{aspect}', falling back to 16:9")
        return ASPECT_RATIOS['16:9']

    if orientation == 'auto' and bounds is not None:
        xmin, ymin, xmax, ymax = bounds
        orientation = 'horizontal' if (xmax - xmin) > (ymax - ymin) else 'vertical'

    return ASPECT_RATIOS[ORIENTATION_ASPECTS.get(orientation, '16:9')]


def unwrap_longitudes(lons):
    """Shift longitudes so a path across the antimeridian stays continuous.

    Each value moves by whole turns until it sits within half a turn of the one
    before it, so a Tokyo-to-Los Angeles track reads 139, 150 ... 230, 242
    rather than falling off the east edge and reappearing on the west. Values
    can end up past 180, which is the point: the alternative is a line that
    leaps the width of the world.
    """
    unwrapped = [float(lons[0])]
    for lon in lons[1:]:
        lon = float(lon)
        unwrapped.append(lon + 360 * round((unwrapped[-1] - lon) / 360))
    return unwrapped


def to_web_mercator(lats, lons):
    """Project degrees to EPSG:3857 meters, as (x, y) arrays.

    Worked out here rather than handed to a CRS transform because a transform
    folds longitude back into 180 degrees, undoing `unwrap_longitudes`.
    """
    xs = [math.radians(lon) * EARTH_RADIUS_M for lon in lons]
    ys = []
    for lat in lats:
        clamped = min(max(float(lat), -MAX_MERCATOR_LATITUDE), MAX_MERCATOR_LATITUDE)
        ys.append(math.log(math.tan(math.pi / 4 + math.radians(clamped) / 2)) * EARTH_RADIUS_M)
    return np.array(xs), np.array(ys)


def _mercator_to_latitude(y):
    """Invert the Web Mercator y coordinate back to degrees."""
    return math.degrees(2 * math.atan(math.exp(y / EARTH_RADIUS_M)) - math.pi / 2)


def _distance_km(lat1, lon1, lat2, lon2):
    """Great-circle distance between two points, in kilometers."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    half_dphi = (phi2 - phi1) / 2
    half_dlambda = math.radians(lon2 - lon1) / 2
    a = math.sin(half_dphi) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(half_dlambda) ** 2
    return 2 * (EARTH_RADIUS_M / 1000) * math.asin(min(1.0, math.sqrt(a)))


def gap_threshold_seconds(timestamps):
    """Return the interval that counts as lost coverage for one track."""
    intervals = [(b - a).total_seconds() for a, b in zip(timestamps, timestamps[1:])
                 if a is not None and b is not None]
    intervals = [interval for interval in intervals if interval > 0]
    if not intervals:
        return GAP_FLOOR_SECONDS
    return max(GAP_FLOOR_SECONDS, GAP_CADENCE_MULTIPLE * statistics.median(intervals))


def gap_indices(timestamps, positions=None, gap_seconds=None):
    """Return the indices a track breaks after, as a set.

    A break belongs between point i and point i + 1. Pass `positions` as
    (lat, lon) pairs to keep an aircraft that sat still between pings from
    breaking; without them, every long interval counts.
    """
    if len(timestamps) < 2:
        return set()

    threshold = gap_seconds or gap_threshold_seconds(timestamps)
    breaks = set()

    for i, (start, end) in enumerate(zip(timestamps, timestamps[1:])):
        if start is None or end is None:
            continue
        if (end - start).total_seconds() <= threshold:
            continue

        if positions is not None:
            (lat1, lon1), (lat2, lon2) = positions[i], positions[i + 1]
            if None not in (lat1, lon1, lat2, lon2):
                if _distance_km(lat1, lon1, lat2, lon2) < GAP_MIN_KM:
                    continue

        breaks.add(i)

    return breaks


def implausible_indices(values, limits):
    """Return the indices of isolated readings no aircraft could have produced.

    A reading qualifies when the readings either side of it agree with each
    other within `tolerance` and it departs from their midpoint by more than
    `threshold`. Both halves of that test carry weight: the departure is what
    makes a reading suspect, and the agreement either side is what separates a
    sensor glitch from a real and violent change, which a chart should keep.
    """
    if not limits:
        return set()

    threshold, tolerance = limits
    found = set()

    for i in range(1, len(values) - 1):
        before, value, after = values[i - 1], values[i], values[i + 1]
        if not all(isinstance(v, (int, float)) and math.isfinite(v)
                   for v in (before, value, after)):
            continue
        if abs(after - before) > tolerance:
            continue
        if abs(value - (before + after) / 2) > threshold:
            found.add(i)

    return found


def mlat_share(tracks):
    """Return the share of fixes located by multilateration rather than ADS-B."""
    if not tracks:
        return 0.0
    return sum(1 for track in tracks
               if str(track.get('source') or '').upper() == 'MLAT') / len(tracks)


def insert_breaks(values, breaks):
    """Return the series as a float array with NaN after each break index.

    matplotlib lifts the pen at a NaN, which is how a gap in coverage reads as
    a gap rather than as a straight line drawn through it.
    """
    if not breaks:
        return np.asarray(values, dtype=float)

    broken = []
    for i, value in enumerate(values):
        broken.append(value)
        if i in breaks:
            broken.append(np.nan)
    return np.asarray(broken, dtype=float)


def resolve_basemap(background):
    """Return (provider, credit) for a basemap key.

    Falls back to the default basemap when a key is unknown, retired or is
    missing the token it needs, so a map still renders.
    """
    key = (background or DEFAULT_BASEMAP).lower()

    if key in RETIRED_BASEMAPS:
        replacement = RETIRED_BASEMAPS[key]
        logger.warning(
            f"Basemap '{key}' needs a CARTO API key and is no longer supported; "
            f"using '{replacement}' instead."
        )
        key = replacement

    if key.startswith('mapbox'):
        provider = _mapbox_provider(key)
        if provider is not None:
            return provider, 'Mapbox'
        key = DEFAULT_BASEMAP

    if key not in BASEMAPS:
        logger.warning(f"Unknown basemap '{key}'; using '{DEFAULT_BASEMAP}'.")
        key = DEFAULT_BASEMAP

    path, credit = BASEMAPS[key]
    try:
        return _lookup_provider(path), credit
    except KeyError:
        logger.warning(f"Basemap '{key}' is unavailable in this xyzservices build; using '{DEFAULT_BASEMAP}'.")
        path, credit = BASEMAPS[DEFAULT_BASEMAP]
        return _lookup_provider(path), credit


def _lookup_provider(path):
    """Resolve a dotted xyzservices path, or pass a ready-made provider through."""
    if not isinstance(path, str):
        return path

    provider = ctx.providers
    for part in path.split('.'):
        provider = provider[part]
    return provider


def _mapbox_provider(key):
    """Build a Mapbox provider from MAPBOX_TOKEN, or None when unavailable."""
    token = os.getenv('MAPBOX_TOKEN') or os.getenv('MAPBOX_ACCESS_TOKEN')
    if not token:
        logger.warning("Mapbox basemap requested but MAPBOX_TOKEN is not set; using the default basemap.")
        return None

    style = key[len('mapbox-'):] if key.startswith('mapbox-') else ''
    style = style or DEFAULT_MAPBOX_STYLE

    # A slash means a custom style ('username/styleid'), which passes through.
    if '/' not in style:
        if style in MAPBOX_STYLE_ALIASES:
            style = MAPBOX_STYLE_ALIASES[style]
        elif not re.search(r'-v\d+$', style):
            logger.warning(
                f"Mapbox style '{style}' is not a known alias ({', '.join(MAPBOX_STYLE_ALIASES)}) "
                "and carries no version suffix; requesting it as given."
            )
        style = f"mapbox/{style}"

    return xyzservices.TileProvider({**ctx.providers.MapBox, 'id': style, 'accessToken': token})


def _auto_zoom(provider, xmin, xmax, ymin, ymax):
    """Pick a zoom level for an extent, which may be wider than the world.

    Follows contextily's own rule of fitting the extent in about four tiles,
    reimplemented because contextily's version reads the extent in degrees and
    can't be handed one that runs past the antimeridian.
    """
    lon_span = abs(xmax - xmin) / WORLD_HALF_WIDTH * 180
    lat_span = abs(_mercator_to_latitude(ymax) - _mercator_to_latitude(ymin))

    levels = [math.ceil(math.log2(720 / span)) for span in (lon_span, lat_span) if span > 0]
    level = min(levels) if levels else provider.get('max_zoom', 19)
    return max(provider.get('min_zoom', 0), min(level, provider.get('max_zoom', 19)))


def _world_copies(xmin, xmax):
    """Yield (left, right, shift) for each copy of the world an extent covers.

    `shift` is the offset from the real x back into the one world tile servers
    publish, so a piece can be requested there and drawn where it belongs.
    """
    world_width = 2 * WORLD_HALF_WIDTH
    first = math.floor((xmin + WORLD_HALF_WIDTH) / world_width)
    last = math.floor((xmax + WORLD_HALF_WIDTH) / world_width)

    for copy in range(first, last + 1):
        shift = copy * world_width
        left = max(xmin, shift - WORLD_HALF_WIDTH)
        right = min(xmax, shift + WORLD_HALF_WIDTH)
        if right > left:
            yield left, right, shift


def _draw_tiles(ax, provider, zoom):
    """Draw basemap tiles behind the current extent, and keep that extent.

    An extent inside the world goes to contextily. One that crosses the
    antimeridian can't: contextily hands the bounds to mercantile, which clamps
    them, so the tiles stop dead at the edge and the rest of the panel comes
    back blank. Those get fetched a world at a time and placed by hand.
    """
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()

    if -WORLD_HALF_WIDTH <= xmin and xmax <= WORLD_HALF_WIDTH:
        # reset_extent must stay True: when False, contextily widens the axes to
        # the tile boundary and the fitted aspect ratio is lost.
        kwargs = {'reset_extent': True, 'attribution': False}
        if zoom is not None:
            kwargs['zoom'] = zoom
        ctx.add_basemap(ax, source=provider, **kwargs)
        return

    level = zoom if zoom is not None else _auto_zoom(provider, xmin, xmax, ymin, ymax)

    for left, right, shift in _world_copies(xmin, xmax):
        image, extent = ctx.bounds2img(left - shift, ymin, right - shift, ymax,
                                       zoom=level, source=provider, ll=False)
        ax.imshow(image, extent=(extent[0] + shift, extent[1] + shift, extent[2], extent[3]),
                  interpolation='bilinear', origin='upper')

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)


def _add_basemap(ax, provider, credit, zoom, log):
    """Draw the basemap, retrying with the default when the tiles fail.

    Tile servers fail at request time, not when the provider is built, so a bad
    style ID or a revoked token only surfaces here. Returns the credit for the
    basemap actually drawn, or None when the map is left bare.
    """
    xlim, ylim = ax.get_xlim(), ax.get_ylim()

    try:
        _draw_tiles(ax, provider, zoom)
        return credit
    except Exception as e:
        log.error(f"Could not load the {credit} basemap: {e}")

    fallback, fallback_credit = resolve_basemap(DEFAULT_BASEMAP)
    if provider is fallback:
        return None

    log.warning(f"Falling back to the {fallback_credit} basemap.")
    # A failed attempt can leave the axes rescaled.
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)

    try:
        _draw_tiles(ax, fallback, zoom)
        return fallback_credit
    except Exception as e:
        log.error(f"The {fallback_credit} basemap failed too; drawing the route on its own: {e}")
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        return None


def _figure(ratio):
    """Create a figure sized to the board width at the given ratio."""
    width = BOARD_WIDTH
    height = width / ratio
    fig = plt.figure(figsize=(width / 72, height / 72))
    return fig, width, height


def _draw_chrome(fig, width, height, headline, dek, source):
    """Draw headline, dek and source line; return the free vertical band.

    Returns (top, bottom, source_text): the band in points measured from the
    bottom of the figure, plus the source artist so callers can correct the
    basemap credit once the tiles have actually loaded.
    """
    top = height - PAD

    if headline:
        fig.text(PAD / width, top / height, headline, ha='left', va='top',
                 fontsize=SIZE_HEADLINE, fontweight='bold', color=COLOR_TEXT)
        top -= SIZE_HEADLINE * LINE_HEIGHT

    if dek:
        dek_top = height - PAD - GAP_HEADLINE_TO_DEK if headline else top
        fig.text(PAD / width, dek_top / height, dek, ha='left', va='top',
                 fontsize=SIZE_DEK, color=COLOR_TEXT)
        top = dek_top - SIZE_DEK * LINE_HEIGHT

    top -= GAP_DEK_TO_PLOT

    bottom = PAD
    source_text = None
    if source:
        source_text = fig.text(PAD / width, bottom / height, source, ha='left', va='bottom',
                               fontsize=SIZE_SOURCE, color=COLOR_MUTED)
        bottom += SIZE_SOURCE * LINE_HEIGHT + GAP_PLOT_TO_SOURCE

    return top, bottom, source_text


def _add_axes(fig, width, height, top, bottom, left=PAD, right=PAD):
    """Place an axes in the free band, in points, and return it."""
    plot_width = width - left - right
    plot_height = top - bottom
    return fig.add_axes([left / width, bottom / height, plot_width / width, plot_height / height])


def _frame_panel(ax):
    """Border the axes so the basemap reads as a panel instead of bleeding out.

    Matches the weight and color of the gridlines on the charts, so a map and a
    chart from the same flight sit together on a page.
    """
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color(COLOR_GRID)
        spine.set_linewidth(1)
        spine.set_zorder(6)


def endpoint_marks(fixes, origin=None, destination=None, in_progress=None):
    """Decide what belongs at each end of a track.

    Returns (index, label, airborne, heading) for the first and last fix. An
    airport code only goes on an end that reached the ground: above
    AIRBORNE_ALTITUDE_FT the line stops where the data stops, not where the
    aircraft did, so the end says which way it was pointed and is labeled for
    what it is. Pass `in_progress` when the API says the flight hadn't landed,
    which is the difference between an aircraft still flying and one whose
    track simply ran out.
    """
    marks = []

    for index, code, fallback in ((0, origin, 'First contact'),
                                  (-1, destination, 'Last contact')):
        fix = fixes[index]
        try:
            altitude = float(fix.get('alt'))
        except (TypeError, ValueError):
            altitude = None

        if altitude is None or altitude <= AIRBORNE_ALTITUDE_FT:
            marks.append((index, code, False, None))
            continue

        try:
            heading = float(fix.get('track'))
        except (TypeError, ValueError):
            heading = None

        label = 'In flight' if in_progress and index == -1 else fallback
        marks.append((index, label, True, heading))

    return marks


def _screen_heading(xs, ys, index):
    """Work out which way the track was pointed at one end, from its geometry.

    A fallback for a fix that didn't report a heading. Web Mercator preserves
    angles, so a bearing on the page is a bearing in the air.
    """
    if len(xs) < 2:
        return None

    if index == 0:
        dx, dy = xs[1] - xs[0], ys[1] - ys[0]
    else:
        dx, dy = xs[-1] - xs[-2], ys[-1] - ys[-2]

    if not (np.isfinite(dx) and np.isfinite(dy)) or (dx == 0 and dy == 0):
        return None

    return math.degrees(math.atan2(dx, dy)) % 360


def _draw_endpoints(ax, xs, ys, marks):
    """Mark each end of the track and label it.

    A dot is an end that reached the ground; an arrowhead is an aircraft still
    flying, turned the way it was last heading. A label sits under its mark
    rather than beside it, since most routes run east to west and a label set
    alongside would land on the line; it moves above the mark near the foot of
    the panel, and hugs the left or right edge instead of centering when it
    would otherwise overflow.
    """
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    x_span, y_span = xmax - xmin, ymax - ymin
    halo = [patheffects.withStroke(linewidth=3, foreground=COLOR_BACKGROUND)]

    for index, label, airborne, heading in marks:
        x, y = xs[index], ys[index]
        if not (np.isfinite(x) and np.isfinite(y)):
            continue

        if airborne:
            if heading is None:
                heading = _screen_heading(xs, ys, index)
            # A three-sided marker points north unrotated, and matplotlib turns
            # it anticlockwise, against the way a compass counts.
            marker, area = (3, 0, -(heading or 0)), ARROW_AREA
        else:
            marker, area = 'o', ENDPOINT_AREA

        ax.scatter([x], [y], s=area, marker=marker, color=COLOR_ROUTE,
                   edgecolor=COLOR_BACKGROUND, linewidth=1.5, zorder=4)

        if not label:
            continue

        low = y_span > 0 and (y - ymin) / y_span < 0.15
        across = (x - xmin) / x_span if x_span > 0 else 0.5
        ha = 'left' if across < 0.06 else 'right' if across > 0.94 else 'center'

        offset = LABEL_OFFSET + (3 if airborne else 0)
        ax.annotate(str(label), (x, y), textcoords='offset points',
                    xytext=(0, offset if low else -offset),
                    ha=ha, va='bottom' if low else 'top', fontsize=SIZE_LABEL,
                    fontweight='bold', color=COLOR_TEXT, zorder=5, path_effects=halo)


def resolve_formats(formats):
    """Normalize requested image formats to a de-duplicated tuple.

    Accepts a list or a comma-separated string, and drops anything that isn't
    an offered format rather than letting matplotlib fail at save time.
    """
    if not formats:
        return DEFAULT_OUTPUT_FORMATS

    if isinstance(formats, str):
        formats = formats.split(',')

    resolved = []
    for fmt in formats:
        fmt = str(fmt).strip().lower().lstrip('.')
        if not fmt or fmt in resolved:
            continue
        if fmt not in OUTPUT_FORMATS:
            logger.warning(f"Unknown output format '{fmt}'; skipping it. "
                           f"Choose from {', '.join(OUTPUT_FORMATS)}.")
            continue
        resolved.append(fmt)

    return tuple(resolved) or DEFAULT_OUTPUT_FORMATS


def _save_figure(fig, output_file, formats, dpi, log, label='Graphic'):
    """Write the figure once per format, reusing the output file's stem.

    So 'map.png' with ('png', 'svg') writes map.png beside map.svg, and the
    file's own extension stands in when no format is asked for. Returns the
    paths written, and logs rather than raises when one fails, so a format that
    can't be written doesn't cost the others.
    """
    if not output_file:
        return []

    stem, extension = os.path.splitext(output_file)

    written = []
    for fmt in resolve_formats(formats or extension):
        path = f"{stem}.{fmt}"
        try:
            if directory := os.path.dirname(path):
                os.makedirs(directory, exist_ok=True)
            fig.savefig(path, dpi=dpi)
            written.append(path)
            log.info(f"{label} saved to {path}")
        except Exception as e:
            log.error(f"Error saving {label.lower()} to {path}: {e}")

    return written


def _fit_extent(bounds, ratio, pad_factor):
    """Expand data bounds to exactly fill an axes of the given ratio."""
    xmin, ymin, xmax, ymax = bounds
    center_x = (xmin + xmax) / 2
    center_y = (ymin + ymax) / 2

    # A stationary aircraft collapses the bounds to a point.
    span_x = max(xmax - xmin, 1000.0) * (1 + 2 * pad_factor)
    span_y = max(ymax - ymin, 1000.0) * (1 + 2 * pad_factor)

    if span_x / span_y < ratio:
        span_x = span_y * ratio
    else:
        span_y = span_x / ratio

    return (center_x - span_x / 2, center_x + span_x / 2,
            center_y - span_y / 2, center_y + span_y / 2)


def _extract_series(tracks, value_key, value_limits, log):
    """Pull a plottable series out of track points, dropping bad rows.

    Returns timestamps, values and (lat, lon) positions, all the same length.
    A missing reading becomes NaN rather than zero: the aircraft wasn't at sea
    level, the receiver just didn't report, and a zero draws a cliff that never
    happened. A reading that arrived but couldn't have been true goes out
    altogether, so the line runs between the fixes either side of it. Positions
    come back so the caller can tell a coverage gap from an aircraft standing
    still.
    """
    minimum, maximum = value_limits
    timestamps = []
    values = []
    positions = []

    for i, track in enumerate(tracks):
        try:
            if track.get('timestamp') is None:
                log.debug(f"Skipping track {i}: missing timestamp")
                continue

            raw = track.get(value_key)
            value = float('nan') if raw is None else float(raw)

            if value < minimum or value > maximum:
                log.debug(f"Skipping track {i}: {value_key} out of range ({value})")
                continue

            timestamps.append(pd.to_datetime(track['timestamp']))
            values.append(value)
            positions.append((track.get('lat'), track.get('lon')))
        except (ValueError, TypeError) as e:
            log.debug(f"Skipping track {i}: error processing data - {e}")
            continue

    if spikes := implausible_indices(values, SPIKE_LIMITS.get(value_key)):
        log.info(f"Dropped {len(spikes)} implausible {value_key} reading(s)")
        for i in sorted(spikes):
            log.debug(f"Dropped {value_key} of {values[i]} at {timestamps[i]}")
        keep = [i for i in range(len(values)) if i not in spikes]
        timestamps = [timestamps[i] for i in keep]
        values = [values[i] for i in keep]
        positions = [positions[i] for i in keep]

    return timestamps, values, positions


def _break_series(timestamps, values, breaks):
    """Return x and y for a line that lifts at each break.

    The break gets a point of its own, halfway between the fixes either side,
    so the line stops where coverage stopped rather than at the last ping.
    """
    if not breaks:
        return timestamps, np.asarray(values, dtype=float)

    xs, ys = [], []
    for i, (timestamp, value) in enumerate(zip(timestamps, values)):
        xs.append(timestamp)
        ys.append(value)
        if i in breaks:
            xs.append(timestamp + (timestamps[i + 1] - timestamp) / 2)
            ys.append(float('nan'))

    return xs, np.asarray(ys, dtype=float)


def _route_phrase(flight_number, origin, destination, flight_id):
    """Describe the flight for a headline."""
    if flight_number and origin and destination:
        return f"{flight_number} from {origin} to {destination}"
    if flight_number:
        return str(flight_number)
    return f"flight {flight_id}"


def _default_dek(timestamps, in_progress=None):
    """Date and tracked duration, as available.

    Says so when the flight hadn't landed, since a duration on its own reads as
    the length of a finished trip.
    """
    if not timestamps:
        return None
    parts = [format_ap_date(timestamps[0])]
    if len(timestamps) > 1 and (duration := _format_duration(timestamps[0], timestamps[-1])):
        parts.append(f"{duration} tracked")
    if in_progress:
        parts.append("still in the air")
    return " · ".join(parts)


def _configure_time_axis(ax, timestamps, tz):
    """Pick a tick interval that keeps the x-axis to about five labels."""
    duration_minutes = 60
    if len(timestamps) > 1:
        duration_minutes = max((timestamps[-1] - timestamps[0]).total_seconds() / 60, 1)

    step = TICK_STEPS_MINUTES[-1]
    for candidate in TICK_STEPS_MINUTES:
        if duration_minutes / candidate <= TARGET_TICK_COUNT:
            step = candidate
            break

    if step < 60:
        ax.xaxis.set_major_locator(mdates.MinuteLocator(byminute=range(0, 60, step), tz=tz))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%-I:%M %p', tz=tz))
    elif step < 1440:
        hours = max(step // 60, 1)
        ax.xaxis.set_major_locator(mdates.HourLocator(byhour=range(0, 24, hours), tz=tz))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%-I %p', tz=tz))
    else:
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(step // 1440, 1), tz=tz))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %-d', tz=tz))


def _configure_value_axis(ax, values, value_formatter, unit):
    """Set y ticks from zero, carrying the unit on the top tick only."""
    readings = [value for value in values if not math.isnan(value)]
    ceiling = max(readings) if readings else 1

    ticks = mticker.MaxNLocator(nbins=5, steps=[1, 2, 2.5, 5, 10]).tick_values(0, ceiling)
    ticks = [t for t in ticks if t >= 0]
    while ticks and ticks[-1] < ceiling:
        ticks.append(ticks[-1] + (ticks[-1] - ticks[-2]))

    # Top out at the highest tick so the unit label sits at the frame rather
    # than below the peak of the line.
    ax.set_ylim(0, ticks[-1] if ticks else ceiling)

    labels = [value_formatter(t) for t in ticks]
    if labels and unit:
        labels[-1] = f"{labels[-1]} {unit}"

    ax.set_yticks(ticks)
    ax.set_yticklabels(labels)


def plot_series_chart(
    tracks,
    flight_id,
    output_file,
    value_key,
    metric_label,
    unit,
    value_limits,
    value_formatter,
    flight_number=None,
    origin=None,
    destination=None,
    timezone=None,
    aspect=None,
    headline=None,
    dek=None,
    source=None,
    data_note=None,
    dpi=200,
    formats=None,
    gap_seconds=None,
    log=None,
):
    """Render a time-series line chart for one numeric field of a flight track.

    Args:
        tracks: List of track points.
        flight_id: Flight identifier, used in the headline fallback.
        output_file: Path to write the image to.
        value_key: Track field to plot (e.g. 'alt' or 'gspeed').
        metric_label: Measure named in the headline (e.g. 'Altitude').
        unit: Unit appended to the top y-axis tick (e.g. 'feet').
        value_limits: (min, max) tuple of plausible values; rows outside are dropped.
        value_formatter: Callable turning a y value into a tick label.
        timezone: IANA zone the timestamps were converted to, for the source line.
        aspect: Aspect ratio key for the finished graphic.
        headline, dek, source: Copy overrides; sensible defaults are built when omitted.
        data_note: Caveat appended to the default source line, e.g. for estimated readings.
        formats: Image formats to write, e.g. ('png', 'svg'); PNG when omitted.
        gap_seconds: Interval that counts as lost coverage; scaled to the track when omitted.
    """
    log = log or logger

    timestamps, values, positions = _extract_series(tracks, value_key, value_limits, log)
    if not timestamps:
        log.warning(f"No valid {value_key} data available for plotting")
        return

    log.debug(f"Creating {value_key} chart with {len(timestamps)} points")

    route = _route_phrase(flight_number, origin, destination, flight_id)
    headline = headline or f"{metric_label} of {route}"
    dek = dek if dek is not None else _default_dek(timestamps)

    if source is None:
        parts = ["Source: Flightradar24"]
        if tz_label := _timezone_label(timestamps, timezone):
            parts.append(f"Times in {tz_label}")
        if data_note:
            parts.append(str(data_note).rstrip('.'))
        source = ". ".join(parts) + ("." if len(parts) > 1 else "")

    fig, width, height = _figure(resolve_aspect(aspect))
    top, bottom, _ = _draw_chrome(fig, width, height, headline, dek, source)

    # Room for the x tick labels between the plot and the source line.
    bottom += SIZE_AXIS * 1.8
    left = PAD + SIZE_AXIS * 5
    ax = _add_axes(fig, width, height, top, bottom, left=left, right=PAD)

    breaks = gap_indices(timestamps, positions=positions, gap_seconds=gap_seconds)
    if breaks:
        log.debug(f"Breaking the {value_key} line at {len(breaks)} coverage gap(s)")
    xs, ys = _break_series(timestamps, values, breaks)
    ax.plot(xs, ys, color=COLOR_ROUTE, linewidth=2)

    ax.set_xlim(timestamps[0], timestamps[-1])
    tz = getattr(timestamps[0], 'tz', None)
    _configure_time_axis(ax, timestamps, tz)
    _configure_value_axis(ax, values, value_formatter, unit)

    ax.grid(True, axis='y', linestyle='-', linewidth=1, color=COLOR_GRID)
    ax.set_axisbelow(True)
    ax.axhline(0, color=COLOR_BASELINE, linewidth=1)

    for side in ('top', 'right', 'left', 'bottom'):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0, colors=COLOR_AXIS, labelsize=SIZE_AXIS)

    _save_figure(fig, output_file, formats, dpi, log, label=f"{metric_label} chart")
    plt.close(fig)


def plot_speed_chart(tracks, flight_id, output_file, flight_number=None, origin=None,
                     destination=None, timezone=None, aspect=None, dpi=200, formats=None,
                     gap_seconds=None, log=None):
    """Create a line chart of ground speed over time.

    Notes the source of the readings on the graphic when much of the track was
    fixed by multilateration, whose speeds wobble by a good margin.
    """
    plot_series_chart(
        tracks,
        flight_id,
        output_file,
        value_key='gspeed',
        metric_label="Ground speed",
        unit="knots",
        value_limits=(0, 1000),
        value_formatter=lambda v: f"{int(v):,}",
        flight_number=flight_number,
        origin=origin,
        destination=destination,
        timezone=timezone,
        aspect=aspect,
        data_note=MLAT_NOTE if mlat_share(tracks) >= MLAT_NOTE_SHARE else None,
        dpi=dpi,
        formats=formats,
        gap_seconds=gap_seconds,
        log=log,
    )


def plot_altitude_chart(tracks, flight_id, output_file, flight_number=None, origin=None,
                        destination=None, timezone=None, aspect=None, dpi=200, formats=None,
                        gap_seconds=None, log=None):
    """Create a line chart of altitude over time."""
    plot_series_chart(
        tracks,
        flight_id,
        output_file,
        value_key='alt',
        metric_label="Altitude",
        unit="feet",
        value_limits=(0, 50000),
        value_formatter=lambda v: f"{int(v):,}",
        flight_number=flight_number,
        origin=origin,
        destination=destination,
        timezone=timezone,
        aspect=aspect,
        dpi=dpi,
        formats=formats,
        gap_seconds=gap_seconds,
        log=log,
    )


def plot_flight_map(sorted_tracks, flight_id, fig_filename=None, orientation=None,
                    aspect=None, pad_factor=0.12, zoom=None, background=DEFAULT_BASEMAP,
                    flight_number=None, origin=None, destination=None, timezone=None,
                    headline=None, dek=None, source=None, dpi=200, formats=None,
                    gap_seconds=None, endpoints=True, in_progress=None, log=None):
    """
    Plot a flight path over a basemap, framed to an exact aspect ratio.

    Args:
        sorted_tracks: List of track points.
        flight_id: Flight identifier.
        fig_filename: Output filename for the plot.
        orientation: Legacy 'horizontal', 'vertical' or 'auto'; `aspect` wins.
        aspect: Aspect ratio key ('16:9', '3:2', '4:3', '1:1', '9:16' or 'W:H').
        pad_factor: Padding around the flight path, before aspect fitting.
        zoom: Basemap zoom level; determined automatically when None.
        background: Basemap key from BASEMAPS, or 'mapbox[-style]'.
        headline, dek, source: Copy overrides.
        formats: Image formats to write, e.g. ('png', 'svg'); PNG when omitted.
        gap_seconds: Interval that counts as lost coverage; scaled to the track when omitted.
        endpoints: Mark the first and last fix, labeled with the airport codes.
        in_progress: True when the flight hadn't landed, which changes what the
            end of the line is called and adds a note to the dek.
    """
    log = log or logger
    log.debug(f"Starting plot_flight_map with {len(sorted_tracks)} track points")

    fixes = [track for track in sorted_tracks
             if track.get('lat') is not None and track.get('lon') is not None]
    if not fixes:
        log.warning("No data available to plot.")
        return

    try:
        lats = [float(track['lat']) for track in fixes]
        lons = unwrap_longitudes([track['lon'] for track in fixes])
        xs, ys = to_web_mercator(lats, lons)
    except (TypeError, ValueError) as e:
        log.error(f"Error preparing geometry: {e}")
        return

    timestamps = [pd.to_datetime(track['timestamp']) if track.get('timestamp') else None
                  for track in fixes]
    breaks = gap_indices(timestamps, positions=list(zip(lats, lons)), gap_seconds=gap_seconds)
    if breaks:
        log.debug(f"Breaking the route at {len(breaks)} coverage gap(s)")

    bounds = (xs.min(), ys.min(), xs.max(), ys.max())
    ratio = resolve_aspect(aspect, orientation, bounds)
    provider, credit = resolve_basemap(background)

    route = _route_phrase(flight_number, origin, destination, flight_id)
    headline = headline or f"Flight path of {route}"

    marks = endpoint_marks(fixes, origin=origin, destination=destination,
                           in_progress=in_progress)

    # The track outranks the summary. Flightradar24 doesn't close a record out
    # the moment the wheels touch, so a flight that has plainly landed can still
    # report itself as flying, and the dek would then contradict its own map.
    still_flying = bool(in_progress) and marks[-1][2]

    if dek is None:
        dek = _default_dek([timestamp for timestamp in timestamps if timestamp is not None],
                           in_progress=still_flying)

    custom_source = source is not None
    if source is None:
        source = f"Source: Flightradar24; basemap by {credit}"

    fig, width, height = _figure(ratio)
    top, bottom, source_text = _draw_chrome(fig, width, height, headline, dek, source)
    ax = _add_axes(fig, width, height, top, bottom)

    ax.plot(insert_breaks(xs, breaks), insert_breaks(ys, breaks), color=COLOR_ROUTE,
            linewidth=2, solid_capstyle='round', solid_joinstyle='round', zorder=3)

    # Fit the extent to the axes, not the other way round, so the saved image
    # keeps the requested ratio without cropping or letterboxing.
    axes_ratio = (width - 2 * PAD) / (top - bottom)
    xmin, xmax, ymin, ymax = _fit_extent(bounds, axes_ratio, pad_factor)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_aspect('equal')

    drawn_credit = _add_basemap(ax, provider, credit, zoom, log)
    log.debug(f"Basemap drawn: {drawn_credit or 'none'}")

    # Never credit a basemap that isn't on the finished graphic.
    if not custom_source and source_text is not None and drawn_credit != credit:
        source_text.set_text(
            f"Source: Flightradar24; basemap by {drawn_credit}" if drawn_credit
            else "Source: Flightradar24"
        )

    if endpoints:
        _draw_endpoints(ax, xs, ys, marks)

    _frame_panel(ax)

    _save_figure(fig, fig_filename, formats, dpi, log, label='Map')
    plt.close(fig)
