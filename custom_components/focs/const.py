"""Constants for the focs.cat fire integration."""

from __future__ import annotations

DOMAIN = "focs"

# focs.cat backend (public Supabase REST endpoint). The anon key below is the
# one shipped in the site's frontend JS, so it is public.
SUPABASE_URL = "https://rycezpzfezvoahdqafjj.supabase.co"
ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ5Y2V6cHpmZXp2b2FoZHFhZmpqIiwicm9sZSI6"
    "ImFub24iLCJpYXQiOjE2ODM4MDcyMzgsImV4cCI6MTk5OTM4MzIzOH0."
    "FHfEQcrG0YT5vtZ7biV7c5ZUDG5hws51upgKomA1nDM"
)

# Configuration keys.
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_RADIUS_KM = "radius_km"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_INCLUDE_ALL = "include_all"
CONF_CIVIL_PROTECTION = "civil_protection"
CONF_WEATHER_ZONES = "weather_zones"

# Defaults (area: Santa Coloma de Gramenet / Badalona / Parc de la Serralada).
DEFAULT_LATITUDE = 41.4517
DEFAULT_LONGITUDE = 2.2080
DEFAULT_RADIUS_KM = 6.0
DEFAULT_SCAN_INTERVAL = 5  # minutes
DEFAULT_INCLUDE_ALL = False
DEFAULT_CIVIL_PROTECTION = True
# MeteoAlarm EMMA_ID of AEMET's "Litoral de Barcelona" warning zone. Empty
# string disables weather warnings.
DEFAULT_WEATHER_ZONES = "ES181"

# Event fired when a new (or newly-active) fire is detected in range.
EVENT_FIRE_DETECTED = "focs_fire_detected"

# Generalitat de Catalunya open data: civil protection plans currently in
# pre-alert, alert or emergency (Socrata dataset wj9c-j6vf, no auth). ES-Alert
# phone broadcasts are sent under one of these plans, so a plan entering a
# phase is the closest machine-readable proxy for an ES-Alert.
PLANS_URL = "https://analisi.transparenciacatalunya.cat/resource/wj9c-j6vf.json"
PLANS_PAGE_URL = "https://interior.gencat.cat/ca/arees_dactuacio/proteccio_civil/"

# Event fired when a civil protection plan is activated, changes phase, gets
# a new communiqué, or is deactivated.
EVENT_PLAN_CHANGED = "focs_civil_protection_plan"

# Phase ranking (accent-stripped, upper-case keys).
PHASE_RANK = {"PREALERTA": 1, "ALERTA": 2, "EMERGENCIA": 3}

# What each plan covers, for messages (the dataset only gives the acronym).
PLAN_RISKS = {
    "INFOCAT": "Incendis forestals",
    "INUNCAT": "Inundacions",
    "NEUCAT": "Nevades",
    "VENTCAT": "Vent",
    "SISMICAT": "Terratrèmols",
    "ALLAUCAT": "Allaus",
    "CAMCAT": "Contaminació marina",
    "PLASEQCAT": "Accidents en indústries químiques",
    "TRANSCAT": "Transport de mercaderies perilloses",
    "RADCAT": "Emergències radiològiques",
    "AEROCAT": "Accidents aeris",
    "PENTA": "Emergència nuclear (Tarragona)",
    "PROCICAT": "Pla territorial (calor, sequera, epidèmies, …)",
}

# MeteoAlarm (EUMETNET) Atom feed of AEMET's live warnings for Spain, per
# warning zone (EMMA_ID), no auth. Each entry links to its full CAP message,
# which carries the Spanish headline/description and the awareness parameters.
METEOALARM_FEED_URL = "https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-spain"
METEOALARM_PAGE_URL = "https://meteoalarm.org?geocode=EMMA_ID:{zone}"

# Event fired when a hazard's warning level in the watched zones changes:
# a warning is issued, its level changes, or it ends.
EVENT_WEATHER_WARNING = "focs_weather_warning"

# MeteoAlarm awareness levels (CAP severity as fallback).
WARNING_LEVELS = {2: "yellow", 3: "orange", 4: "red"}
SEVERITY_LEVEL = {"MODERATE": 2, "SEVERE": 3, "EXTREME": 4}
LEVEL_LABELS = {"yellow": "groc", "orange": "taronja", "red": "vermell"}

# MeteoAlarm awareness types, normalized (see normalize_hazard), with Catalan
# labels for messages.
HAZARD_LABELS = {
    "wind": "Vent",
    "snow_ice": "Neu i gel",
    "thunderstorm": "Tempestes",
    "fog": "Boira",
    "high_temperature": "Calor",
    "low_temperature": "Fred",
    "coastal_event": "Fenòmens costaners",
    "forest_fire": "Risc d'incendi",
    "avalanches": "Allaus",
    "rain": "Pluja",
    "flooding": "Inundacions",
    "rain_flood": "Pluja i inundacions",
}

# Custom Lovelace card, served and auto-registered by the integration.
CARD_URL = "/focs_frontend/focs-fire-card.js"
CARD_VERSION = "0.0.3"
