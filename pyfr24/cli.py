#!/usr/bin/env python3
"""
Command-line interface for the Flightradar24 API client.
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from . import FR24API, configure_logging

def setup_logging(args):
    """Configure logging based on command-line arguments."""
    level = getattr(logging, args.log_level.upper())
    configure_logging(level=level, log_file=args.log_file)
    return logging.getLogger(__name__)

def get_client(args):
    """Get an API client instance."""
    # Try to get token from command line argument first
    token = args.token
    
    # If not provided, try environment variable
    if not token:
        token = os.environ.get("FLIGHTRADAR_API_KEY")
    
    # If still not found, prompt user
    if not token:
        token = input("Please enter your Flightradar24 API token: ")
    
    if not token:
        raise ValueError("No API token provided. Please set FLIGHTRADAR_API_KEY environment variable or use --token option.")
    
    return FR24API(token)

def format_json(data):
    """Format JSON data for display."""
    return json.dumps(data, indent=2)

def _convert_timestamp(ts_str, tz_str):
    """Convert a timestamp string to a different timezone."""
    if not tz_str or not ts_str or 'N/A' in ts_str:
        return ts_str
    try:
        target_tz = ZoneInfo(tz_str)
        dt_obj = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        local_dt = dt_obj.astimezone(target_tz)
        return local_dt.isoformat()
    except (ZoneInfoNotFoundError, ValueError) as e:
        # Log this error or handle it as needed
        return ts_str

def _format_readable_timestamp(iso_str, tz_str=None):
    """Formats an ISO timestamp string into a human-readable format."""
    if not iso_str or 'N/A' in iso_str:
        return "N/A"
    try:
        dt_obj = datetime.fromisoformat(iso_str)

        # Get timezone abbreviation, with special handling for common US timezones
        tz_name = dt_obj.tzname()
        if tz_str:
            if 'America/New_York' in tz_str:
                tz_name = 'ET'
            elif 'America/Chicago' in tz_str:
                tz_name = 'CT'
            elif 'America/Denver' in tz_str:
                tz_name = 'MT'
            elif 'America/Los_Angeles' in tz_str:
                tz_name = 'PT'

        # Format time with a.m./p.m.
        hour = int(dt_obj.strftime('%I'))
        minute = dt_obj.strftime('%M')
        period = dt_obj.strftime('%p').lower().replace('am', 'a.m.').replace('pm', 'p.m.')
        time_str = f"{hour}:{minute} {period}"

        # Format final string: "August 2, 2025, at 10:55 a.m. ET"
        return f"{dt_obj.strftime('%B')} {dt_obj.day}, {dt_obj.year}, at {time_str} {tz_name}"

    except (ValueError, TypeError):
        return iso_str



def flight_summary_command(args):
    """Handle the flight summary command."""
    logger = setup_logging(args)
    api = get_client(args)
    
    try:
        # Convert date strings to ISO format if they don't include time
        from_date = args.from_date
        to_date = args.to_date
        
        if len(from_date) == 10:  # YYYY-MM-DD format
            from_date = f"{from_date}T00:00:00Z"
        if len(to_date) == 10:  # YYYY-MM-DD format
            to_date = f"{to_date}T23:59:59Z"
        
        if args.full:
            result = api.get_flight_summary_full(
                flights=args.flight,
                flight_datetime_from=from_date,
                flight_datetime_to=to_date
            )
        else:
            result = api.get_flight_summary_light(
                flights=args.flight,
                flight_datetime_from=from_date,
                flight_datetime_to=to_date
            )
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"Results saved to {args.output}")
        else:
            print(format_json(result))
    except Exception as e:
        logger.error(f"Error fetching flight summary: {e}")
        print(f"Error: {e}")
        sys.exit(1)

def live_flights_command(args):
    """Handle the live flights command."""
    logger = setup_logging(args)
    api = get_client(args)
    
    try:
        result = api.get_live_flights_by_registration(args.registration)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"Results saved to {args.output}")
        else:
            print(format_json(result))
    except Exception as e:
        logger.error(f"Error fetching live flights: {e}")
        print(f"Error: {e}")
        sys.exit(1)

def flight_tracks_command(args):
    """Handle the flight tracks command."""
    logger = setup_logging(args)
    api = get_client(args)
    
    try:
        result = api.get_flight_tracks(args.flight_id)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"Results saved to {args.output}")
        else:
            print(format_json(result))
    except Exception as e:
        logger.error(f"Error fetching flight tracks: {e}")
        print(f"Error: {e}")
        sys.exit(1)

def export_flight_command(args):
    """Export flight data to CSV, GeoJSON, KML and plot."""
    logger = setup_logging(args)
    api = get_client(args)
    try:
        output_dir = api.export_flight_data(
            args.flight_id, 
            output_dir=args.output_dir,
            background=args.background,
            orientation=args.orientation,
            timezone=args.timezone
        )
        print(f"Flight data exported to directory: {output_dir}")
        print("Files created:")
        print("  - data.csv: CSV of flight track points")
        print("  - points.geojson: GeoJSON of track points")
        print("  - line.geojson: GeoJSON LineString connecting the points")
        print("  - track.kml: Flight path in KML format")
        print("  - map.png: Map visualization of the flight path")
        print("  - speed.png: Line chart of speed over time")
        print("  - altitude.png: Line chart of altitude over time")
    except Exception as e:
        logger.error(f"Error exporting flight data: {e}")
        print(f"Error: {e}")
        sys.exit(1)

def airline_info_command(args):
    """Handle the airline info command."""
    logger = setup_logging(args)
    api = get_client(args)
    
    try:
        result = api.get_airline_light(args.icao)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"Results saved to {args.output}")
        else:
            print(format_json(result))
    except Exception as e:
        logger.error(f"Error fetching airline info: {e}")
        print(f"Error: {e}")
        sys.exit(1)

def airport_info_command(args):
    """Handle the airport info command."""
    logger = setup_logging(args)
    api = get_client(args)
    
    try:
        result = api.get_airport_full(args.code)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"Results saved to {args.output}")
        else:
            print(format_json(result))
    except Exception as e:
        logger.error(f"Error fetching airport info: {e}")
        print(f"Error: {e}")
        sys.exit(1)

def flight_positions_command(args):
    """Handle the flight positions command."""
    logger = setup_logging(args)
    api = get_client(args)
    
    try:
        result = api.get_flight_positions_light(args.bounds)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"Results saved to {args.output}")
        else:
            print(format_json(result))
    except Exception as e:
        logger.error(f"Error fetching flight positions: {e}")
        print(f"Error: {e}")
        sys.exit(1)

def flight_ids_command(args):
    """Handle the flight IDs command."""
    logger = setup_logging(args)
    api = get_client(args)
    
    try:
        # Convert date strings to ISO format if they don't include time
        from_date = args.from_date
        to_date = args.to_date
        
        if len(from_date) == 10:  # YYYY-MM-DD format
            from_date = f"{from_date}T00:00:00Z"
        if len(to_date) == 10:  # YYYY-MM-DD format
            to_date = f"{to_date}T23:59:59Z"
        
        flight_ids = api.get_flight_ids_by_registration(
            args.registration,
            from_date,
            to_date
        )
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(flight_ids, f, indent=2)
            print(f"Flight IDs saved to {args.output}")
        else:
            print(format_json(flight_ids))
    except Exception as e:
        logger.error(f"Error fetching flight IDs: {e}")
        print(f"Error: {e}")
        sys.exit(1)

def smart_export_flight_command(args):
    logger = setup_logging(args)
    api = get_client(args)
    try:
        print("Fetching summary...")
                    # Call smart_export_flight with auto_select if provided
        result = api.smart_export_flight(
            flight_number=args.flight,
            date=args.date,
            output_dir=args.output_dir,
            background=args.background,
            orientation=args.orientation,
            auto_select=args.auto_select,
            timezone=args.timezone,
        )
        options = result.get('options', [])
        selected = result.get('selected')
        output_dir = result.get('output_dir')
        error = result.get('error')
        # If multiple matches and no auto_select, prompt user
        if not selected and options:
            print(f"Multiple flights found for {args.flight} on {args.date}:")
            for idx, opt in enumerate(options):
                orig = opt.get('orig_icao') or opt.get('origin') or 'ORIG'
                dest = opt.get('dest_icao_actual') or opt.get('dest_icao') or opt.get('destination') or 'DEST'
                dep = opt.get('datetime_takeoff') or opt.get('first_seen') or 'N/A'
                arr = opt.get('datetime_landed') or opt.get('last_seen') or 'N/A'
                reg = opt.get('reg') or opt.get('registration') or 'N/A'
                typ = opt.get('type') or 'N/A'
                fid = opt.get('fr24_id') or opt.get('id') or 'N/A'
                print(f"[{idx}] {fid} | {orig}  {dest} | {dep[:16]}–{arr[:16]} | {reg} | {typ}")
            # Prompt user
            while True:
                try:
                    sel = input(f"Select a flight to export [0-{len(options)-1}]: ")
                    sel = int(sel)
                    if 0 <= sel < len(options):
                        break
                    else:
                        print("Invalid selection. Try again.")
                except Exception:
                    print("Invalid input. Enter a number.")
            print("Fetching tracks and exporting files...")
            # Call again with auto_select=sel
            result = api.smart_export_flight(
                flight_number=args.flight,
                date=args.date,
                output_dir=args.output_dir,
                background=args.background,
                orientation=args.orientation,
                auto_select=sel,
                timezone=args.timezone,
                labels=args.labels,
            )
            selected = result.get('selected')
            output_dir = result.get('output_dir')
        if selected and output_dir:
            print("Exporting files...")
            orig = selected.get('orig_icao') or selected.get('origin') or 'ORIG'
            dest = selected.get('dest_icao_actual') or selected.get('dest_icao') or selected.get('destination') or 'DEST'
            dep_utc = selected.get('datetime_takeoff') or selected.get('first_seen') or 'N/A'
            arr_utc = selected.get('datetime_landed') or selected.get('last_seen') or 'N/A'
            dep_iso = _convert_timestamp(dep_utc, args.timezone)
            arr_iso = _convert_timestamp(arr_utc, args.timezone)
            dep_readable = _format_readable_timestamp(dep_iso, args.timezone)
            arr_readable = _format_readable_timestamp(arr_iso, args.timezone)
            reg = selected.get('reg') or selected.get('registration') or 'N/A'
            typ = selected.get('type') or 'N/A'
            fid = selected.get('fr24_id') or selected.get('id') or 'N/A'
            # Write toplines.json
            toplines = {
                "flight_number": args.flight,
                "flight_id": fid,
                "date": args.date,
                "origin": orig,
                "destination": dest,
                "departure_time": dep_iso,
                "arrival_time": arr_iso,
                "departure_time_readable": dep_readable,
                "arrival_time_readable": arr_readable,
                "registration": reg,
                "aircraft_type": typ
            }
            import os
            toplines_path = os.path.join(output_dir, "toplines.json")
            with open(toplines_path, "w") as f:
                json.dump(toplines, f, indent=2)
            print(f"\nExporting flight {fid} ({args.flight}) from {orig} to {dest} on {dep_iso[:16]}–{arr_iso[:16]}")
            print(f"Output directory: {output_dir}")
            print("Files created:")
            print("  - data.csv: CSV of flight track points")
            print("  - points.geojson: GeoJSON of track points")
            print("  - line.geojson: GeoJSON LineString connecting the points")
            print("  - track.kml: Flight path in KML format")
            print("  - map.png: Map visualization of the flight path")
            print("  - speed.png: Line chart of speed over time")
            print("  - altitude.png: Line chart of altitude over time")
            print("  - toplines.json: Topline summary of the exported flight")
            print("\nExport complete!")
        elif error:
            print(f"Error: {error}")
        else:
            print("Unknown error or no flights found.")
    except Exception as e:
        logger.error(f"Error in smart export: {e}")
        print(f"Error: {e}")
        sys.exit(1)

def create_parser():
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Flightradar24 API client command-line interface",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Global arguments
    parser.add_argument("-t", "--token", help="API token (can also be set via FLIGHTRADAR_API_KEY env var)")
    parser.add_argument("-l", "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Logging level")
    parser.add_argument("-f", "--log-file", help="Log file path")
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Flight summary command
    flight_summary_parser = subparsers.add_parser("flight-summary", help="Get flight summary information")
    flight_summary_parser.add_argument("-F", "--flight", required=True, help="Flight number or callsign")
    flight_summary_parser.add_argument("-f", "--from-date", required=True, help="Start date/time (YYYY-MM-DD)")
    flight_summary_parser.add_argument("-t", "--to-date", required=True, help="End date/time (YYYY-MM-DD)")
    flight_summary_parser.add_argument("--full", action="store_true", help="Get full summary instead of light")
    flight_summary_parser.add_argument("-o", "--output", help="Output file path (JSON)")
    flight_summary_parser.set_defaults(func=flight_summary_command)
    
    # Live flights command
    live_flights_parser = subparsers.add_parser("live-flights", help="Get live flights by aircraft registration")
    live_flights_parser.add_argument("-R", "--registration", required=True, help="Aircraft registration (e.g., N12345)")
    live_flights_parser.add_argument("-o", "--output", help="Output file path (JSON)")
    live_flights_parser.set_defaults(func=live_flights_command)
    
    # Flight tracks command
    flight_tracks_parser = subparsers.add_parser("flight-tracks", help="Get detailed flight track data")
    flight_tracks_parser.add_argument("-i", "--flight-id", required=True, help="Flight ID (e.g., 39a84c3c)")
    flight_tracks_parser.add_argument("-o", "--output", help="Output file path (JSON)")
    flight_tracks_parser.set_defaults(func=flight_tracks_command)
    
    # Export flight command
    export_flight_parser = subparsers.add_parser("export-flight", help="Export flight data to CSV, GeoJSON, KML and plot")
    export_flight_parser.add_argument("-i", "--flight-id", required=True, help="Flight ID")
    export_flight_parser.add_argument("-o", "--output-dir", help="Output directory path")
    export_flight_parser.add_argument("--background", 
                                      choices=['carto-light', 'carto-dark', 'osm', 'esri-topo', 'esri-satellite'], 
                                      default='carto-light', 
                                      help="Map background. 'carto-light' (default), 'carto-dark', 'osm', 'esri-topo', 'esri-satellite'")
    export_flight_parser.add_argument("--orientation", choices=['horizontal', 'vertical', 'auto'], default='horizontal', help="Map orientation (16:9, 9:16, or auto-detect)")

    export_flight_parser.add_argument("--timezone", help="Convert UTC timestamps to a specific timezone (e.g., 'America/New_York')")
    export_flight_parser.set_defaults(func=export_flight_command)
    
    # Airline info command
    airline_info_parser = subparsers.add_parser("airline-info", help="Get airline information")
    airline_info_parser.add_argument("-i", "--icao", required=True, help="Airline ICAO code (e.g., AAL)")
    airline_info_parser.add_argument("-o", "--output", help="Output file path (JSON)")
    airline_info_parser.set_defaults(func=airline_info_command)
    
    # Airport info command
    airport_info_parser = subparsers.add_parser("airport-info", help="Get airport information")
    airport_info_parser.add_argument("-c", "--code", required=True, help="Airport IATA or ICAO code (e.g., JFK)")
    airport_info_parser.add_argument("-o", "--output", help="Output file path (JSON)")
    airport_info_parser.set_defaults(func=airport_info_command)
    
    # Flight positions command
    flight_positions_parser = subparsers.add_parser("flight-positions", help="Get flight positions within bounds")
    flight_positions_parser.add_argument("-b", "--bounds", required=True, 
                                       help="Bounding box coordinates (lat1,lon1,lat2,lon2)")
    flight_positions_parser.add_argument("-o", "--output", help="Output file path (JSON)")
    flight_positions_parser.set_defaults(func=flight_positions_command)
    
    # Flight IDs command
    flight_ids_parser = subparsers.add_parser("flight-ids", help="Get flight IDs for an aircraft registration")
    flight_ids_parser.add_argument("-R", "--registration", required=True, help="Aircraft registration (e.g., N12345)")
    flight_ids_parser.add_argument("-f", "--from-date", required=True, help="Start date (YYYY-MM-DD)")
    flight_ids_parser.add_argument("-t", "--to-date", required=True, help="End date (YYYY-MM-DD)")
    flight_ids_parser.add_argument("-o", "--output", help="Output file path (JSON)")
    flight_ids_parser.set_defaults(func=flight_ids_command)
    
    # Smart export command
    smart_export_parser = subparsers.add_parser("smart-export", help="Smart export by flight number and date with interactive selection")
    smart_export_parser.add_argument("-F", "--flight", required=True, help="Flight number or callsign")
    smart_export_parser.add_argument("-d", "--date", required=True, help="Date (YYYY-MM-DD)")
    smart_export_parser.add_argument("-o", "--output-dir", help="Output directory path")
    smart_export_parser.add_argument("--background", 
                                     choices=['carto-light', 'carto-dark', 'osm', 'esri-topo', 'esri-satellite'], 
                                     default='carto-light', 
                                     help="Map background. 'carto-light' (default), 'carto-dark', 'osm', 'esri-topo', 'esri-satellite'")
    smart_export_parser.add_argument("--orientation", choices=['horizontal', 'vertical', 'auto'], default='horizontal', help="Map orientation (16:9, 9:16, or auto-detect)")

    smart_export_parser.add_argument("--auto-select", help="Auto-select: 'latest', 'earliest', or index (for scripting)")
    smart_export_parser.add_argument("--timezone", help="Convert UTC timestamps to a specific timezone (e.g., 'America/New_York')")
    smart_export_parser.set_defaults(func=smart_export_flight_command)
    
    return parser

def main():
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)

if __name__ == "__main__":
    main()
