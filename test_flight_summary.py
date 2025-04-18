from pyfr24 import FR24API
import os
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get API token from environment
token = os.getenv('FLIGHTRADAR_API_KEY')
if not token:
    raise ValueError("Please set FLIGHTRADAR_API_KEY environment variable")

# Initialize client
client = FR24API(token=token)

# Test flight IDs and numbers
test_data = {
    'flight_ids': ["39f4007e", "39f406c4"],    # Flight IDs
    'flights': ["UA1930", "UA253"]  # Flight numbers
}

# Test dates - use timestamps for more precise control
now = datetime.utcnow()  # Use UTC time
today_start = now.replace(hour=0, minute=0, second=0).strftime("%Y-%m-%dT%H:%M:%SZ")
today_end = now.replace(hour=23, minute=59, second=59).strftime("%Y-%m-%dT%H:%M:%SZ")
test_dates = {
    'from': today_start,
    'to': today_end
}

def test_flight_summary():
    print("\nTesting flight summary methods...")
    print(f"Searching for flights from {test_dates['from']} to {test_dates['to']}")
    
    # Test with first flight ID
    print("\n1. Testing with flight ID (39f4007e):")
    try:
        logger.debug(f"Making request with flight ID: {test_data['flight_ids'][0]}")
        logger.debug(f"Date range: {test_dates['from']} to {test_dates['to']}")
        result = client.get_flight_summary_light(
            flight_ids=test_data['flight_ids'][0],
            flight_datetime_from=test_dates['from'],
            flight_datetime_to=test_dates['to']
        )
        print(f"Light summary response: {result}")
    except Exception as e:
        print(f"Error with flight ID: {e}")
    
    # Test with second flight ID
    print("\n2. Testing with flight ID (39f406c4):")
    try:
        logger.debug(f"Making request with flight ID: {test_data['flight_ids'][1]}")
        logger.debug(f"Date range: {test_dates['from']} to {test_dates['to']}")
        result = client.get_flight_summary_light(
            flight_ids=test_data['flight_ids'][1],
            flight_datetime_from=test_dates['from'],
            flight_datetime_to=test_dates['to']
        )
        print(f"Light summary response: {result}")
    except Exception as e:
        print(f"Error with flight ID: {e}")
    
    # Test with UA1930
    print("\n3. Testing with United flight number (UA1930):")
    try:
        logger.debug(f"Making request with flight number: {test_data['flights'][0]}")
        logger.debug(f"Date range: {test_dates['from']} to {test_dates['to']}")
        result = client.get_flight_summary_light(
            flights=test_data['flights'][0],
            flight_datetime_from=test_dates['from'],
            flight_datetime_to=test_dates['to']
        )
        print(f"Light summary response: {result}")
    except Exception as e:
        print(f"Error with UA1930: {e}")
    
    # Test with UA253
    print("\n4. Testing with United flight number (UA253):")
    try:
        logger.debug(f"Making request with flight number: {test_data['flights'][1]}")
        logger.debug(f"Date range: {test_dates['from']} to {test_dates['to']}")
        result = client.get_flight_summary_light(
            flights=test_data['flights'][1],
            flight_datetime_from=test_dates['from'],
            flight_datetime_to=test_dates['to']
        )
        print(f"Light summary response: {result}")
    except Exception as e:
        print(f"Error with UA253: {e}")
    
    # Test with both flight IDs
    print("\n5. Testing with both flight IDs:")
    try:
        logger.debug(f"Making request with flight IDs: {test_data['flight_ids']}")
        logger.debug(f"Date range: {test_dates['from']} to {test_dates['to']}")
        result = client.get_flight_summary_light(
            flight_ids=test_data['flight_ids'],
            flight_datetime_from=test_dates['from'],
            flight_datetime_to=test_dates['to']
        )
        print(f"Light summary response: {result}")
    except Exception as e:
        print(f"Error with both flight IDs: {e}")
    
    # Test with both flight numbers
    print("\n6. Testing with both flight numbers:")
    try:
        logger.debug(f"Making request with flight numbers: {test_data['flights']}")
        logger.debug(f"Date range: {test_dates['from']} to {test_dates['to']}")
        result = client.get_flight_summary_light(
            flights=test_data['flights'],
            flight_datetime_from=test_dates['from'],
            flight_datetime_to=test_dates['to']
        )
        print(f"Light summary response: {result}")
    except Exception as e:
        print(f"Error with both flight numbers: {e}")
    
    # Let's also try the full summary for UA1930
    print("\n7. Testing full summary with UA1930:")
    try:
        logger.debug(f"Making full summary request with flight number: {test_data['flights'][0]}")
        logger.debug(f"Date range: {test_dates['from']} to {test_dates['to']}")
        result = client.get_flight_summary_full(
            flights=test_data['flights'][0],
            flight_datetime_from=test_dates['from'],
            flight_datetime_to=test_dates['to']
        )
        print(f"Full summary response: {result}")
    except Exception as e:
        print(f"Error with full summary: {e}")
    
    # Test invalid flight format
    print("\n8. Testing with invalid flight format:")
    try:
        result = client.get_flight_summary_light(
            flights="invalid!@#",
            flight_datetime_from=test_dates['from'],
            flight_datetime_to=test_dates['to']
        )
        print(f"Light summary response: {result}")
    except Exception as e:
        print(f"Expected error with invalid flight format: {e}")
    
    # Test invalid date format
    print("\n9. Testing with invalid date format:")
    try:
        result = client.get_flight_summary_light(
            flights=test_data['flights'][0],
            flight_datetime_from="2024-04-18",  # Valid date
            flight_datetime_to="invalid-date"   # Invalid date
        )
        print(f"Light summary response: {result}")
    except Exception as e:
        print(f"Expected error with invalid date: {e}")

if __name__ == "__main__":
    test_flight_summary() 