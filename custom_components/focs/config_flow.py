"""Config and options flow for the focs.cat fire integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback

from .const import (
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
    DOMAIN,
)


def _schema(defaults: dict[str, Any], hass_lat: float, hass_lon: float) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_LATITUDE,
                default=defaults.get(CONF_LATITUDE, hass_lat),
            ): vol.Coerce(float),
            vol.Required(
                CONF_LONGITUDE,
                default=defaults.get(CONF_LONGITUDE, hass_lon),
            ): vol.Coerce(float),
            vol.Required(
                CONF_RADIUS_KM,
                default=defaults.get(CONF_RADIUS_KM, DEFAULT_RADIUS_KM),
            ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=200)),
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=1440)),
            vol.Required(
                CONF_INCLUDE_ALL,
                default=defaults.get(CONF_INCLUDE_ALL, DEFAULT_INCLUDE_ALL),
            ): bool,
        }
    )


class FocsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Initial setup flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="focs.cat Fire Alerts", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(
                {},
                self.hass.config.latitude or DEFAULT_LATITUDE,
                self.hass.config.longitude or DEFAULT_LONGITUDE,
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        return FocsOptionsFlow(entry)


class FocsOptionsFlow(OptionsFlow):
    """Allow editing radius, interval, etc. after setup."""

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {**self._entry.data, **self._entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=_schema(
                current,
                current.get(CONF_LATITUDE, DEFAULT_LATITUDE),
                current.get(CONF_LONGITUDE, DEFAULT_LONGITUDE),
            ),
        )
