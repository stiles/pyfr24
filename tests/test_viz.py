"""
Tests for the graphics helpers, which need no live API to exercise.

The failures these guard against all reached finished graphics: a Tokyo to Los
Angeles route drawn the long way around the world (issue #2), a line ruled
straight through six hours of missing ADS-B coverage (issue #3), a flight still
at 39,000 feet over Pennsylvania labeled as arrived at JFK, and a single bad
ping that dropped a cruising 787 to 30 knots.
"""

import datetime
import os
import tempfile
import unittest
from unittest import mock

import matplotlib

matplotlib.use('Agg')

import matplotlib.colors
import matplotlib.pyplot
import numpy as np

from pyfr24 import viz

START = datetime.datetime(2025, 11, 2, 13, 0, tzinfo=datetime.timezone.utc)


def at(minutes):
    """A timestamp this many minutes into the flight."""
    return START + datetime.timedelta(minutes=minutes)


def fix(minutes, lat, lon, alt=35000, gspeed=480, track=None, source='ADSB'):
    """One track point, shaped like the API's."""
    return {
        'timestamp': at(minutes).isoformat(),
        'lat': lat,
        'lon': lon,
        'alt': alt,
        'gspeed': gspeed,
        'track': track,
        'source': source,
    }


class TestFormatDuration(unittest.TestCase):
    """Deks read as sentences, so durations are spelled out, not abbreviated."""

    def test_hours_and_minutes(self):
        self.assertEqual(viz._format_duration(at(0), at(171)), '2 hours, 51 minutes')

    def test_singulars_stay_singular(self):
        self.assertEqual(viz._format_duration(at(0), at(61)), '1 hour, 1 minute')

    def test_whole_hours_drop_the_minutes(self):
        self.assertEqual(viz._format_duration(at(0), at(180)), '3 hours')

    def test_under_an_hour_drops_the_hours(self):
        self.assertEqual(viz._format_duration(at(0), at(47)), '47 minutes')

    def test_nothing_tracked_has_no_duration(self):
        """A single ping is not a duration, and shouldn't read as '0 minutes'."""
        self.assertIsNone(viz._format_duration(at(0), at(0)))


class TestUnwrapLongitudes(unittest.TestCase):
    """A track that crosses the antimeridian has to stay one continuous path."""

    def test_a_pacific_crossing_runs_past_180(self):
        """Tokyo to Los Angeles heads east; the longitudes must too."""
        unwrapped = viz.unwrap_longitudes([170.0, 179.0, -179.0, -170.0])

        self.assertEqual(unwrapped, [170.0, 179.0, 181.0, 190.0])

    def test_no_step_jumps_the_world(self):
        """The defect was a single segment spanning most of the globe."""
        unwrapped = viz.unwrap_longitudes([139.0, 160.0, 178.0, -170.0, -140.0, -118.0])
        steps = [abs(b - a) for a, b in zip(unwrapped, unwrapped[1:])]

        self.assertTrue(all(step < 180 for step in steps), steps)

    def test_a_domestic_route_is_left_alone(self):
        lons = [-118.35, -115.0, -105.2, -97.04]

        self.assertEqual(viz.unwrap_longitudes(lons), lons)

    def test_a_westbound_crossing_runs_below_negative_180(self):
        """The same path flown the other way unwraps the other way."""
        self.assertEqual(viz.unwrap_longitudes([-170.0, -179.0, 179.0]),
                         [-170.0, -179.0, -181.0])


class TestWebMercator(unittest.TestCase):
    """Projected by hand, because a CRS transform folds longitude back in."""

    def test_the_prime_meridian_is_the_origin(self):
        xs, ys = viz.to_web_mercator([0.0], [0.0])

        self.assertAlmostEqual(xs[0], 0.0)
        self.assertAlmostEqual(ys[0], 0.0)

    def test_the_antimeridian_lands_on_the_world_edge(self):
        xs, _ = viz.to_web_mercator([0.0], [180.0])

        self.assertAlmostEqual(xs[0], viz.WORLD_HALF_WIDTH, places=3)

    def test_an_unwrapped_longitude_keeps_going(self):
        """The whole point: 200 degrees east is past the edge, not back at -160."""
        xs, _ = viz.to_web_mercator([0.0], [200.0])

        self.assertGreater(xs[0], viz.WORLD_HALF_WIDTH)

    def test_latitude_round_trips(self):
        _, ys = viz.to_web_mercator([34.05], [0.0])

        self.assertAlmostEqual(viz._mercator_to_latitude(ys[0]), 34.05, places=6)

    def test_the_poles_are_clamped(self):
        """Web Mercator sends 90 degrees to infinity."""
        _, ys = viz.to_web_mercator([90.0, -90.0], [0.0, 0.0])

        self.assertTrue(np.all(np.isfinite(ys)))


class TestWorldCopies(unittest.TestCase):
    """Tile servers publish one world, so a wider extent is fetched in pieces."""

    def test_an_ordinary_extent_is_one_piece(self):
        copies = list(viz._world_copies(-1e6, 1e6))

        self.assertEqual(copies, [(-1e6, 1e6, 0)])

    def test_crossing_the_antimeridian_splits_in_two(self):
        copies = list(viz._world_copies(1.4e7, 2.8e7))

        self.assertEqual(len(copies), 2)
        self.assertEqual(copies[0][1], viz.WORLD_HALF_WIDTH)
        self.assertEqual(copies[1][0], viz.WORLD_HALF_WIDTH)

    def test_every_piece_lands_inside_the_published_world(self):
        """Each piece is requested at its shifted position, which must be valid."""
        for left, right, shift in viz._world_copies(1.4e7, 2.8e7):
            self.assertGreaterEqual(left - shift, -viz.WORLD_HALF_WIDTH - 1)
            self.assertLessEqual(right - shift, viz.WORLD_HALF_WIDTH + 1)

    def test_the_pieces_cover_the_whole_extent(self):
        copies = list(viz._world_copies(1.4e7, 2.8e7))

        self.assertEqual(copies[0][0], 1.4e7)
        self.assertEqual(copies[-1][1], 2.8e7)


class TestGapDetection(unittest.TestCase):
    """A hole in coverage is not a straight line the aircraft flew."""

    def test_a_long_gap_over_ground_covered_breaks(self):
        timestamps = [at(0), at(1), at(400), at(401)]
        positions = [(35.5, 139.8), (35.6, 140.2), (34.0, -130.0), (33.9, -129.5)]

        self.assertEqual(viz.gap_indices(timestamps, positions), {1})

    def test_a_parked_aircraft_does_not_break(self):
        """Twenty minutes between pings at the same gate is one line, not three."""
        timestamps = [at(0), at(21), at(25)]
        positions = [(34.2, -118.35)] * 3

        self.assertEqual(viz.gap_indices(timestamps, positions), set())

    def test_normal_cadence_does_not_break(self):
        timestamps = [at(i / 2) for i in range(20)]
        positions = [(34.0 + i / 100, -118.0 + i / 10) for i in range(20)]

        self.assertEqual(viz.gap_indices(timestamps, positions), set())

    def test_an_explicit_threshold_wins(self):
        timestamps = [at(0), at(2), at(4)]
        positions = [(34.0, -118.0), (34.5, -117.0), (35.0, -116.0)]

        self.assertEqual(viz.gap_indices(timestamps, positions, gap_seconds=60), {0, 1})

    def test_missing_timestamps_are_skipped(self):
        self.assertEqual(viz.gap_indices([at(0), None, at(400)]), set())

    def test_one_point_cannot_have_a_gap(self):
        self.assertEqual(viz.gap_indices([at(0)]), set())


class TestGapThreshold(unittest.TestCase):
    """The threshold scales with each track, since cadence varies by region."""

    def test_a_dense_track_gets_the_floor(self):
        """Twelve times a seven-second cadence is under a minute, which is noise."""
        timestamps = [at(i * 7 / 60) for i in range(30)]

        self.assertEqual(viz.gap_threshold_seconds(timestamps), viz.GAP_FLOOR_SECONDS)

    def test_a_sparse_track_scales_up(self):
        timestamps = [at(i * 2) for i in range(10)]

        self.assertEqual(viz.gap_threshold_seconds(timestamps),
                         viz.GAP_CADENCE_MULTIPLE * 120)

    def test_no_intervals_falls_back_to_the_floor(self):
        self.assertEqual(viz.gap_threshold_seconds([at(0)]), viz.GAP_FLOOR_SECONDS)


class TestInsertBreaks(unittest.TestCase):
    """matplotlib lifts the pen at a NaN, which is how a gap reads as a gap."""

    def test_a_nan_lands_after_each_break(self):
        broken = viz.insert_breaks([1.0, 2.0, 3.0], {0})

        self.assertEqual(len(broken), 4)
        self.assertTrue(np.isnan(broken[1]))
        self.assertEqual(list(broken[[0, 2, 3]]), [1.0, 2.0, 3.0])

    def test_no_breaks_leaves_the_series_alone(self):
        self.assertEqual(list(viz.insert_breaks([1.0, 2.0], set())), [1.0, 2.0])


class TestResolveFormats(unittest.TestCase):
    """A bad format should cost nothing, not fail the export at save time."""

    def test_nothing_asked_for_means_png(self):
        self.assertEqual(viz.resolve_formats(None), ('png',))

    def test_a_comma_separated_string_is_split(self):
        self.assertEqual(viz.resolve_formats('png,svg'), ('png', 'svg'))

    def test_duplicates_and_case_and_dots_are_normalized(self):
        self.assertEqual(viz.resolve_formats(['.SVG', 'svg', 'PNG']), ('svg', 'png'))

    def test_an_unknown_format_is_dropped(self):
        self.assertEqual(viz.resolve_formats('png,tiff'), ('png',))

    def test_only_unknown_formats_falls_back_to_png(self):
        self.assertEqual(viz.resolve_formats('tiff'), ('png',))


class TestExtractSeries(unittest.TestCase):
    """A missing reading is missing, not zero."""

    def test_a_missing_value_becomes_nan(self):
        """Substituting zero drew a cliff to sea level that never happened."""
        _, values, _ = viz._extract_series(
            [fix(0, 34.0, -118.0, alt=35000), fix(1, 34.1, -117.9, alt=None)],
            'alt', (0, 50000), viz.logger,
        )

        self.assertEqual(values[0], 35000)
        self.assertTrue(np.isnan(values[1]))

    def test_positions_come_back_alongside(self):
        """The caller needs them to tell lost coverage from a parked aircraft."""
        _, values, positions = viz._extract_series(
            [fix(0, 34.0, -118.0)], 'alt', (0, 50000), viz.logger,
        )

        self.assertEqual(len(positions), len(values))
        self.assertEqual(positions[0], (34.0, -118.0))

    def test_out_of_range_readings_are_dropped(self):
        _, values, _ = viz._extract_series(
            [fix(0, 34.0, -118.0, alt=35000), fix(1, 34.1, -117.9, alt=99000)],
            'alt', (0, 50000), viz.logger,
        )

        self.assertEqual(len(values), 1)

    def test_an_implausible_reading_goes_out_with_its_timestamp(self):
        """Left in, one bad ping drew a cliff to the floor of the chart."""
        tracks = [fix(0, 34.0, -118.0, gspeed=496),
                  fix(1, 34.1, -117.9, gspeed=30),
                  fix(2, 34.2, -117.8, gspeed=494)]

        timestamps, values, positions = viz._extract_series(
            tracks, 'gspeed', (0, 1000), viz.logger)

        self.assertEqual(values, [496.0, 494.0])
        self.assertEqual(len(timestamps), 2)
        self.assertEqual(len(positions), 2)


class TestImplausibleReadings(unittest.TestCase):
    """A reading that arrived is not the same as a reading that could be true."""

    LIMITS = viz.SPIKE_LIMITS['gspeed']

    def test_an_isolated_glitch_is_flagged(self):
        """NZ6 reported 30 knots at 35,000 feet between two readings near 500."""
        readings = [496.0, 495.0, 30.0, 494.0, 493.0]

        self.assertEqual(viz.implausible_indices(readings, self.LIMITS), {2})

    def test_a_glitch_upward_is_flagged_too(self):
        self.assertEqual(viz.implausible_indices([160.0, 950.0, 170.0], self.LIMITS), {1})

    def test_a_real_descent_survives(self):
        """Showing a drop like this is the point of the chart, not something to smooth."""
        readings = [35000.0, 30000.0, 24000.0, 17000.0, 9000.0, 2000.0]

        self.assertEqual(viz.implausible_indices(readings, viz.SPIKE_LIMITS['alt']), set())

    def test_plausible_variation_survives(self):
        """A 40-knot swing at cruise happens, and the filter has to leave it be."""
        self.assertEqual(viz.implausible_indices([489.0, 450.0, 491.0], self.LIMITS), set())

    def test_a_missing_reading_is_not_a_glitch(self):
        self.assertEqual(
            viz.implausible_indices([495.0, float('nan'), 494.0], self.LIMITS), set())

    def test_the_ends_are_never_flagged(self):
        """A first or last reading has nothing either side to judge it against."""
        self.assertEqual(
            viz.implausible_indices([30.0, 495.0, 494.0, 30.0], self.LIMITS), set())

    def test_a_field_with_no_limits_is_left_alone(self):
        self.assertEqual(viz.implausible_indices([496.0, 30.0, 494.0], None), set())


class TestMlatShare(unittest.TestCase):
    """Speeds derived from signal timing wobble, and the chart has to own that."""

    def test_an_adsb_track_has_no_mlat(self):
        self.assertEqual(viz.mlat_share([fix(0, 34.0, -118.0)]), 0.0)

    def test_the_share_counts_mlat_fixes(self):
        tracks = [fix(0, 34.0, -118.0, source='MLAT'), fix(1, 34.1, -117.9),
                  fix(2, 34.2, -117.8), fix(3, 34.3, -117.7)]

        self.assertEqual(viz.mlat_share(tracks), 0.25)

    def test_an_empty_track_has_no_share(self):
        self.assertEqual(viz.mlat_share([]), 0.0)


class TestEndpointMarks(unittest.TestCase):
    """An airport code at the end of a line is a claim the track has to support."""

    def test_a_track_that_reached_the_ground_gets_its_codes(self):
        fixes = [fix(0, 37.6, -122.4, alt=0), fix(317, 40.6, -73.8, alt=0)]

        marks = viz.endpoint_marks(fixes, origin='KSFO', destination='KJFK')

        self.assertEqual([(label, airborne) for _, label, airborne, _ in marks],
                         [('KSFO', False), ('KJFK', False)])

    def test_a_flight_still_flying_is_not_at_its_destination(self):
        """DL691 was at 39,000 feet over Pennsylvania, labeled KJFK."""
        fixes = [fix(0, 37.6, -122.4, alt=0), fix(317, 41.7, -77.3, alt=39000, track=120)]

        marks = viz.endpoint_marks(fixes, origin='KSFO', destination='KJFK', in_progress=True)

        self.assertEqual(marks[-1], (-1, 'In flight', True, 120.0))

    def test_a_track_that_runs_out_early_says_so(self):
        """Coverage often stops short of the runway, which is no arrival either."""
        fixes = [fix(0, 35.7, 139.8, alt=0), fix(600, 34.4, -118.9, alt=15900, track=95)]

        marks = viz.endpoint_marks(fixes, origin='RJTT', destination='KLAX')

        self.assertEqual(marks[-1][1], 'Last contact')

    def test_a_track_picked_up_in_the_air_says_so(self):
        fixes = [fix(0, 34.0, -118.0, alt=33000, track=95), fix(300, 40.6, -73.8, alt=0)]

        marks = viz.endpoint_marks(fixes, origin='KLAX', destination='KJFK')

        self.assertEqual([label for _, label, _, _ in marks], ['First contact', 'KJFK'])

    def test_a_missing_altitude_keeps_the_code(self):
        """With no altitude there's no reason to doubt the airport."""
        fixes = [fix(0, 34.0, -118.0, alt=None), fix(300, 40.6, -73.8, alt=None)]

        marks = viz.endpoint_marks(fixes, origin='KLAX', destination='KJFK')

        self.assertEqual([label for _, label, _, _ in marks], ['KLAX', 'KJFK'])


class TestScreenHeading(unittest.TestCase):
    """A fallback for the rare fix that doesn't report which way it was pointed."""

    def test_east_reads_as_ninety(self):
        heading = viz._screen_heading(np.array([0.0, 100.0]), np.array([0.0, 0.0]), -1)

        self.assertAlmostEqual(heading, 90.0)

    def test_north_reads_as_zero(self):
        heading = viz._screen_heading(np.array([0.0, 0.0]), np.array([0.0, 100.0]), -1)

        self.assertAlmostEqual(heading, 0.0)

    def test_the_start_looks_forward(self):
        """At the start the aircraft was heading toward the next fix, not the last."""
        heading = viz._screen_heading(np.array([0.0, 100.0, 200.0]),
                                      np.array([0.0, 0.0, 0.0]), 0)

        self.assertAlmostEqual(heading, 90.0)

    def test_a_stationary_pair_has_no_heading(self):
        self.assertIsNone(
            viz._screen_heading(np.array([5.0, 5.0]), np.array([5.0, 5.0]), -1))


class TestDefaultDek(unittest.TestCase):
    """A duration on its own reads as the length of a finished trip."""

    def test_a_finished_flight_reads_as_a_duration(self):
        self.assertEqual(viz._default_dek([at(0), at(171)]),
                         'Nov. 2, 2025 · 2 hours, 51 minutes tracked')

    def test_a_flight_still_flying_says_so(self):
        dek = viz._default_dek([at(0), at(171)], in_progress=True)

        self.assertTrue(dek.endswith('still in the air'), dek)


class TestBreakSeries(unittest.TestCase):
    """The chart line stops where coverage stopped, not at the last ping."""

    def test_the_break_sits_between_the_fixes(self):
        timestamps = [at(0), at(400)]
        xs, ys = viz._break_series(timestamps, [35000.0, 38000.0], {0})

        self.assertEqual(len(xs), 3)
        self.assertEqual(xs[1], at(200))
        self.assertTrue(np.isnan(ys[1]))


class TestFramePanel(unittest.TestCase):
    """Without a border the basemap bleeds into the page with nothing between."""

    def test_the_border_is_drawn_on_every_side(self):
        _, ax = matplotlib.pyplot.subplots()
        self.addCleanup(matplotlib.pyplot.close, 'all')

        viz._frame_panel(ax)

        self.assertEqual(len(ax.spines), 4)
        for spine in ax.spines.values():
            self.assertTrue(spine.get_visible())

    def test_the_border_matches_the_chart_gridlines(self):
        """A map and a chart of the same flight sit together on a page."""
        _, ax = matplotlib.pyplot.subplots()
        self.addCleanup(matplotlib.pyplot.close, 'all')

        viz._frame_panel(ax)

        expected = matplotlib.colors.to_rgba(viz.COLOR_GRID)
        for spine in ax.spines.values():
            self.assertEqual(matplotlib.colors.to_rgba(spine.get_edgecolor()), expected)

    def test_the_ticks_are_cleared(self):
        _, ax = matplotlib.pyplot.subplots()
        self.addCleanup(matplotlib.pyplot.close, 'all')

        viz._frame_panel(ax)

        self.assertEqual(list(ax.get_xticks()), [])
        self.assertEqual(list(ax.get_yticks()), [])


class TestRendering(unittest.TestCase):
    """End to end, with the tile fetch stubbed out so tests stay offline."""

    def setUp(self):
        self.tracks = [fix(i, 34.0 + i / 60, -118.35 + i / 4) for i in range(40)]
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)

    def path(self, name):
        return os.path.join(self.directory.name, name)

    def test_a_map_is_written_in_every_format(self):
        with mock.patch.object(viz, '_draw_tiles'):
            viz.plot_flight_map(self.tracks, '3cee33af', fig_filename=self.path('map.png'),
                                flight_number='AA26', origin='RJTT', destination='KLAX',
                                formats=('png', 'svg'))

        self.assertTrue(os.path.exists(self.path('map.png')))
        self.assertTrue(os.path.exists(self.path('map.svg')))

    def test_svg_type_stays_editable(self):
        """Outlined type can't be restyled or retyped in Illustrator."""
        with mock.patch.object(viz, '_draw_tiles'):
            viz.plot_flight_map(self.tracks, '3cee33af', fig_filename=self.path('map.svg'),
                                flight_number='AA26', origin='RJTT', destination='KLAX')

        with open(self.path('map.svg'), encoding='utf-8') as f:
            svg = f.read()

        self.assertIn('Flight path of AA26 from RJTT to KLAX', svg)

    def test_a_failed_basemap_still_leaves_a_map(self):
        """Tiles fail at request time, and a route on white beats no graphic."""
        with mock.patch.object(viz, '_draw_tiles', side_effect=OSError('no tiles')):
            viz.plot_flight_map(self.tracks, '3cee33af', fig_filename=self.path('map.png'))

        self.assertTrue(os.path.exists(self.path('map.png')))

    def test_charts_are_written_in_every_format(self):
        viz.plot_altitude_chart(self.tracks, '3cee33af', self.path('altitude.png'),
                                flight_number='AA26', formats=('png', 'svg'))

        self.assertTrue(os.path.exists(self.path('altitude.png')))
        self.assertTrue(os.path.exists(self.path('altitude.svg')))

    def test_a_chart_survives_missing_readings(self):
        """Every altitude NaN once meant a max() over NaN and an unreadable axis."""
        tracks = [fix(i, 34.0 + i / 60, -118.0 + i / 4, alt=None) for i in range(10)]

        viz.plot_altitude_chart(tracks, '3cee33af', self.path('altitude.png'))

        self.assertTrue(os.path.exists(self.path('altitude.png')))

    def test_a_flight_still_flying_is_not_labeled_as_arrived(self):
        """The end of the line is where the data stops, not where the aircraft lands."""
        tracks = [fix(i, 34.0 + i / 60, -118.35 + i / 4, alt=37000, track=95)
                  for i in range(40)]

        with mock.patch.object(viz, '_draw_tiles'), \
                mock.patch.object(viz, '_draw_endpoints') as draw_endpoints:
            viz.plot_flight_map(tracks, '4166af99', fig_filename=self.path('map.svg'),
                                flight_number='DL691', origin='KSFO', destination='KJFK',
                                in_progress=True)

        marks = draw_endpoints.call_args.args[-1]
        self.assertEqual([label for _, label, _, _ in marks], ['First contact', 'In flight'])

        with open(self.path('map.svg'), encoding='utf-8') as f:
            self.assertIn('still in the air', f.read())

    def test_a_landed_flight_ignores_a_stale_in_progress_flag(self):
        """FR24 doesn't close a record out the moment the wheels touch down."""
        tracks = [fix(i, 34.0 + i / 60, -118.35 + i / 4, alt=37000, track=95)
                  for i in range(39)]
        tracks.append(fix(39, 34.65, -108.85, alt=0, track=95))

        with mock.patch.object(viz, '_draw_tiles'):
            viz.plot_flight_map(tracks, '4166af99', fig_filename=self.path('map.svg'),
                                flight_number='DL691', origin='KSFO', destination='KJFK',
                                in_progress=True)

        with open(self.path('map.svg'), encoding='utf-8') as f:
            self.assertNotIn('still in the air', f.read())

    def test_an_mlat_track_says_its_speeds_are_estimated(self):
        tracks = [fix(i, 34.0 + i / 60, -118.35 + i / 4, source='MLAT') for i in range(40)]

        viz.plot_speed_chart(tracks, '3ced3afd', self.path('speed.svg'))

        with open(self.path('speed.svg'), encoding='utf-8') as f:
            svg = f.read()

        self.assertIn('estimated', svg)

    def test_an_adsb_track_makes_no_such_note(self):
        viz.plot_speed_chart(self.tracks, '3cee33af', self.path('speed.svg'))

        with open(self.path('speed.svg'), encoding='utf-8') as f:
            svg = f.read()

        self.assertNotIn('estimated', svg)

    def test_an_empty_track_writes_nothing(self):
        with mock.patch.object(viz, '_draw_tiles'):
            viz.plot_flight_map([], '3cee33af', fig_filename=self.path('map.png'))

        self.assertFalse(os.path.exists(self.path('map.png')))


if __name__ == '__main__':
    unittest.main()
