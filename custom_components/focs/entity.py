"""Shared helpers for focs.cat entities."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN


def focs_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Group all entities of one config entry under a single device."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="focs.cat Fire Alerts",
        manufacturer="focs.cat",
        entry_type=DeviceEntryType.SERVICE,
        configuration_url="https://focs.cat/list",
    )
