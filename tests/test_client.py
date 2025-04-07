"""
Tests for the FR24API client.
"""

import os
import json
import unittest
from unittest.mock import patch, MagicMock
import requests
from pyfr24 import FR24API, FR24Error, FR24AuthenticationError, FR24NotFoundError, FR24ConnectionError

class TestFR24API(unittest.TestCase):
    """Test cases for the FR24API client."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.api = FR24API("test_token")
        self.mock_response = MagicMock()
        self.mock_response.json.return_value = {"data": "test_data"}
        self.mock_response.status_code = 200  # Set default status code to 200 (success)
    
    @patch('requests.Session.request')
    def test_get_flight_summary_light(self, mock_request):
        """Test get_flight_summary_light method."""
        mock_request.return_value = self.mock_response
        
        result = self.api.get_flight_summary_light(
            flights="AA123",
            flight_datetime_from="2023-01-01T00:00:00Z",
            flight_datetime_to="2023-01-01T23:59:59Z"
        )
        
        mock_request.assert_called_once()
        self.assertEqual(result, {"data": "test_data"})
    
    @patch('requests.Session.request')
    def test_get_flight_summary_full(self, mock_request):
        """Test get_flight_summary_full method."""
        mock_request.return_value = self.mock_response
        
        result = self.api.get_flight_summary_full(
            flights="AA123",
            flight_datetime_from="2023-01-01T00:00:00Z",
            flight_datetime_to="2023-01-01T23:59:59Z"
        )
        
        mock_request.assert_called_once()
        self.assertEqual(result, {"data": "test_data"})
    
    @patch('requests.Session.request')
    def test_get_live_flights_by_registration(self, mock_request):
        """Test get_live_flights_by_registration method."""
        mock_request.return_value = self.mock_response
        
        result = self.api.get_live_flights_by_registration("N12345")
        
        mock_request.assert_called_once()
        self.assertEqual(result, {"data": "test_data"})
    
    @patch('requests.Session.request')
    def test_get_airline_light(self, mock_request):
        """Test get_airline_light method."""
        mock_request.return_value = self.mock_response
        
        result = self.api.get_airline_light("AAL")
        
        mock_request.assert_called_once()
        self.assertEqual(result, {"data": "test_data"})
    
    @patch('requests.Session.request')
    def test_get_airport_full(self, mock_request):
        """Test get_airport_full method."""
        mock_request.return_value = self.mock_response
        
        result = self.api.get_airport_full("JFK")
        
        mock_request.assert_called_once()
        self.assertEqual(result, {"data": "test_data"})
    
    @patch('requests.Session.request')
    def test_get_flight_positions_light(self, mock_request):
        """Test get_flight_positions_light method."""
        mock_request.return_value = self.mock_response
        
        result = self.api.get_flight_positions_light("40.0,-74.0,41.0,-73.0")
        
        mock_request.assert_called_once()
        self.assertEqual(result, {"data": "test_data"})
    
    @patch('requests.Session.request')
    def test_get_flight_tracks(self, mock_request):
        """Test get_flight_tracks method."""
        mock_request.return_value = self.mock_response
        
        result = self.api.get_flight_tracks("12345")
        
        mock_request.assert_called_once()
        self.assertEqual(result, {"data": "test_data"})
    
    @patch('requests.Session.request')
    def test_authentication_error(self, mock_request):
        """Test handling of authentication errors."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_request.return_value = mock_response
        
        with self.assertRaises(FR24AuthenticationError):
            self.api.get_flight_summary_light(
                flights="AA123",
                flight_datetime_from="2023-01-01T00:00:00Z",
                flight_datetime_to="2023-01-01T23:59:59Z"
            )
    
    @patch('requests.Session.request')
    def test_not_found_error(self, mock_request):
        """Test handling of not found errors."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_request.return_value = mock_response
        
        with self.assertRaises(FR24NotFoundError):
            self.api.get_flight_summary_light(
                flights="AA123",
                flight_datetime_from="2023-01-01T00:00:00Z",
                flight_datetime_to="2023-01-01T23:59:59Z"
            )
    
    @patch('requests.Session.request')
    def test_connection_error(self, mock_request):
        """Test handling of connection errors."""
        mock_request.side_effect = requests.exceptions.ConnectionError("Connection error")
        
        with self.assertRaises(FR24ConnectionError):
            self.api.get_flight_summary_light(
                flights="AA123",
                flight_datetime_from="2023-01-01T00:00:00Z",
                flight_datetime_to="2023-01-01T23:59:59Z"
            )

if __name__ == '__main__':
    unittest.main()
