from __future__ import annotations

import json
from datetime import date
from urllib.error import URLError

import pytest

from scripts import weather


class _FakeResponse:
    def __init__(self, body: dict) -> None:
        self._body = json.dumps(body).encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *exc: object) -> bool:
        return False


def _patch_urlopen(monkeypatch: pytest.MonkeyPatch, responses: list) -> list[str]:
    """Queue fake responses (dicts) or exceptions for successive urlopen calls."""

    calls: list[str] = []

    def fake_urlopen(request, timeout=None):
        calls.append(request.full_url)
        item = responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return _FakeResponse(item)

    monkeypatch.setattr(weather.urllib.request, "urlopen", fake_urlopen)
    return calls


def test_weather_code_description_known_and_unknown() -> None:
    assert weather.weather_code_description(0) == "clear"
    assert weather.weather_code_description(61) == "light rain"
    assert weather.weather_code_description(999) == "code 999"
    assert weather.weather_code_description(None) is None


def test_geocode_city_returns_coordinates(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_urlopen(
        monkeypatch, [{"results": [{"latitude": 59.437, "longitude": 24.7536}]}]
    )

    latitude, longitude = weather.geocode_city("Tallinn", "EE")

    assert latitude == pytest.approx(59.437)
    assert longitude == pytest.approx(24.7536)


def test_geocode_city_raises_when_no_results(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_urlopen(monkeypatch, [{"results": []}])

    with pytest.raises(weather.WeatherLookupError):
        weather.geocode_city("Nowhereville")


def test_fetch_weather_returns_forecast_data(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_urlopen(
        monkeypatch,
        [
            {
                "daily": {
                    "weathercode": [0],
                    "temperature_2m_max": [20.0],
                    "temperature_2m_min": [10.0],
                    "windspeed_10m_max": [12.4],
                }
            }
        ],
    )

    result = weather.fetch_weather(59.4, 24.7, date(2026, 7, 5))

    assert result == {"weather": "clear", "temperature_c": 15.0, "wind": "12 km/h"}


def test_fetch_weather_falls_back_to_archive_when_forecast_is_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _patch_urlopen(
        monkeypatch,
        [
            {
                "daily": {
                    "weathercode": [],
                    "temperature_2m_max": [],
                    "temperature_2m_min": [],
                    "windspeed_10m_max": [],
                }
            },
            {
                "daily": {
                    "weathercode": [61],
                    "temperature_2m_max": [8.0],
                    "temperature_2m_min": [4.0],
                    "windspeed_10m_max": [5.0],
                }
            },
        ],
    )

    result = weather.fetch_weather(59.4, 24.7, date(2020, 1, 1))

    assert result["weather"] == "light rain"
    assert result["temperature_c"] == 6.0
    assert len(calls) == 2
    assert weather.FORECAST_URL in calls[0]
    assert weather.ARCHIVE_URL in calls[1]


def test_fetch_weather_raises_when_no_data_anywhere(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_urlopen(monkeypatch, [{"daily": {}}, {"daily": {}}])

    with pytest.raises(weather.WeatherLookupError):
        weather.fetch_weather(0, 0, date(2026, 1, 1))


def test_fetch_weather_raises_when_request_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_urlopen(monkeypatch, [URLError("boom"), URLError("boom again")])

    with pytest.raises(weather.WeatherLookupError):
        weather.fetch_weather(0, 0, date(2026, 1, 1))


def test_geolocate_ip_returns_coordinates(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_urlopen(monkeypatch, [{"latitude": 59.4, "longitude": 24.7}])

    latitude, longitude = weather.geolocate_ip()

    assert (latitude, longitude) == (59.4, 24.7)


def test_geolocate_ip_raises_when_coordinates_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_urlopen(monkeypatch, [{"error": "reserved range"}])

    with pytest.raises(weather.WeatherLookupError):
        weather.geolocate_ip()


def test_fetch_weather_for_city_combines_geocode_and_fetch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_urlopen(
        monkeypatch,
        [
            {"results": [{"latitude": 59.4, "longitude": 24.7}]},
            {
                "daily": {
                    "weathercode": [0],
                    "temperature_2m_max": [20.0],
                    "temperature_2m_min": [10.0],
                    "windspeed_10m_max": [12.0],
                }
            },
        ],
    )

    result = weather.fetch_weather_for_city("Tallinn", "EE", date(2026, 7, 5))

    assert result["weather"] == "clear"


def test_fetch_weather_for_auto_locate_combines_geolocation_and_fetch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_urlopen(
        monkeypatch,
        [
            {"latitude": 59.4, "longitude": 24.7},
            {
                "daily": {
                    "weathercode": [3],
                    "temperature_2m_max": [5.0],
                    "temperature_2m_min": [1.0],
                    "windspeed_10m_max": [20.0],
                }
            },
        ],
    )

    result = weather.fetch_weather_for_auto_locate(date(2026, 7, 5))

    assert result["weather"] == "overcast"
    assert result["wind"] == "20 km/h"
