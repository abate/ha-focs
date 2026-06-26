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

# Defaults (area: Santa Coloma de Gramenet / Badalona / Parc de la Serralada).
DEFAULT_LATITUDE = 41.4517
DEFAULT_LONGITUDE = 2.2080
DEFAULT_RADIUS_KM = 6.0
DEFAULT_SCAN_INTERVAL = 5  # minutes
DEFAULT_INCLUDE_ALL = False

# Event fired when a new (or newly-active) fire is detected in range.
EVENT_FIRE_DETECTED = "focs_fire_detected"
