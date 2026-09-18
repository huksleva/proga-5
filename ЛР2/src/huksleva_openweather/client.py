"""Current weather and five-day forecast through OpenWeather API 2.5."""

from typing import Any

import requests


class OpenWeatherError(Exception):
    """An API, transport, or response-format error."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class OpenWeatherClient:
    """Reusable client. An injected session remains owned by the caller."""

    def __init__(
        self,
        api_key: str,
        *,
        units: str = "metric",
        lang: str = "ru",
        timeout: float = 10,
        session: requests.Session | None = None,
    ):
        if not api_key.strip():
            raise ValueError("API key must not be empty")
        if units not in {"standard", "metric", "imperial"}:
            raise ValueError("Unsupported units")
        if timeout <= 0:
            raise ValueError("Timeout must be positive")
        self._api_key = api_key
        self.units = units
        self.lang = lang
        self.timeout = timeout
        self._owns_session = session is None
        self._session = session if session is not None else requests.Session()

    def current(self, city: str) -> dict[str, Any]:
        """Return current weather for a city, e.g. 'Moscow,RU'."""
        return self._get("weather", city)

    def forecast(self, city: str) -> dict[str, Any]:
        """Return the five-day forecast in three-hour intervals."""
        return self._get("forecast", city)

    def _get(self, endpoint: str, city: str) -> dict[str, Any]:
        if not city.strip():
            raise ValueError("City must not be empty")
        try:
            response = self._session.get(
                f"https://api.openweathermap.org/data/2.5/{endpoint}",
                params={"q": city, "appid": self._api_key,
                        "units": self.units, "lang": self.lang},
                timeout=self.timeout,
            )
        except requests.RequestException:
            # Requests exceptions can contain the URL with the secret API key.
            raise OpenWeatherError("Unable to contact OpenWeather") from None
        try:
            payload = response.json()
        except ValueError:
            raise OpenWeatherError("OpenWeather returned invalid JSON", response.status_code) from None
        if not isinstance(payload, dict):
            raise OpenWeatherError("OpenWeather returned an invalid response", response.status_code)
        if response.status_code != 200 or str(payload.get("cod", 200)) != "200":
            raise OpenWeatherError(
                f"OpenWeather request failed (HTTP {response.status_code})",
                response.status_code,
            )
        return payload

    def close(self) -> None:
        """Close the session created by this client."""
        if self._owns_session:
            self._session.close()

    def __enter__(self) -> "OpenWeatherClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
