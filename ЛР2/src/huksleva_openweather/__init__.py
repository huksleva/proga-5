"""Public interface of the OpenWeather client."""

from .client import OpenWeatherClient, OpenWeatherError

__all__ = ["OpenWeatherClient", "OpenWeatherError"]
