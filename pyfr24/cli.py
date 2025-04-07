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

def get_api_client(args):
    """Get an API client instance using the provided token or environment variable."""
    token = args.token or os.environ.get("FLIGHTRADAR_API_KEY")
    if not token:
        print("Error: No API token provided. Set FLIGHTRADAR_API_KEY environment variable or use --token.")
        sys.exit(1)
    return FR24API(token)

def format_json(data):
    """Format JSON data for display."""
    return json.dumps(data, indent=2)

def flight_summary_command(args):
    """Handle the flight summary command."""
    logger = setup_logging(args)
    api = get_api_client(args)
    
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
    api = get_api_client(args)
    
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
    api = get_api_client(args)
    
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
    """Handle the export flight command."""
    logger = setup_logging(args)
    api = get_api_client(args)
    
    try:
        output_dir = api.export_flight_data(args.flight_id, output_dir=args.output_dir)
        print(f"Flight data exported to directory: {output_dir}")
    except Exception as e:
        logger.error(f"Error exporting flight data: {e}")
        print(f"Error: {e}")
        sys.exit(1)

def airline_info_command(args):
    """Handle the airline info command."""
    logger = setup_logging(args)
    api = get_api_client(args)
    
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
    api = get_api_client(args)
    
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
    api = get_api_client(args)
    
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

def create_parser():
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Flightradar24 API client command-line interface",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Global arguments
    parser.add_argument("--token", help="API token (can also be set via FLIGHTRADAR_API_KEY env var)")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Logging level")
    parser.add_argument("--log-file", help="Log file path")
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Flight summary command
    flight_summary_parser = subparsers.add_parser("flight-summary", help="Get flight summary")
    flight_summary_parser.add_argument("--flight", required=True, help="Flight number or callsign")
    flight_summary_parser.add_argument("--from-date", required=True, help="Start date/time (ISO format)")
    flight_summary_parser.add_argument("--to-date", required=True, help="End date/time (ISO format)")
    flight_summary_parser.add_argument("--full", action="store_true", help="Get full summary instead of light")
    flight_summary_parser.add_argument("--output", help="Output file path (JSON)")
    flight_summary_parser.set_defaults(func=flight_summary_command)
    
    # Live flights command
    live_flights_parser = subparsers.add_parser("live-flights", help="Get live flights by registration")
    live_flights_parser.add_argument("--registration", required=True, help="Aircraft registration")
    live_flights_parser.add_argument("--output", help="Output file path (JSON)")
    live_flights_parser.set_defaults(func=live_flights_command)
    
    # Flight tracks command
    flight_tracks_parser = subparsers.add_parser("flight-tracks", help="Get flight tracks")
    flight_tracks_parser.add_argument("--flight-id", required=True, help="Flight ID")
    flight_tracks_parser.add_argument("--output", help="Output file path (JSON)")
    flight_tracks_parser.set_defaults(func=flight_tracks_command)
    
    # Export flight command
    export_flight_parser = subparsers.add_parser("export-flight", help="Export flight data")
    export_flight_parser.add_argument("--flight-id", required=True, help="Flight ID")
    export_flight_parser.add_argument("--output-dir", help="Output directory")
    export_flight_parser.set_defaults(func=export_flight_command)
    
    # Airline info command
    airline_info_parser = subparsers.add_parser("airline-info", help="Get airline information")
    airline_info_parser.add_argument("--icao", required=True, help="Airline ICAO code")
    airline_info_parser.add_argument("--output", help="Output file path (JSON)")
    airline_info_parser.set_defaults(func=airline_info_command)
    
    # Airport info command
    airport_info_parser = subparsers.add_parser("airport-info", help="Get airport information")
    airport_info_parser.add_argument("--code", required=True, help="Airport IATA or ICAO code")
    airport_info_parser.add_argument("--output", help="Output file path (JSON)")
    airport_info_parser.set_defaults(func=airport_info_command)
    
    # Flight positions command
    flight_positions_parser = subparsers.add_parser("flight-positions", help="Get flight positions")
    flight_positions_parser.add_argument("--bounds", required=True, 
                                        help="Bounding box (format: minLat,minLon,maxLat,maxLon)")
    flight_positions_parser.add_argument("--output", help="Output file path (JSON)")
    flight_positions_parser.set_defaults(func=flight_positions_command)
    
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