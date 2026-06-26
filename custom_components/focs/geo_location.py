"""Geo-location entities: one map marker per in-range fire.

These transient entities are created and removed as fires enter/leave the
configured radius, so HA's Map card (with geo_location_sources: [focs]) plots
the current fires automatically.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.geo_location import GeolocationEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FocsCoordinator

SOURCE = "focs"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: FocsCoordinator = hass.data[DOMAIN][entry.entry_id]
    manager = FocsGeoManager(hass, coordinator, async_add_entities)
    entry.async_on_unload(coordinator.async_add_listener(manager.sync))
    manager.sync()


class FocsGeoManager:
    """Keeps the set of geo_location entities in sync with the fire list."""

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: FocsCoordinator,
        async_add_entities: AddEntitiesCallback,
    ) -> None:
        self.hass = hass
        self.coordinator = coordinator
        self.async_add_entities = async_add_entities
        self.entities: dict[Any, FocsGeoEvent] = {}

    @callback
    def sync(self) -> None:
        current = {f.get("id") for f in (self.coordinator.data or [])}

        # Remove markers for fires no longer in range.
        for fire_id in list(self.entities):
            if fire_id not in current:
                entity = self.entities.pop(fire_id)
                self.hass.async_create_task(entity.async_remove(force_remove=True))

        # Add markers for newly in-range fires.
        new_entities = [
            FocsGeoEvent(self.coordinator, fire_id)
            for fire_id in current
            if fire_id not in self.entities
        ]
        for entity in new_entities:
            self.entities[entity.fire_id] = entity
        if new_entities:
            self.async_add_entities(new_entities)


class FocsGeoEvent(CoordinatorEntity[FocsCoordinator], GeolocationEvent):
    """A single fire as a map marker; reads live data from the coordinator."""

    _attr_icon = "mdi:fire"
    _attr_unit_of_measurement = UnitOfLength.KILOMETERS

    def __init__(self, coordinator: FocsCoordinator, fire_id: Any) -> None:
        super().__init__(coordinator)
        self.fire_id = fire_id
        self._attr_unique_id = f"focs_fire_{fire_id}"

    def _fire(self) -> dict[str, Any]:
        for f in self.coordinator.data or []:
            if f.get("id") == self.fire_id:
                return f
        return {}

    @property
    def source(self) -> str:
        return SOURCE

    @property
    def available(self) -> bool:
        return bool(self._fire())

    @property
    def name(self) -> str:
        return self._fire().get("location") or f"Fire {self.fire_id}"

    @property
    def latitude(self) -> float | None:
        return self._fire().get("latitude")

    @property
    def longitude(self) -> float | None:
        return self._fire().get("longitude")

    @property
    def distance(self) -> float | None:
        return self._fire().get("distance_km")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        f = self._fire()
        # Everything except the geometry already exposed as state/lat/long.
        return {
            k: v
            for k, v in f.items()
            if k not in ("latitude", "longitude", "distance_km")
        }
