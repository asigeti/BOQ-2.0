import random

def get_weather_forecast(location: str) -> dict:
    """
    Mock weather forecast.
    """
    conditions = ["Sunny", "Cloudy", "Rainy", "Windy"]
    forecast = []
    for i in range(5):
        forecast.append({
            "day": f"Day {i+1}",
            "condition": random.choice(conditions),
            "temp_high": random.randint(60, 90),
            "temp_low": random.randint(40, 60)
        })
    
    return {
        "location": location,
        "forecast": forecast
    }
