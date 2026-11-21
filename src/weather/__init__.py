"""OpenWeather integration and weather suitability helpers."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional


OPENWEATHER_CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"


class WeatherAPIError(RuntimeError):
    """Raised when current weather cannot be retrieved or parsed."""


def fetch_current_weather(city: str, api_key: Optional[str] = None, timeout: int = 10) -> Dict[str, Any]:
    """Fetch and normalize current weather for a city using OpenWeather."""
    city_name = city.strip()
    if not city_name:
        raise WeatherAPIError("City is required.")

    if api_key is None:
        from src.config import API_KEY
        api_key = API_KEY

    key = str(api_key or "").strip()
    if not key:
        raise WeatherAPIError("OPENWEATHER_API_KEY is not configured.")

    query = urllib.parse.urlencode({"q": city_name, "appid": key, "units": "metric"})
    request = urllib.request.Request(
        f"{OPENWEATHER_CURRENT_URL}?{query}",
        headers={"Accept": "application/json", "User-Agent": "MLMP-Weather/1.0"},
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            raise WeatherAPIError("OpenWeather rejected the API key.") from exc
        if exc.code == 404:
            raise WeatherAPIError(f"City '{city_name}' was not found.") from exc
        raise WeatherAPIError(f"OpenWeather request failed with HTTP status {exc.code}.") from exc
    except urllib.error.URLError as exc:
        raise WeatherAPIError("Could not connect to OpenWeather. Check your internet connection.") from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise WeatherAPIError("OpenWeather returned an invalid response.") from exc

    try:
        temperature = float(payload["main"]["temp"])
        weather_items = payload.get("weather") or []
        condition = str(weather_items[0].get("main", "Unknown")).strip() or "Unknown"
        description = str(weather_items[0].get("description", condition)).strip() or condition
        feels_like = float(payload["main"].get("feels_like", temperature))
        humidity = int(payload["main"].get("humidity", 0))
    except (KeyError, TypeError, ValueError) as exc:
        raise WeatherAPIError("OpenWeather response did not contain valid weather data.") from exc

    rain = condition.lower() in {"rain", "drizzle", "thunderstorm"}
    rain_amount = payload.get("rain")
    if isinstance(rain_amount, dict):
        rain = rain or any(float(value) > 0 for value in rain_amount.values() if isinstance(value, (int, float)))

    return {
        "city": str(payload.get("name", city_name)),
        "temperature_c": temperature,
        "feels_like_c": feels_like,
        "condition": condition,
        "description": description,
        "humidity": humidity,
        "rain": rain,
        "source": "OpenWeather",
    }


def manual_weather(temperature_c: float, condition: str = "Clear", rain: bool = False) -> Dict[str, Any]:
    """Normalize manually entered weather data for fallback use."""
    try:
        temperature = float(temperature_c)
    except (TypeError, ValueError) as exc:
        raise ValueError("Temperature must be a number.") from exc

    normalized_condition = str(condition or "Clear").strip().title() or "Clear"
    return {
        "city": "Manual input",
        "temperature_c": temperature,
        "feels_like_c": temperature,
        "condition": normalized_condition,
        "description": normalized_condition,
        "humidity": None,
        "rain": bool(rain or normalized_condition.lower() in {"rain", "drizzle", "thunderstorm"}),
        "source": "Manual input",
    }


def get_season_for_weather(weather: Dict[str, Any]) -> str:
    """Map current temperature to a clothing season."""
    temperature = float(weather.get("temperature_c", 20.0))
    if temperature < 10:
        return "Winter"
    if temperature < 18:
        return "Autumn"
    if temperature < 27:
        return "Spring"
    return "Summer"


def weather_clothing_advice(weather: Dict[str, Any]) -> Dict[str, Any]:
    """Create season-appropriate clothing advice, including rain and cold guidance."""
    temperature = float(weather.get("temperature_c", 20.0))
    rain = bool(weather.get("rain", False))
    season = get_season_for_weather(weather)

    if temperature < 10:
        clothing = "Wear a warm jacket or sweater, trousers or jeans, and closed shoes."
    elif temperature < 18:
        clothing = "Choose a light jacket or hoodie with trousers or jeans."
    elif temperature < 27:
        clothing = "Choose breathable shirts or tops with trousers, jeans, or shorts."
    else:
        clothing = "Choose light fabrics, shorts or skirts, and breathable tops."

    if rain:
        clothing += " Add a rain-resistant jacket and wear closed, water-safe footwear."

    return {"season": season, "temperature_c": temperature, "rain": rain, "advice": clothing}
