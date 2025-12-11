class WeatherNotImplementedError(Exception):
    """Raised when weather feature is called but not yet implemented"""
    pass


def get_weather_forecast(location: str) -> dict:
    """
    Get weather forecast for construction planning.

    NO MOCK DATA - This feature requires real weather API integration.
    """
    raise WeatherNotImplementedError(
        "Weather forecast not yet implemented. "
        "This feature requires integration with a real weather API (e.g., OpenWeatherMap)."
    )
