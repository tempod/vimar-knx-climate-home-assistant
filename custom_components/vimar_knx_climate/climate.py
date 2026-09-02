"""Entità climate per termostati Vimar esposti via KNX."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_TEMPERATURE,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfTemperature,
)
from homeassistant.core import Event, HomeAssistant, State, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    ATTR_ACTIVE_SETPOINT,
    ATTR_RAW_MODE,
    ATTR_RAW_SEASON,
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
    DEFAULT_MAX_TEMP,
    DEFAULT_MIN_TEMP,
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
    DEFAULT_TEMP_STEP,
    DOMAIN,
    FAN_NORMALIZATION,
    KEEP_ORIGINAL,
)

_LOGGER = logging.getLogger(__name__)

INVALID_STATES = (None, STATE_UNKNOWN, STATE_UNAVAILABLE, "")

# Nomi di dominio/servizio usati come letterali: fanno parte dell'API pubblica
# dei servizi di Home Assistant e non cambiano tra le versioni.
NUMBER_DOMAIN = "number"
SERVICE_SET_VALUE = "set_value"
ATTR_VALUE = "value"

SELECT_DOMAIN = "select"
SERVICE_SELECT_OPTION = "select_option"
ATTR_OPTION = "option"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Crea l'entità climate a partire dalla config entry."""
    async_add_entities([VimarKnxClimate(entry)])


class VimarKnxClimate(ClimateEntity):
    """Aggrega sensor + select + number KNX in un'unica entità climate."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_should_poll = False
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = DEFAULT_TEMP_STEP

    def __init__(self, entry: ConfigEntry) -> None:
        """Inizializza l'entità leggendo data + options."""
        self._entry = entry
        conf: dict[str, Any] = {**entry.data, **entry.options}
        self._conf = conf

        self._src_current_temp: str | None = conf.get(CONF_CURRENT_TEMP)
        self._src_mode: str | None = conf.get(CONF_MODE)
        self._src_season: str | None = conf.get(CONF_SEASON)
        self._src_fan: str | None = conf.get(CONF_FAN)
        self._src_summer: str | None = conf.get(CONF_TEMP_SUMMER)
        self._src_winter: str | None = conf.get(CONF_TEMP_WINTER)
        self._src_auto: str | None = conf.get(CONF_TEMP_AUTO)

        self._opt_off: str = conf.get(CONF_OPT_OFF, DEFAULT_OPT_OFF)
        self._opt_auto: str = conf.get(CONF_OPT_AUTO, DEFAULT_OPT_AUTO)
        self._opt_manual: str = conf.get(CONF_OPT_MANUAL, DEFAULT_OPT_MANUAL)
        self._opt_timed: str = conf.get(CONF_OPT_TIMED, DEFAULT_OPT_TIMED)
        self._opt_cooling: str = conf.get(CONF_OPT_COOLING, DEFAULT_OPT_COOLING)
        self._opt_heating: str = conf.get(CONF_OPT_HEATING, DEFAULT_OPT_HEATING)

        self._standard_fan: bool = conf.get(
            CONF_STANDARD_FAN_MODES, DEFAULT_STANDARD_FAN_MODES
        )
        self._preset_pairs: list[tuple[str, str]] = self._build_preset_pairs(conf)

        # Modalità da ripristinare quando si riaccende il termostato.
        self._last_active_mode: str = self._opt_manual

        name: str = conf.get(CONF_NAME, entry.title or DEFAULT_NAME)
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=name,
            manufacturer="Vimar",
            model="Termostato KNX",
        )

        features = ClimateEntityFeature.TARGET_TEMPERATURE
        features |= ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF
        features |= ClimateEntityFeature.PRESET_MODE
        if self._src_fan:
            features |= ClimateEntityFeature.FAN_MODE
        self._attr_supported_features = features

    # ------------------------------------------------------------------
    # Mappatura verso i valori standard di Home Assistant
    # ------------------------------------------------------------------

    def _build_preset_pairs(self, conf: dict[str, Any]) -> list[tuple[str, str]]:
        """Costruisce le coppie (valore esposto a HA, opzione Vimar).

        I preset standard hanno un'icona nel frontend; le etichette Vimar no.
        Se due profili venissero mappati sullo stesso preset standard, la
        traduzione viene disattivata per tutti per non perdere informazione.
        """
        sources = (
            (self._opt_auto, conf.get(CONF_PRESET_AUTO_AS, DEFAULT_PRESET_AUTO_AS)),
            (
                self._opt_manual,
                conf.get(CONF_PRESET_MANUAL_AS, DEFAULT_PRESET_MANUAL_AS),
            ),
            (self._opt_timed, conf.get(CONF_PRESET_TIMED_AS, DEFAULT_PRESET_TIMED_AS)),
        )

        exposed = [
            vimar if target in (None, KEEP_ORIGINAL) else target
            for vimar, target in sources
        ]

        if len(set(exposed)) != len(exposed):
            _LOGGER.warning(
                "Mappatura dei preset ambigua (%s): uso le etichette Vimar originali",
                exposed,
            )
            return [(vimar, vimar) for vimar, _ in sources]

        return [(shown, vimar) for shown, (vimar, _) in zip(exposed, sources)]

    @property
    def _fan_map(self) -> dict[str, str]:
        """Coppie (valore esposto a HA, opzione del select KNX) per la ventola."""
        options = self._options_of(self._src_fan)
        if not options or not self._standard_fan:
            return {option: option for option in options}

        mapped: dict[str, str] = {}
        for option in options:
            standard = FAN_NORMALIZATION.get(option.strip().lower())
            mapped[standard or option] = option

        if len(mapped) != len(options):
            _LOGGER.warning(
                "Velocità ventola ambigue dopo la normalizzazione (%s): "
                "uso le etichette originali",
                options,
            )
            return {option: option for option in options}

        return mapped

    # ------------------------------------------------------------------
    # Ciclo di vita
    # ------------------------------------------------------------------

    async def async_added_to_hass(self) -> None:
        """Si iscrive ai cambi di stato delle entità sorgente."""
        await super().async_added_to_hass()

        sources = [
            e
            for e in (
                self._src_current_temp,
                self._src_mode,
                self._src_season,
                self._src_fan,
                self._src_summer,
                self._src_winter,
                self._src_auto,
            )
            if e
        ]

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, sources, self._async_source_changed
            )
        )
        self._remember_active_mode()
        self._log_source_diagnostics()

    @callback
    def _log_source_diagnostics(self) -> None:
        """Segnala le sorgenti che non espongono quello che ci si aspetta."""
        for label, entity_id in (
            ("ventola", self._src_fan),
            ("modalità", self._src_mode),
            ("stagione", self._src_season),
        ):
            if not entity_id:
                continue
            if self.hass.states.get(entity_id) is None:
                _LOGGER.warning(
                    "L'entità %s configurata per la %s non esiste: "
                    "controlla knx.yaml e il nome dell'entità",
                    entity_id,
                    label,
                )
            elif not self._options_of(entity_id):
                _LOGGER.warning(
                    "L'entità %s (%s) non espone alcuna opzione: "
                    "il relativo comando non comparirà sulla card",
                    entity_id,
                    label,
                )

    @callback
    def _async_source_changed(self, event: Event) -> None:
        """Propaga il cambio di stato di una sorgente."""
        self._remember_active_mode()
        self.async_write_ha_state()

    @callback
    def _remember_active_mode(self) -> None:
        """Memorizza l'ultima modalità diversa da OFF."""
        raw = self._raw_state(self._src_mode)
        if raw is not None and raw != self._opt_off:
            self._last_active_mode = raw

    # ------------------------------------------------------------------
    # Lettura stati sorgente
    # ------------------------------------------------------------------

    def _state_obj(self, entity_id: str | None) -> State | None:
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in INVALID_STATES:
            return None
        return state

    def _raw_state(self, entity_id: str | None) -> str | None:
        state = self._state_obj(entity_id)
        return state.state if state else None

    def _float_state(self, entity_id: str | None) -> float | None:
        state = self._state_obj(entity_id)
        if state is None:
            return None
        try:
            return float(state.state)
        except (TypeError, ValueError):
            _LOGGER.debug("Valore non numerico da %s: %s", entity_id, state.state)
            return None

    def _attributes_of(self, entity_id: str | None) -> dict[str, Any]:
        """Attributi dell'entità, anche quando lo stato non è ancora noto.

        Le opzioni di un select KNX e i limiti di un number derivano dalla
        configurazione, non dal bus: esistono già prima che arrivi la prima
        risposta di stato. Filtrarli in base allo stato farebbe sparire le
        velocità della ventola finché il termostato non trasmette.
        """
        if not entity_id:
            return {}
        state = self.hass.states.get(entity_id)
        return dict(state.attributes) if state else {}

    def _options_of(self, entity_id: str | None) -> list[str]:
        return list(self._attributes_of(entity_id).get("options") or [])

    # ------------------------------------------------------------------
    # Setpoint attivo
    # ------------------------------------------------------------------

    @property
    def _active_setpoint_entity(self) -> str | None:
        """Determina quale entità number rappresenta il setpoint corrente.

        In modalità Automatico il termostato Vimar usa il setpoint dedicato
        ("Temp Auto"); altrimenti usa il setpoint estivo o invernale a seconda
        della stagione impostata.
        """
        mode = self._raw_state(self._src_mode)
        if mode == self._opt_auto and self._src_auto:
            return self._src_auto

        season = self._raw_state(self._src_season)
        if season == self._opt_cooling and self._src_summer:
            return self._src_summer
        if season == self._opt_heating and self._src_winter:
            return self._src_winter

        # Fallback: prima entità disponibile.
        return self._src_winter or self._src_summer or self._src_auto

    # ------------------------------------------------------------------
    # Proprietà climate
    # ------------------------------------------------------------------

    @property
    def available(self) -> bool:
        """Indisponibile solo se le entità sorgente mancano o sono offline.

        Uno stato ancora sconosciuto (KNX non ha ancora risposto alla prima
        lettura) non è un buon motivo per nascondere l'intero termostato.
        """
        for entity_id in (self._src_mode, self._src_current_temp):
            state = self.hass.states.get(entity_id) if entity_id else None
            if state is None or state.state == STATE_UNAVAILABLE:
                return False
        return True

    @property
    def current_temperature(self) -> float | None:
        """Temperatura misurata dalla sonda."""
        return self._float_state(self._src_current_temp)

    @property
    def target_temperature(self) -> float | None:
        """Setpoint attualmente in uso."""
        return self._float_state(self._active_setpoint_entity)

    @property
    def min_temp(self) -> float:
        """Limite minimo, letto dall'entità number attiva."""
        value = self._attributes_of(self._active_setpoint_entity).get("min")
        return float(value) if value is not None else DEFAULT_MIN_TEMP

    @property
    def max_temp(self) -> float:
        """Limite massimo, letto dall'entità number attiva."""
        value = self._attributes_of(self._active_setpoint_entity).get("max")
        return float(value) if value is not None else DEFAULT_MAX_TEMP

    @property
    def target_temperature_step(self) -> float:
        """Passo, letto dall'entità number attiva."""
        value = self._attributes_of(self._active_setpoint_entity).get("step")
        return float(value) if value is not None else DEFAULT_TEMP_STEP

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Modalità disponibili, in base alle entità configurate."""
        modes = [HVACMode.OFF]
        if self._src_season:
            modes.extend([HVACMode.HEAT, HVACMode.COOL])
        elif self._src_summer and not self._src_winter:
            modes.append(HVACMode.COOL)
        else:
            modes.append(HVACMode.HEAT)
        return modes

    @property
    def hvac_mode(self) -> HVACMode | None:
        """OFF se la modalità Vimar è OFF, altrimenti dipende dalla stagione."""
        mode = self._raw_state(self._src_mode)
        if mode is None:
            return None
        if mode == self._opt_off:
            return HVACMode.OFF

        season = self._raw_state(self._src_season)
        if season == self._opt_cooling:
            return HVACMode.COOL
        if season == self._opt_heating:
            return HVACMode.HEAT

        # Nessun select stagione configurato.
        return HVACMode.COOL if HVACMode.COOL in self.hvac_modes else HVACMode.HEAT

    @property
    def preset_modes(self) -> list[str]:
        """Profili disponibili, già tradotti nei valori standard di HA."""
        available = self._options_of(self._src_mode)
        if not available:
            return [shown for shown, _ in self._preset_pairs]
        return [shown for shown, vimar in self._preset_pairs if vimar in available]

    @property
    def preset_mode(self) -> str | None:
        """Profilo corrente; None quando il termostato è spento."""
        mode = self._raw_state(self._src_mode)
        if mode is None or mode == self._opt_off:
            return None
        for shown, vimar in self._preset_pairs:
            if vimar == mode:
                return shown
        return mode

    @property
    def fan_modes(self) -> list[str] | None:
        """Velocità disponibili, già tradotte nei valori standard di HA."""
        if not self._src_fan:
            return None
        return list(self._fan_map) or None

    @property
    def fan_mode(self) -> str | None:
        """Velocità ventola corrente."""
        raw = self._raw_state(self._src_fan)
        if raw is None:
            return None
        for shown, option in self._fan_map.items():
            if option == raw:
                return shown
        return raw

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Espone i valori grezzi, utili per debug e automazioni."""
        return {
            ATTR_RAW_MODE: self._raw_state(self._src_mode),
            ATTR_RAW_SEASON: self._raw_state(self._src_season),
            ATTR_ACTIVE_SETPOINT: self._active_setpoint_entity,
        }

    # ------------------------------------------------------------------
    # Comandi
    # ------------------------------------------------------------------

    async def _async_select(self, entity_id: str | None, option: str) -> None:
        """Chiama select.select_option sull'entità KNX indicata."""
        if not entity_id:
            return
        valid = self._options_of(entity_id)
        if valid and option not in valid:
            _LOGGER.warning(
                "Opzione '%s' non disponibile su %s (opzioni: %s). "
                "Controlla le etichette configurate nell'integrazione.",
                option,
                entity_id,
                valid,
            )
            return
        await self.hass.services.async_call(
            SELECT_DOMAIN,
            SERVICE_SELECT_OPTION,
            {ATTR_ENTITY_ID: entity_id, ATTR_OPTION: option},
            blocking=True,
            context=self._context,
        )

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Scrive il setpoint sull'entità number attiva."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        entity_id = self._active_setpoint_entity
        if not entity_id:
            _LOGGER.warning("Nessuna entità di setpoint configurata")
            return

        await self.hass.services.async_call(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: float(temperature)},
            blocking=True,
            context=self._context,
        )

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """OFF spegne il termostato; HEAT/COOL cambiano stagione e riaccendono."""
        if hvac_mode == HVACMode.OFF:
            await self._async_select(self._src_mode, self._opt_off)
            return

        if self._src_season:
            season = (
                self._opt_cooling if hvac_mode == HVACMode.COOL else self._opt_heating
            )
            await self._async_select(self._src_season, season)

        # Se era spento, ripristina l'ultimo profilo attivo.
        if self._raw_state(self._src_mode) == self._opt_off:
            await self._async_select(self._src_mode, self._last_active_mode)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Imposta il profilo, ritraducendolo nell'etichetta Vimar."""
        target = next(
            (vimar for shown, vimar in self._preset_pairs if shown == preset_mode),
            preset_mode,
        )
        await self._async_select(self._src_mode, target)

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Imposta la velocità, ritraducendola nell'opzione del select KNX."""
        target = self._fan_map.get(fan_mode, fan_mode)
        await self._async_select(self._src_fan, target)

    async def async_turn_off(self) -> None:
        """Spegne il termostato."""
        await self.async_set_hvac_mode(HVACMode.OFF)

    async def async_turn_on(self) -> None:
        """Riaccende il termostato sull'ultimo profilo usato."""
        await self._async_select(self._src_mode, self._last_active_mode)
