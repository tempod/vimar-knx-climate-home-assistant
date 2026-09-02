"""Config flow per Vimar KNX Climate."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_CURRENT_TEMP,
    CONF_FAN,
    CONF_MODE,
    CONF_NAME,
    CONF_OPT_AUTO,
    CONF_OPT_COOLING,
    CONF_OPT_HEATING,
    CONF_OPT_MANUAL,
    CONF_OPT_OFF,
    CONF_OPT_TIMED,
    CONF_PRESET_AUTO_AS,
    CONF_PRESET_MANUAL_AS,
    CONF_PRESET_TIMED_AS,
    CONF_SEASON,
    CONF_STANDARD_FAN_MODES,
    CONF_TEMP_AUTO,
    CONF_TEMP_SUMMER,
    CONF_TEMP_WINTER,
    DEFAULT_NAME,
    DEFAULT_OPT_AUTO,
    DEFAULT_OPT_COOLING,
    DEFAULT_OPT_HEATING,
    DEFAULT_OPT_MANUAL,
    DEFAULT_OPT_OFF,
    DEFAULT_OPT_TIMED,
    DEFAULT_PRESET_AUTO_AS,
    DEFAULT_PRESET_MANUAL_AS,
    DEFAULT_PRESET_TIMED_AS,
    DEFAULT_STANDARD_FAN_MODES,
    DOMAIN,
    PRESET_SELECTOR_OPTIONS,
)


def _entity(domain: str, **kwargs: Any) -> selector.EntitySelector:
    return selector.EntitySelector(
        selector.EntitySelectorConfig(domain=domain, **kwargs)
    )


def _marker(
    required: bool, key: str, defaults: dict[str, Any], fallback: Any = None
) -> vol.Marker:
    """Crea un marker voluptuous precompilato con il valore corrente."""
    value = defaults.get(key, fallback)
    description = {"suggested_value": value} if value is not None else None
    cls = vol.Required if required else vol.Optional
    return cls(key, description=description)


def build_schema(defaults: dict[str, Any], include_name: bool = True) -> vol.Schema:
    """Costruisce lo schema del form, precompilato con i valori esistenti."""
    fields: dict[Any, Any] = {}

    if include_name:
        fields[_marker(True, CONF_NAME, defaults, DEFAULT_NAME)] = (
            selector.TextSelector()
        )

    fields[_marker(True, CONF_CURRENT_TEMP, defaults)] = _entity("sensor")
    fields[_marker(True, CONF_MODE, defaults)] = _entity("select")
    fields[_marker(False, CONF_SEASON, defaults)] = _entity("select")
    fields[_marker(False, CONF_FAN, defaults)] = _entity("select")
    fields[_marker(False, CONF_TEMP_SUMMER, defaults)] = _entity("number")
    fields[_marker(False, CONF_TEMP_WINTER, defaults)] = _entity("number")
    fields[_marker(False, CONF_TEMP_AUTO, defaults)] = _entity("number")

    for key, fallback in (
        (CONF_OPT_OFF, DEFAULT_OPT_OFF),
        (CONF_OPT_AUTO, DEFAULT_OPT_AUTO),
        (CONF_OPT_MANUAL, DEFAULT_OPT_MANUAL),
        (CONF_OPT_TIMED, DEFAULT_OPT_TIMED),
        (CONF_OPT_COOLING, DEFAULT_OPT_COOLING),
        (CONF_OPT_HEATING, DEFAULT_OPT_HEATING),
    ):
        fields[_marker(True, key, defaults, fallback)] = selector.TextSelector()

    # Mappatura sui valori standard di Home Assistant, per avere le icone.
    fields[
        _marker(True, CONF_STANDARD_FAN_MODES, defaults, DEFAULT_STANDARD_FAN_MODES)
    ] = selector.BooleanSelector()

    for key, fallback in (
        (CONF_PRESET_AUTO_AS, DEFAULT_PRESET_AUTO_AS),
        (CONF_PRESET_MANUAL_AS, DEFAULT_PRESET_MANUAL_AS),
        (CONF_PRESET_TIMED_AS, DEFAULT_PRESET_TIMED_AS),
    ):
        fields[_marker(True, key, defaults, fallback)] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=list(PRESET_SELECTOR_OPTIONS),
                mode=selector.SelectSelectorMode.DROPDOWN,
                translation_key="standard_preset",
            )
        )

    return vol.Schema(fields)


class VimarKnxClimateConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestisce la configurazione iniziale."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Primo e unico passo della configurazione."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if not _at_least_one_setpoint(user_input):
                errors["base"] = "no_setpoint"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=build_schema(user_input or {}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> VimarKnxClimateOptionsFlow:
        """Restituisce il flow delle opzioni."""
        return VimarKnxClimateOptionsFlow()


class VimarKnxClimateOptionsFlow(config_entries.OptionsFlow):
    """Permette di modificare la configurazione dopo l'installazione."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Modifica delle opzioni."""
        errors: dict[str, str] = {}
        current = {**self.config_entry.data, **self.config_entry.options}

        if user_input is not None:
            if not _at_least_one_setpoint(user_input):
                errors["base"] = "no_setpoint"
            else:
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=build_schema(user_input or current, include_name=False),
            errors=errors,
        )


def _at_least_one_setpoint(data: dict[str, Any]) -> bool:
    """Serve almeno un'entità number per poter impostare la temperatura."""
    return any(
        data.get(key)
        for key in (CONF_TEMP_SUMMER, CONF_TEMP_WINTER, CONF_TEMP_AUTO)
    )
