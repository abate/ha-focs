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

from .const import (
    CARD_URL,
    CARD_VERSION,
    CONF_CIVIL_PROTECTION,
    CONF_WEATHER_ZONES,
    DEFAULT_CIVIL_PROTECTION,
    DEFAULT_WEATHER_ZONES,
    DOMAIN,
    EVENT_FIRE_DETECTED,
    EVENT_PLAN_CHANGED,
    EVENT_WEATHER_WARNING,
    HAZARD_LABELS,
    LEVEL_LABELS,
    WARNING_LEVELS,
)
from .coordinator import (
    FocsCoordinator,
    PlansCoordinator,
    WeatherCoordinator,
    plans_key,
    weather_key,
)

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


def _fire_event(
    hass: HomeAssistant, fire: dict[str, Any], change: str, previous_status: Any
) -> None:
    """Emit a focs_fire_detected event with the full fire dict plus change info.

    `change` is "new" (first time seen in range) or "status_change".
    `previous_status` is the prior status on a status change, else None.
    """
    data = dict(fire)
    data["change"] = change
    data["previous_status"] = previous_status
    hass.bus.async_fire(EVENT_FIRE_DETECTED, data)


def _plan_state(plan: dict[str, Any]) -> tuple:
    return (plan.get("phase"), plan.get("since"), plan.get("bulletin_url"))


def _plan_event(
    hass: HomeAssistant,
    plan: dict[str, Any],
    change: str,
    previous_phase: Any,
) -> None:
    """Emit a focs_civil_protection_plan event.

    `change` is "activated", "phase_change", "update" (same phase, new
    timestamp or bulletin) or "deactivated" (the plan left the dataset).
    """
    data = dict(plan)
    data["change"] = change
    data["previous_phase"] = previous_phase
    hass.bus.async_fire(EVENT_PLAN_CHANGED, data)


async def _setup_plans(hass: HomeAssistant, entry: ConfigEntry) -> PlansCoordinator:
    """Start the civil protection plans poller and its change events."""
    plans = PlansCoordinator(hass, entry)
    # Not first_refresh: the Generalitat portal being down must not stop the
    # fire alerts from loading. Entities show unavailable until it answers.
    await plans.async_refresh()
    last: dict[Any, dict[str, Any]] = {}

    @callback
    def _handle_plans() -> None:
        nonlocal last
        if not plans.last_update_success:
            return
        current = {p["id"]: p for p in plans.data}
        if plans.seen is not None:
            for pid, plan in current.items():
                if pid not in plans.seen:
                    _plan_event(hass, plan, "activated", None)
                elif plans.seen[pid] != _plan_state(plan):
                    prev = plans.seen[pid][0]
                    change = "phase_change" if prev != plan["phase"] else "update"
                    _plan_event(hass, plan, change, prev)
            for pid, state in plans.seen.items():
                if pid not in current:
                    gone = dict(last.get(pid) or {"id": pid, "plan": pid, "name": pid})
                    gone["active"] = False
                    _plan_event(hass, gone, "deactivated", state[0])
        plans.seen = {pid: _plan_state(p) for pid, p in current.items()}
        last = current

    entry.async_on_unload(plans.async_add_listener(_handle_plans))
    _handle_plans()  # seed from the first poll, if it succeeded
    return plans


def weather_zones(entry: ConfigEntry) -> set[str]:
    """Watched MeteoAlarm zones from the comma-separated option."""
    opts = {**entry.data, **entry.options}
    raw = opts.get(CONF_WEATHER_ZONES, DEFAULT_WEATHER_ZONES) or ""
    return {z.strip().upper() for z in raw.split(",") if z.strip()}


def _weather_event(
    hass: HomeAssistant,
    hazard: str,
    warnings: list[dict[str, Any]],
    change: str,
    previous_level: int,
) -> None:
    """Emit a focs_weather_warning event for one hazard.

    `change` is "issued" (no warning before), "level_change" or "ended".
    The top-level fields are those of the highest current warning for the
    hazard (none on "ended"); `warnings` lists all of them.
    """
    top = warnings[0] if warnings else {}
    level = top.get("level", 0)
    prev_name = WARNING_LEVELS.get(previous_level)
    data = dict(top)
    data.update(
        {
            "hazard": hazard,
            "hazard_label": HAZARD_LABELS.get(hazard, hazard),
            "level": level,
            "level_name": WARNING_LEVELS.get(level),
            "level_label": LEVEL_LABELS.get(WARNING_LEVELS.get(level)),
            "change": change,
            "previous_level": previous_level,
            "previous_level_name": prev_name,
            "previous_level_label": LEVEL_LABELS.get(prev_name),
            "warnings": warnings,
        }
    )
    hass.bus.async_fire(EVENT_WEATHER_WARNING, data)


async def _setup_weather(
    hass: HomeAssistant, entry: ConfigEntry, zones: set[str]
) -> WeatherCoordinator:
    """Start the MeteoAlarm poller and its per-hazard change events."""
    weather = WeatherCoordinator(hass, entry, zones)
    # Not first_refresh, for the same reason as the plans poller.
    await weather.async_refresh()

    @callback
    def _handle_weather() -> None:
        if not weather.last_update_success:
            return
        by_hazard: dict[str, list[dict[str, Any]]] = {}
        for w in weather.data:  # already sorted highest level first
            by_hazard.setdefault(w["hazard"], []).append(w)
        current = {h: ws[0]["level"] for h, ws in by_hazard.items()}
        if weather.seen is not None:
            for hazard, level in current.items():
                prev = weather.seen.get(hazard, 0)
                if level != prev:
                    change = "level_change" if prev else "issued"
                    _weather_event(hass, hazard, by_hazard[hazard], change, prev)
            for hazard, prev in weather.seen.items():
                if hazard not in current:
                    _weather_event(hass, hazard, [], "ended", prev)
        weather.seen = current

    entry.async_on_unload(weather.async_add_listener(_handle_weather))
    _handle_weather()  # seed from the first poll, if it succeeded
    return weather


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up focs.cat from a config entry."""
    await _register_frontend(hass)

    coordinator = FocsCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    # Seed last-seen statuses from the first refresh so we don't blast events
    # for the full backlog on startup; only fires that appear (or change status)
    # after setup trigger notifications.
    coordinator.seen = {f.get("id"): f.get("status") for f in coordinator.data}

    @callback
    def _handle_update() -> None:
        for fire in coordinator.data:
            fid = fire.get("id")
            if fid not in coordinator.seen:
                _fire_event(hass, fire, "new", None)
            elif coordinator.seen[fid] != fire.get("status"):
                _fire_event(hass, fire, "status_change", coordinator.seen[fid])
        coordinator.seen = {f.get("id"): f.get("status") for f in coordinator.data}

    entry.async_on_unload(coordinator.async_add_listener(_handle_update))

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    opts = {**entry.data, **entry.options}
    if opts.get(CONF_CIVIL_PROTECTION, DEFAULT_CIVIL_PROTECTION):
        hass.data[DOMAIN][plans_key(entry)] = await _setup_plans(hass, entry)
    if zones := weather_zones(entry):
        hass.data[DOMAIN][weather_key(entry)] = await _setup_weather(hass, entry, zones)
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
        hass.data[DOMAIN].pop(plans_key(entry), None)
        hass.data[DOMAIN].pop(weather_key(entry), None)
    return unloaded
