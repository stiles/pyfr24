import requests

class FR24API:
    def __init__(self, token):
        # Set base URL and headers with the API token.
        self.base_url = "https://fr24api.flightradar24.com"
        self.headers = {
            "Accept": "application/json",
            "Accept-Version": "v1",
            "Authorization": f"Bearer {token}"
        }
    
    def get_live_flights_by_registration(self, registration, bounds=None):
        # Get live flights filtered by aircraft registration.
        url = f"{self.base_url}/api/live/flight-positions/light"
        params = {"registrations": registration}
        if bounds:
            params["bounds"] = bounds
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_airline_light(self, icao):
        # Get basic airline info by ICAO code.
        url = f"{self.base_url}/api/static/airlines/{icao}/light"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_airport_full(self, code):
        # Get detailed airport info by IATA or ICAO code.
        url = f"{self.base_url}/api/static/airports/{code}/full"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_flight_positions_light(self, bounds, **kwargs):
        # Get real-time flight positions within specified bounds.
        url = f"{self.base_url}/api/live/flight-positions/light"
        params = {"bounds": bounds}
        params.update(kwargs)
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_flight_summary_light(self, flights, flight_datetime_from, flight_datetime_to, **kwargs):
        # Get basic flight summary information.
        url = f"{self.base_url}/api/flight-summary/light"
        params = {
            "flights": flights,
            "flight_datetime_from": flight_datetime_from,
            "flight_datetime_to": flight_datetime_to
        }
        params.update(kwargs)
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_flight_summary_full(self, flights, flight_datetime_from, flight_datetime_to, **kwargs):
        # Get detailed flight summary information.
        url = f"{self.base_url}/api/flight-summary/full"
        params = {
            "flights": flights,
            "flight_datetime_from": flight_datetime_from,
            "flight_datetime_to": flight_datetime_to
        }
        params.update(kwargs)
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_flight_tracks(self, flight_id):
        # Get a flight's track (ADS-B pings) using its FR24 flight ID.
        url = f"{self.base_url}/api/flight-tracks"
        params = {"flight_id": flight_id}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()