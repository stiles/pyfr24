import pytest
from pyfr24 import FR24API

# Dummy response object for monkeypatching.
class DummyResponse:
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
    def json(self):
        return self.json_data
    def raise_for_status(self):
        if self.status_code != 200:
            raise Exception(f"HTTP {self.status_code}")

def test_get_airline_light(monkeypatch):
    # Dummy data to simulate an API response.
    dummy_data = {"name": "Test Airline", "iata": "TA", "icao": "TST"}
    def dummy_get(url, headers):
        return DummyResponse(dummy_data)
    monkeypatch.setattr("requests.get", dummy_get)
    
    api = FR24API("dummy_token")
    data = api.get_airline_light("TST")
    assert data["icao"] == "TST"

def test_get_flight_tracks(monkeypatch):
    dummy_data = {"fr24_id": "dummy", "tracks": []}
    def dummy_get(url, headers, params):
        return DummyResponse(dummy_data)
    monkeypatch.setattr("requests.get", dummy_get)
    
    api = FR24API("dummy_token")
    data = api.get_flight_tracks("dummy_id")
    assert "tracks" in data
