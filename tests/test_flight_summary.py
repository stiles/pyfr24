import pytest
from pyfr24 import FR24API
import os
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.fixture
def api_token():
    """Fixture to get the API token from environment."""
    token = os.getenv('FLIGHTRADAR_API_KEY')
    if not token:
        pytest.skip("FLIGHTRADAR_API_KEY environment variable not set")
    return token

@pytest.fixture
def client(api_token):
    """Fixture to create and return an FR24API client."""
    return FR24API(token=api_token)

@pytest.fixture
def test_data():
    """Fixture containing test flight IDs and numbers."""
    return {
        'flight_ids': ["39f4007e", "39f406c4"],    # Flight IDs
        'flights': ["UA1930", "UA253"]  # Flight numbers
    }

@pytest.fixture
def test_dates():
    """Fixture to generate test date range."""
    now = datetime.utcnow()  # Use UTC time
    today_start = now.replace(hour=0, minute=0, second=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    today_end = now.replace(hour=23, minute=59, second=59).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        'from': today_start,
        'to': today_end
    }

def test_single_flight_id(client, test_data, test_dates):
    """Test retrieving flight summary with a single flight ID."""
    logger.debug(f"Making request with flight ID: {test_data['flight_ids'][0]}")
    logger.debug(f"Date range: {test_dates['from']} to {test_dates['to']}")
    
    result = client.get_flight_summary_light(
        flight_ids=test_data['flight_ids'][0],
        flight_datetime_from=test_dates['from'],
        flight_datetime_to=test_dates['to']
    )
    
    assert result is not None
    assert 'data' in result
    assert len(result['data']) > 0
    assert result['data'][0]['fr24_id'] == test_data['flight_ids'][0]

def test_single_flight_number(client, test_data, test_dates):
    """Test retrieving flight summary with a single flight number."""
    logger.debug(f"Making request with flight number: {test_data['flights'][0]}")
    logger.debug(f"Date range: {test_dates['from']} to {test_dates['to']}")
    
    result = client.get_flight_summary_light(
        flights=test_data['flights'][0],
        flight_datetime_from=test_dates['from'],
        flight_datetime_to=test_dates['to']
    )
    
    assert result is not None
    assert 'data' in result
    assert len(result['data']) > 0
    assert result['data'][0]['flight'] == test_data['flights'][0]

def test_multiple_flight_ids(client, test_data, test_dates):
    """Test retrieving flight summary with multiple flight IDs."""
    logger.debug(f"Making request with flight IDs: {test_data['flight_ids']}")
    logger.debug(f"Date range: {test_dates['from']} to {test_dates['to']}")
    
    result = client.get_flight_summary_light(
        flight_ids=test_data['flight_ids'],
        flight_datetime_from=test_dates['from'],
        flight_datetime_to=test_dates['to']
    )
    
    assert result is not None
    assert 'data' in result
    assert len(result['data']) == len(test_data['flight_ids'])
    returned_ids = [flight['fr24_id'] for flight in result['data']]
    assert all(id in returned_ids for id in test_data['flight_ids'])

def test_multiple_flight_numbers(client, test_data, test_dates):
    """Test retrieving flight summary with multiple flight numbers."""
    logger.debug(f"Making request with flight numbers: {test_data['flights']}")
    logger.debug(f"Date range: {test_dates['from']} to {test_dates['to']}")
    
    result = client.get_flight_summary_light(
        flights=test_data['flights'],
        flight_datetime_from=test_dates['from'],
        flight_datetime_to=test_dates['to']
    )
    
    assert result is not None
    assert 'data' in result
    assert len(result['data']) > 0
    returned_flights = [flight['flight'] for flight in result['data']]
    assert all(flight in returned_flights for flight in test_data['flights'])

def test_full_summary(client, test_data, test_dates):
    """Test retrieving full flight summary."""
    logger.debug(f"Making full summary request with flight number: {test_data['flights'][0]}")
    logger.debug(f"Date range: {test_dates['from']} to {test_dates['to']}")
    
    result = client.get_flight_summary_full(
        flights=test_data['flights'][0],
        flight_datetime_from=test_dates['from'],
        flight_datetime_to=test_dates['to']
    )
    
    assert result is not None
    assert 'data' in result
    assert len(result['data']) > 0
    assert result['data'][0]['flight'] == test_data['flights'][0]
    # Verify full summary contains additional fields
    assert 'actual_distance' in result['data'][0]
    assert 'circle_distance' in result['data'][0]

def test_invalid_flight_format(client, test_dates):
    """Test handling of invalid flight format."""
    with pytest.raises(Exception) as exc_info:
        client.get_flight_summary_light(
            flights="invalid!@#",
            flight_datetime_from=test_dates['from'],
            flight_datetime_to=test_dates['to']
        )
    assert "Validation failed" in str(exc_info.value)

def test_invalid_date_format(client, test_data):
    """Test handling of invalid date format."""
    with pytest.raises(Exception) as exc_info:
        client.get_flight_summary_light(
            flights=test_data['flights'][0],
            flight_datetime_from="2024-04-18",  # Valid date
            flight_datetime_to="invalid-date"   # Invalid date
        )
    assert "Invalid date format" in str(exc_info.value) 