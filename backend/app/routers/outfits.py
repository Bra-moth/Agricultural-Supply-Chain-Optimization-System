from fastapi import APIRouter
from ..services.weather import fetch_weather
from ..services.recommendations import generate_outfit

router = APIRouter(prefix="/outfits")

@router.get("/")
async def get_outfits(user_id: str, lat: float, lon: float):
    weather = fetch_weather(lat, lon, "your_api_key")
    return generate_outfit(weather, user_id)