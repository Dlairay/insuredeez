"""Tool #1
an API call to a free weather API that takes in the name of a region in Singapore and returns the weather conditions
"""
import json
import requests
def get_weather_for_area(area_name: str) -> dict:
    """Get weather forecast for a Singapore area including UV index."""
    # convert area name into a standard form
    area_name = area_name.lower().replace(" ", "_")

    # get coordinates of location name
    with open("/content/intro_to_ai_agents/sg_planning_area_coords.json", "r", encoding="utf-8") as f:
        all_coords = json.load(f)

    if area_name not in all_coords:
        raise ValueError(f"Unknown area: {area_name}")

    coords = all_coords[area_name]

    # Fixed default variables - no optional parameters
    hourly_vars = ["temperature_2m", "precipitation_probability", "wind_speed_10m"]
    daily_vars = ["weathercode", "temperature_2m_max", "temperature_2m_min", "uv_index_max"]
    timezone = "Asia/Singapore"

    params = {
        "latitude": coords["lat"],
        "longitude": coords["lon"],
        "current_weather": "true",
        "hourly": ",".join(hourly_vars),
        "daily": ",".join(daily_vars),
        "timezone": timezone,
    }

    resp = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=10)
    return resp.json()