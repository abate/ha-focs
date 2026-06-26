"""Data update coordinator for the focs.cat fire integration."""

from __future__ import annotations

import logging
import math
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    ANON_KEY,
    CONF_INCLUDE_ALL,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_RADIUS_KM,
    CONF_SCAN_INTERVAL,
    DEFAULT_INCLUDE_ALL,
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    DEFAULT_RADIUS_KM,
    DEFAULT_SCAN_INTERVAL,
    SUPABASE_URL,
)

_LOGGER = logging.getLogger(__name__)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km between two lat/lon points."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = (
        math.sin(dp / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _yes(value: Any) -> bool:
    """focs.cat encodes booleans as the strings 'yes'/'no'."""
    if isinstance(value, str):
        return value.strip().lower() == "yes"
    return bool(value)


def normalize_fire(raw: dict[str, Any], distance_km: float) -> dict[str, Any]:
    """Project a raw focs.cat row into a clean, UI/notification-friendly dict."""
    fid = raw.get("id")
    return {
        "id": fid,
        "status": raw.get("status"),
        "type": raw.get("type"),
        "location": raw.get("where_geolocation_full") or raw.get("where_geolocation"),
        "latitude": _to_float(raw.get("latitude")),
        "longitude": _to_float(raw.get("longitude")),
        "distance_km": round(distance_km, 2),
        "ops": _to_int(raw.get("ops")),
        "radius": raw.get("radius"),
        "fire_trucks": _to_int(raw.get("total_fire_trucks")),
        "firefighters": _to_int(raw.get("total_firefighters")),
        "helicopters": _to_int(raw.get("total_helicopters")),
        "planes": _to_int(raw.get("total_planes")),
        "burnt_area": raw.get("total_burnt_area_iso"),
        "is_forest_fire": _yes(raw.get("is_forest_fire")),
        "is_controlled": _yes(raw.get("is_controlled_fire")),
        "is_stabilized": _yes(raw.get("is_stabilized_fire")),
        "is_extinguished": _yes(raw.get("is_extinguished_fire")),
        "description": raw.get("tweet_text"),
        "tweet_url": raw.get("tweet_url"),
        "media": raw.get("tweet_media_array"),
        "source": raw.get("source"),
        "last_update": (
            raw.get("when_last_time")
            or raw.get("when_timestamp")
            or raw.get("tweet_timestamp")
        ),
        "url": f"https://focs.cat/fire/{fid}",
    }


class FocsCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Polls the focs.cat backend and keeps the list of in-range fires."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        opts = {**entry.data, **entry.options}
        self._lat = float(opts.get(CONF_LATITUDE, DEFAULT_LATITUDE))
        self._lon = float(opts.get(CONF_LONGITUDE, DEFAULT_LONGITUDE))
        self._radius = float(opts.get(CONF_RADIUS_KM, DEFAULT_RADIUS_KM))
        self._include_all = bool(opts.get(CONF_INCLUDE_ALL, DEFAULT_INCLUDE_ALL))
        interval = int(opts.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))

        # Last-seen status per fire id, so we fire an event for new fires and
        # for fires whose status changed.
        self.seen: dict[Any, Any] = {}

        super().__init__(
            hass,
            _LOGGER,
            name="focs.cat fires",
            update_interval=timedelta(minutes=interval),
        )

    async def _fetch_fires(self) -> list[dict[str, Any]]:
        session = async_get_clientsession(self.hass)
        url = (
            f"{SUPABASE_URL}/rest/v1/fires"
            "?select=*&order=when_last_time.desc&limit=2000"
        )
        headers = {"apikey": ANON_KEY, "Authorization": f"Bearer {ANON_KEY}"}
        async with session.get(url, headers=headers, timeout=30) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def _async_update_data(self) -> list[dict[str, Any]]:
        try:
            raw = await self._fetch_fires()
        except Exception as err:  # noqa: BLE001 - surfaced to HA as UpdateFailed
            raise UpdateFailed(f"Error fetching focs.cat data: {err}") from err

        matches: list[dict[str, Any]] = []
        for f in raw:
            lat, lon = _to_float(f.get("latitude")), _to_float(f.get("longitude"))
            if lat is None or lon is None:
                continue
            if not self._include_all and (f.get("status") or "").lower() != "actiu":
                continue
            dist = haversine_km(lat, lon, self._lat, self._lon)
            if dist <= self._radius:
                matches.append(normalize_fire(f, dist))

        matches.sort(key=lambda x: x["distance_km"])
        return matches
