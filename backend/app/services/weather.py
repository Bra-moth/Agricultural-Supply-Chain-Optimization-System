import requests
from ..utils.geolocation import get_coordinates

def fetch_weather(lat: float, lon: float, api_key: str):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}"
    return requests.get(url).json()