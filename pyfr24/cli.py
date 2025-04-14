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

def flight_summary_command(args):
    """Handle the flight summary command."""
    logger = setup_logging(args)
    api = get_client(args)
    
    try:
        if args.full:
            result = api.get_flight_summary_full(
                flights=args.flight,
                flight_datetime_from=args.from_date,
                flight_datetime_to=args.to_date
            )
        else:
            result = api.get_flight_summary_light(
                flights=args.flight,
                flight_datetime_from=args.from_date,
                flight_datetime_to=args.to_date
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
            orientation=args.orientation
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
        flight_ids = api.get_flight_ids_by_registration(
            args.registration,
            args.from_date,
            args.to_date
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
    export_flight_parser.add_argument("--background", choices=['carto', 'osm', 'stamen', 'esri'], default='carto', help="Map background provider")
    export_flight_parser.add_argument("--orientation", choices=['horizontal', 'vertical', 'auto'], default='horizontal', help="Map orientation (16:9, 9:16, or auto-detect)")
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