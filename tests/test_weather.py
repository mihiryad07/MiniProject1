from src.weather import (
    WeatherAPIError,
    fetch_current_weather,
    get_season_for_weather,
    manual_weather,
    weather_clothing_advice,
)


def test_manual_weather_normalizes_fallback_values():
    weather = manual_weather(5, "Snow", False)

    assert weather["temperature_c"] == 5
    assert weather["source"] == "Manual input"
    assert weather["condition"] == "Snow"
    assert get_season_for_weather(weather) == "Winter"


def test_weather_advice_considers_cold_and_rain():
    advice = weather_clothing_advice(manual_weather(7, "Rain", True))

    assert advice["season"] == "Winter"
    assert advice["rain"] is True
    assert "jacket" in advice["advice"].lower()
    assert "closed" in advice["advice"].lower()


def test_missing_api_key_is_reported_as_weather_error():
    try:
        fetch_current_weather("Mumbai", api_key="")
        assert False, "Expected WeatherAPIError"
    except WeatherAPIError:
        pass
