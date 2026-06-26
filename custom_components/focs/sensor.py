"""Sensors: count of in-range fires and nearest-fire distance."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FocsCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: FocsCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            FocsCountSensor(coordinator, entry),
            FocsNearestSensor(coordinator, entry),
        ]
    )


class FocsCountSensor(CoordinatorEntity[FocsCoordinator], SensorEntity):
    """Number of fires currently within the configured radius."""

    _attr_has_entity_name = True
    _attr_name = "Fires in range"
    _attr_icon = "mdi:fire"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: FocsCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_count"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data or [])


class FocsNearestSensor(CoordinatorEntity[FocsCoordinator], SensorEntity):
    """Distance to the nearest in-range fire (km)."""

    _attr_has_entity_name = True
    _attr_name = "Nearest fire distance"
    _attr_icon = "mdi:map-marker-distance"
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: FocsCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_nearest"

    @property
    def native_value(self) -> float | None:
        fires = self.coordinator.data or []
        return fires[0].get("_distance_km") if fires else None
