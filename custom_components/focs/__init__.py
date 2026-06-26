"""The focs.cat fire integration."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback

from .const import CARD_URL, CARD_VERSION, DOMAIN, EVENT_FIRE_DETECTED
from .coordinator import FocsCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.GEO_LOCATION,
]


async def _register_frontend(hass: HomeAssistant) -> None:
    """Serve and auto-load the custom Lovelace card (once per HA instance)."""
    store = hass.data.setdefault(DOMAIN, {})
    if store.get("_frontend_registered"):
        return
    card_file = Path(__file__).parent / "www" / "focs-fire-card.js"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(card_file), cache_headers=False)]
    )
    # Versioned query busts the browser cache when the card is updated.
    add_extra_js_url(hass, f"{CARD_URL}?v={CARD_VERSION}")
    store["_frontend_registered"] = True


def _fire_event(hass: HomeAssistant, fire: dict[str, Any]) -> None:
    """Emit a focs_fire_detected event carrying the full normalized fire dict."""
    hass.bus.async_fire(EVENT_FIRE_DETECTED, dict(fire))


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up focs.cat from a config entry."""
    await _register_frontend(hass)

    coordinator = FocsCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    # Seed known IDs from the first refresh so we don't blast events for the
    # full backlog on startup; only genuinely new fires trigger notifications.
    coordinator.known_ids = {f.get("id") for f in coordinator.data}

    @callback
    def _handle_update() -> None:
        for fire in coordinator.data:
            if fire.get("id") not in coordinator.known_ids:
                _fire_event(hass, fire)
        coordinator.known_ids = {f.get("id") for f in coordinator.data}

    entry.async_on_unload(coordinator.async_add_listener(_handle_update))

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded
