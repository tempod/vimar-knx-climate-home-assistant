"""Costanti per l'integrazione Vimar KNX Climate."""

from __future__ import annotations

DOMAIN = "vimar_knx_climate"

# --- Entità sorgente ------------------------------------------------------
CONF_NAME = "name"
CONF_CURRENT_TEMP = "current_temperature_entity"
CONF_MODE = "mode_entity"
CONF_SEASON = "season_entity"
CONF_FAN = "fan_entity"
CONF_TEMP_SUMMER = "summer_temp_entity"
CONF_TEMP_WINTER = "winter_temp_entity"
CONF_TEMP_AUTO = "auto_temp_entity"

# --- Etichette delle opzioni dei select KNX -------------------------------
# Sono configurabili perché dipendono da come l'utente ha scritto knx.yaml.
CONF_OPT_OFF = "option_off"
CONF_OPT_AUTO = "option_auto"
CONF_OPT_MANUAL = "option_manual"
CONF_OPT_TIMED = "option_timed"
CONF_OPT_COOLING = "option_cooling"
CONF_OPT_HEATING = "option_heating"

DEFAULT_OPT_OFF = "OFF"
DEFAULT_OPT_AUTO = "Automatico"
DEFAULT_OPT_MANUAL = "Manuale"
DEFAULT_OPT_TIMED = "A Tempo"
DEFAULT_OPT_COOLING = "Raffrescamento"
DEFAULT_OPT_HEATING = "Riscaldamento"

DEFAULT_NAME = "Termostato Vimar"

# --- Mappatura verso i valori standard di Home Assistant ------------------
# Il frontend disegna le icone solo per un elenco chiuso di valori di
# fan_mode e preset_mode. Qualsiasi altro valore diventa un pallino.
CONF_STANDARD_FAN_MODES = "standard_fan_modes"
CONF_PRESET_AUTO_AS = "preset_auto_as"
CONF_PRESET_MANUAL_AS = "preset_manual_as"
CONF_PRESET_TIMED_AS = "preset_timed_as"

KEEP_ORIGINAL = "keep_original"

DEFAULT_STANDARD_FAN_MODES = True
DEFAULT_PRESET_AUTO_AS = "home"
DEFAULT_PRESET_MANUAL_AS = "comfort"
DEFAULT_PRESET_TIMED_AS = "boost"

# Preset riconosciuti dal frontend, con la relativa icona.
STANDARD_PRESETS: tuple[str, ...] = (
    "none",       # mdi:circle-off-outline
    "eco",        # mdi:leaf
    "away",       # mdi:account-arrow-right
    "boost",      # mdi:rocket-launch
    "comfort",    # mdi:sofa
    "home",       # mdi:home
    "sleep",      # mdi:power-sleep
    "activity",   # mdi:motion-sensor
)

PRESET_SELECTOR_OPTIONS: tuple[str, ...] = (KEEP_ORIGINAL,) + STANDARD_PRESETS

# Velocità ventola riconosciute dal frontend:
# off, on, auto, low (fan-speed-1), medium (fan-speed-2), high (fan-speed-3),
# middle, focus, diffuse.
FAN_NORMALIZATION: dict[str, str] = {
    "off": "off",
    "spento": "off",
    "on": "on",
    "acceso": "on",
    "auto": "auto",
    "automatico": "auto",
    "automatica": "auto",
    "low": "low",
    "bassa": "low",
    "basso": "low",
    "min": "low",
    "minima": "low",
    "v1": "low",
    "1": "low",
    "med": "medium",
    "mid": "medium",
    "medium": "medium",
    "media": "medium",
    "medio": "medium",
    "middle": "medium",
    "v2": "medium",
    "2": "medium",
    "high": "high",
    "alta": "high",
    "alto": "high",
    "max": "high",
    "massima": "high",
    "v3": "high",
    "3": "high",
}

# --- Fallback per i limiti di temperatura ---------------------------------
DEFAULT_MIN_TEMP = 5.0
DEFAULT_MAX_TEMP = 35.0
DEFAULT_TEMP_STEP = 0.1

ATTR_RAW_MODE = "vimar_modalita"
ATTR_RAW_SEASON = "vimar_stagione"
ATTR_ACTIVE_SETPOINT = "setpoint_attivo"
