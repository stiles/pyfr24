"""Plotting helpers for flight track data.

All map and chart rendering lives here so the API client stays focused on
talking to Flightradar24.

Graphics are laid out on a points grid where one point equals one pixel of the
design, then scaled up at save time. Type sizes therefore match a style guide
written in pixels, and the saved image keeps the requested aspect ratio exactly.
"""

import logging
import os
import re

import contextily as ctx
import contextily.tile
import geopandas as gpd
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
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

# Layout constants, in points. The board width is the CMS maximum.
BOARD_WIDTH = 780
PAD = 14
GAP_HEADLINE_TO_DEK = 30
GAP_DEK_TO_PLOT = 25
GAP_PLOT_TO_SOURCE = 8
LINE_HEIGHT = 1.25

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
    })


configure_style()


def format_ap_date(value):
    """Format a date AP style, e.g. 'Aug. 28, 2026'."""
    return f"{AP_MONTHS[value.month]} {value.day}, {value.year}"


def _format_duration(start, end):
    """Return a duration like '2 hr 51 min', or None if it isn't meaningful."""
    minutes = int(round((end - start).total_seconds() / 60))
    if minutes <= 0:
        return None
    hours, minutes = divmod(minutes, 60)
    if hours and minutes:
        return f"{hours} hr {minutes} min"
    if hours:
        return f"{hours} hr"
    return f"{minutes} min"


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


def _add_basemap(ax, provider, credit, zoom, log):
    """Draw the basemap, retrying with the default when the tiles fail.

    Tile servers fail at request time, not when the provider is built, so a bad
    style ID or a revoked token only surfaces here. Returns the credit for the
    basemap actually drawn, or None when the map is left bare.
    """
    # reset_extent must stay True: when False, contextily widens the axes to
    # the tile boundary and the fitted aspect ratio is lost.
    kwargs = {'reset_extent': True, 'attribution': False}
    if zoom is not None:
        kwargs['zoom'] = zoom

    xlim, ylim = ax.get_xlim(), ax.get_ylim()

    try:
        ctx.add_basemap(ax, source=provider, **kwargs)
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
        ctx.add_basemap(ax, source=fallback, **kwargs)
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
    """Pull (timestamp, value) pairs out of track points, dropping bad rows."""
    minimum, maximum = value_limits
    timestamps = []
    values = []

    for i, track in enumerate(tracks):
        try:
            if track.get('timestamp') is None:
                log.debug(f"Skipping track {i}: missing timestamp")
                continue

            raw = track.get(value_key)
            # Missing readings sit on the ground at either end of a track.
            value = 0.0 if raw is None else float(raw)

            if value < minimum or value > maximum:
                log.debug(f"Skipping track {i}: {value_key} out of range ({value})")
                continue

            timestamps.append(pd.to_datetime(track['timestamp']))
            values.append(value)
        except (ValueError, TypeError) as e:
            log.debug(f"Skipping track {i}: error processing data - {e}")
            continue

    return timestamps, values


def _route_phrase(flight_number, origin, destination, flight_id):
    """Describe the flight for a headline."""
    if flight_number and origin and destination:
        return f"{flight_number} from {origin} to {destination}"
    if flight_number:
        return str(flight_number)
    return f"flight {flight_id}"


def _default_dek(timestamps):
    """Date and tracked duration, as available."""
    if not timestamps:
        return None
    parts = [format_ap_date(timestamps[0])]
    if len(timestamps) > 1 and (duration := _format_duration(timestamps[0], timestamps[-1])):
        parts.append(f"{duration} tracked")
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
    ceiling = max(values) if values else 1

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
    dpi=200,
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
    """
    log = log or logger

    timestamps, values = _extract_series(tracks, value_key, value_limits, log)
    if not timestamps:
        log.warning(f"No valid {value_key} data available for plotting")
        return

    log.debug(f"Creating {value_key} chart with {len(timestamps)} points")

    route = _route_phrase(flight_number, origin, destination, flight_id)
    headline = headline or f"{metric_label} of {route}"
    dek = dek if dek is not None else _default_dek(timestamps)

    if source is None:
        source = "Source: Flightradar24"
        if tz_label := _timezone_label(timestamps, timezone):
            source = f"{source}. Times in {tz_label}."

    fig, width, height = _figure(resolve_aspect(aspect))
    top, bottom, _ = _draw_chrome(fig, width, height, headline, dek, source)

    # Room for the x tick labels between the plot and the source line.
    bottom += SIZE_AXIS * 1.8
    left = PAD + SIZE_AXIS * 5
    ax = _add_axes(fig, width, height, top, bottom, left=left, right=PAD)

    ax.plot(timestamps, values, color=COLOR_ROUTE, linewidth=2)

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

    fig.savefig(output_file, dpi=dpi)
    plt.close(fig)
    log.info(f"{metric_label} chart saved to {output_file}")


def plot_speed_chart(tracks, flight_id, output_file, flight_number=None, origin=None,
                     destination=None, timezone=None, aspect=None, dpi=200, log=None):
    """Create a line chart of ground speed over time."""
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
        dpi=dpi,
        log=log,
    )


def plot_altitude_chart(tracks, flight_id, output_file, flight_number=None, origin=None,
                        destination=None, timezone=None, aspect=None, dpi=200, log=None):
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
        log=log,
    )


def plot_flight_map(sorted_tracks, flight_id, fig_filename=None, orientation=None,
                    aspect=None, pad_factor=0.12, zoom=None, background=DEFAULT_BASEMAP,
                    flight_number=None, origin=None, destination=None, timezone=None,
                    headline=None, dek=None, source=None, dpi=200, log=None):
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
    """
    log = log or logger
    log.debug(f"Starting plot_flight_map with {len(sorted_tracks)} track points")

    df = pd.DataFrame(sorted_tracks)
    if df.empty:
        log.warning("No data available to plot.")
        return

    try:
        gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs="EPSG:4326")
        gdf_plot = gdf.to_crs(epsg=3857)
    except Exception as e:
        log.error(f"Error preparing geometry: {e}")
        return

    bounds = gdf_plot.total_bounds
    ratio = resolve_aspect(aspect, orientation, bounds)
    provider, credit = resolve_basemap(background)

    route = _route_phrase(flight_number, origin, destination, flight_id)
    headline = headline or f"Flight path of {route}"

    if dek is None:
        timestamps = [pd.to_datetime(t['timestamp']) for t in sorted_tracks if t.get('timestamp')]
        dek = _default_dek(timestamps)

    custom_source = source is not None
    if source is None:
        source = f"Source: Flightradar24; basemap by {credit}"

    fig, width, height = _figure(ratio)
    top, bottom, source_text = _draw_chrome(fig, width, height, headline, dek, source)
    ax = _add_axes(fig, width, height, top, bottom)

    ax.plot(gdf_plot.geometry.x, gdf_plot.geometry.y, color=COLOR_ROUTE, linewidth=2,
            solid_capstyle='round', solid_joinstyle='round', zorder=3)

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

    ax.set_axis_off()

    if fig_filename:
        try:
            if directory := os.path.dirname(fig_filename):
                os.makedirs(directory, exist_ok=True)
            fig.savefig(fig_filename, dpi=dpi)
            log.info(f"Map saved to {fig_filename}")
        except Exception as e:
            log.error(f"Error saving map: {e}")

    plt.close(fig)
