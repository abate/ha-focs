"""Sensors: count of in-range fires and nearest-fire distance."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FocsCoordinator, PlansCoordinator, phase_key, plans_key
from .entity import focs_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: FocsCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        FocsCountSensor(coordinator, entry),
        FocsNearestSensor(coordinator, entry),
    ]
    plans: PlansCoordinator | None = hass.data[DOMAIN].get(plans_key(entry))
    if plans is not None:
        entities.append(CivilProtectionPhaseSensor(plans, entry))
    async_add_entities(entities)


class FocsCountSensor(CoordinatorEntity[FocsCoordinator], SensorEntity):
    """Number of fires currently within the configured radius."""

    _attr_has_entity_name = True
    _attr_name = "Fires in range"
    _attr_icon = "mdi:fire"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: FocsCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_count"
        self._attr_device_info = focs_device_info(entry)

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
        self._attr_device_info = focs_device_info(entry)

    @property
    def native_value(self) -> float | None:
        fires = self.coordinator.data or []
        return fires[0].get("distance_km") if fires else None


class CivilProtectionPhaseSensor(CoordinatorEntity[PlansCoordinator], SensorEntity):
    """Highest phase among the active civil protection plans."""

    _attr_has_entity_name = True
    _attr_name = "Civil protection phase"
    _attr_icon = "mdi:shield-alert-outline"
    _attr_device_class = SensorDeviceClass.ENUM

    def __init__(self, coordinator: PlansCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_options = ["none", "prealerta", "alerta", "emergencia"]
        self._attr_unique_id = f"{entry.entry_id}_civil_protection_phase"
        self._attr_device_info = focs_device_info(entry)

    @property
    def native_value(self) -> str:
        plans = self.coordinator.data or []
        key = phase_key(plans[0]["phase"]).lower() if plans else "none"
        return key if key in self._attr_options else "none"

    @property
    def extra_state_attributes(self) -> dict:
        return {"plans": [p["plan"] for p in self.coordinator.data or []]}
