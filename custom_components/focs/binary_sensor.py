"""Binary sensor: is there a fire in range right now."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FocsCoordinator, PlansCoordinator, plans_key
from .entity import focs_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: FocsCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[BinarySensorEntity] = [FocsNearbyBinarySensor(coordinator, entry)]
    plans: PlansCoordinator | None = hass.data[DOMAIN].get(plans_key(entry))
    if plans is not None:
        entities.append(CivilProtectionBinarySensor(plans, entry))
    async_add_entities(entities)


class FocsNearbyBinarySensor(CoordinatorEntity[FocsCoordinator], BinarySensorEntity):
    """On when at least one fire is within the configured radius."""

    _attr_has_entity_name = True
    _attr_name = "Fire nearby"
    _attr_device_class = BinarySensorDeviceClass.SAFETY

    def __init__(self, coordinator: FocsCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_fire_nearby"
        self._attr_device_info = focs_device_info(entry)

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict:
        fires = self.coordinator.data or []
        nearest = fires[0] if fires else None
        return {
            "count": len(fires),
            "nearest_distance_km": nearest["distance_km"] if nearest else None,
            "nearest_location": nearest["location"] if nearest else None,
            # Full per-fire detail (location, resources, description, media, …).
            "fires": fires,
        }


class CivilProtectionBinarySensor(
    CoordinatorEntity[PlansCoordinator], BinarySensorEntity
):
    """On when any Catalan civil protection plan is in pre-alert or higher."""

    _attr_has_entity_name = True
    _attr_name = "Civil protection plan active"
    _attr_device_class = BinarySensorDeviceClass.SAFETY
    _attr_icon = "mdi:shield-alert"

    def __init__(self, coordinator: PlansCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_civil_protection"
        self._attr_device_info = focs_device_info(entry)

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict:
        plans = self.coordinator.data or []
        top = plans[0] if plans else None
        return {
            "count": len(plans),
            "highest_phase": top["phase"] if top else None,
            # Full per-plan detail (phase, since, description, bulletin_url, …).
            "plans": plans,
        }
