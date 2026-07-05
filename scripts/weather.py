"""Look up weather for a run day from the internet, stdlib-only.

Two independent lookups, both opt-in (never called unless the caller asks):

- ``geocode_city`` resolves a city/country name to coordinates via the
  Open-Meteo Geocoding API (free, no API key).
- ``geolocate_ip`` resolves the caller's approximate location from their
  public IP via a free IP geolocation service. This is a coarser, more
  privacy-sensitive fallback for when the caller does not want to type a
  city name; it is only ever invoked by an explicit ``--auto-locate`` flag
  upstream, never by default.

``fetch_weather`` then looks up the day's weather for a resolved
``(latitude, longitude)`` using Open-Meteo's Forecast API (which covers
today and the recent past) and falls back to the Archive API for older
dates. No API key is required for either. GPS from the runner's actual
activity is never involved here: only a city name (or, with auto-locate, the
public IP address) leaves the machine.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from typing import Any

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
IP_GEOLOCATION_URL = "https://ipapi.co/json/"

DEFAULT_TIMEOUT = 10.0

# WMO weather codes (used by Open-Meteo) mapped to short human descriptions.
# https://open-meteo.com/en/docs (see "WMO Weather interpretation codes")
_WEATHER_CODES: dict[int, str] = {
    0: "clear",
    1: "mostly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "fog",
    51: "light drizzle",
    53: "drizzle",
    55: "heavy drizzle",
    56: "freezing drizzle",
    57: "freezing drizzle",
    61: "light rain",
    63: "rain",
    65: "heavy rain",
    66: "freezing rain",
    67: "freezing rain",
    71: "light snow",
    73: "snow",
    75: "heavy snow",
    77: "snow grains",
    80: "rain showers",
    81: "rain showers",
    82: "heavy rain showers",
    85: "snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with hail",
    99: "thunderstorm with hail",
}


class WeatherLookupError(Exception):
    """Raised when a geocoding, geolocation, or weather request fails."""


def weather_code_description(code: int | None) -> str | None:
    """Map a WMO weather code to a short human-readable description."""

    if code is None:
        return None
    return _WEATHER_CODES.get(int(code), f"code {code}")


def _get_json(url: str, params: dict[str, Any], timeout: float) -> dict[str, Any]:
    """Perform a GET request and parse the JSON response body."""

    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(f"{url}?{query}", headers={"User-Agent": "running-content-engine"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise WeatherLookupError(f"Request to {url} failed: {exc}") from exc

    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise WeatherLookupError(f"Could not parse JSON response from {url}: {exc}") from exc


def geocode_city(
    city: str, country: str | None = None, *, timeout: float = DEFAULT_TIMEOUT
) -> tuple[float, float]:
    """Resolve a city (and optional ISO country code) to (latitude, longitude).

    Raises:
        WeatherLookupError: if the request fails or no match is found.
    """

    params: dict[str, Any] = {"name": city, "count": 1, "format": "json"}
    if country:
        params["country_code"] = country

    data = _get_json(GEOCODING_URL, params, timeout)
    results = data.get("results") or []
    if not results:
        location = f"{city}, {country}" if country else city
        raise WeatherLookupError(f"No geocoding match found for '{location}'.")

    match = results[0]
    return float(match["latitude"]), float(match["longitude"])


def geolocate_ip(*, timeout: float = DEFAULT_TIMEOUT) -> tuple[float, float]:
    """Resolve the caller's approximate (latitude, longitude) from their public IP.

    This sends a request to a third-party IP geolocation service and should
    only be called when the caller has explicitly opted in (e.g. via an
    ``--auto-locate`` flag), never by default.

    Raises:
        WeatherLookupError: if the request fails or returns no coordinates.
    """

    request = urllib.request.Request(
        IP_GEOLOCATION_URL, headers={"User-Agent": "running-content-engine"}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise WeatherLookupError(f"IP geolocation request failed: {exc}") from exc

    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        raise WeatherLookupError(f"Could not parse IP geolocation response: {exc}") from exc

    latitude = data.get("latitude")
    longitude = data.get("longitude")
    if latitude is None or longitude is None:
        raise WeatherLookupError(f"IP geolocation response had no coordinates: {data}")

    return float(latitude), float(longitude)


def _extract_daily_weather(data: dict[str, Any]) -> dict[str, Any] | None:
    """Pull the first day's weather fields out of an Open-Meteo daily response."""

    daily = data.get("daily") or {}
    codes = daily.get("weathercode") or []
    highs = daily.get("temperature_2m_max") or []
    lows = daily.get("temperature_2m_min") or []
    winds = daily.get("windspeed_10m_max") or []

    if not codes and not highs and not lows:
        return None

    result: dict[str, Any] = {}

    code = codes[0] if codes else None
    description = weather_code_description(code)
    if description is not None:
        result["weather"] = description

    if highs and lows and highs[0] is not None and lows[0] is not None:
        result["temperature_c"] = round((float(highs[0]) + float(lows[0])) / 2, 1)
    elif highs and highs[0] is not None:
        result["temperature_c"] = round(float(highs[0]), 1)

    if winds and winds[0] is not None:
        result["wind"] = f"{round(float(winds[0]))} km/h"

    return result or None


def fetch_weather(
    latitude: float,
    longitude: float,
    target_date: date,
    *,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Fetch a day's weather summary for a resolved location.

    Tries the Forecast API first (covers today and the recent past), then
    falls back to the Archive API for older dates. Returns a dict shaped like
    ``{"weather": "clear", "temperature_c": 16.4, "wind": "12 km/h"}`` with
    only the keys that were resolvable.

    Raises:
        WeatherLookupError: if both endpoints fail or return no data.
    """

    common_params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": target_date.isoformat(),
        "end_date": target_date.isoformat(),
        "daily": "weathercode,temperature_2m_max,temperature_2m_min,windspeed_10m_max",
        "timezone": "auto",
    }

    errors: list[str] = []

    try:
        data = _get_json(FORECAST_URL, common_params, timeout)
        result = _extract_daily_weather(data)
        if result:
            return result
    except WeatherLookupError as exc:
        errors.append(str(exc))

    try:
        data = _get_json(ARCHIVE_URL, common_params, timeout)
        result = _extract_daily_weather(data)
        if result:
            return result
    except WeatherLookupError as exc:
        errors.append(str(exc))

    detail = f" ({'; '.join(errors)})" if errors else ""
    raise WeatherLookupError(
        f"No weather data available for {target_date.isoformat()} at "
        f"({latitude}, {longitude}).{detail}"
    )


def fetch_weather_for_city(
    city: str,
    country: str | None,
    target_date: date,
    *,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Geocode a city/country and fetch that day's weather in one call."""

    latitude, longitude = geocode_city(city, country, timeout=timeout)
    return fetch_weather(latitude, longitude, target_date, timeout=timeout)


def fetch_weather_for_auto_locate(
    target_date: date, *, timeout: float = DEFAULT_TIMEOUT
) -> dict[str, Any]:
    """Geolocate the caller's IP and fetch that day's weather in one call."""

    latitude, longitude = geolocate_ip(timeout=timeout)
    return fetch_weather(latitude, longitude, target_date, timeout=timeout)
