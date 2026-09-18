"""Command-line interface; the API key is read from the environment."""

import argparse
import json
import os

from .client import OpenWeatherClient, OpenWeatherError


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch OpenWeather data")
    parser.add_argument("city")
    parser.add_argument("--forecast", action="store_true")
    parser.add_argument("--units", choices=["standard", "metric", "imperial"], default="metric")
    parser.add_argument("--lang", default="ru")
    args = parser.parse_args()
    key = os.environ.get("OPENWEATHER_API_KEY", "")
    try:
        with OpenWeatherClient(key, units=args.units, lang=args.lang) as client:
            data = client.forecast(args.city) if args.forecast else client.current(args.city)
    except (ValueError, OpenWeatherError) as exc:
        parser.exit(1, f"Error: {exc}\n")
    print(json.dumps(data, ensure_ascii=False, indent=2))
