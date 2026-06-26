# focs.cat Fire Alerts — Home Assistant integration

Polls the [focs.cat](https://focs.cat) backend and alerts you to wildfires near
a location. Built to be installed via [HACS](https://hacs.xyz).

## What you get

- **Entities** (for dashboards / state automations):
  - `binary_sensor.<name>_fire_nearby` — on when ≥1 fire is in range. Attributes:
    `count`, `nearest_distance_km`, `nearest_location`, and `fires` — a list of
    the full per-fire detail (see fields below).
  - `sensor.<name>_fires_in_range` — count of in-range fires.
  - `sensor.<name>_nearest_fire_distance` — km to the closest fire.
  - **`geo_location` entities** — one per in-range fire, created/removed as fires
    come and go. They plot automatically on HA's **Map** card via
    `geo_location_sources: [focs]`, and each marker carries the full detail as
    attributes.
- **Events** (for per-fire notifications): `focs_fire_detected` fires on the HA
  event bus for each newly-detected fire.

Every fire (event payload, `fires` attribute, and map-marker attributes) carries
the same normalized fields, derived from the focs.cat / bomberscat data:

```
id, status, type, location, latitude, longitude, distance_km,
ops, radius, fire_trucks, firefighters, helicopters, planes, burnt_area,
is_forest_fire, is_controlled, is_stabilized, is_extinguished,
description (bomberscat tweet text), tweet_url, media (photo/video URLs),
source, last_update (epoch ms), url (focs.cat fire page)
```

## Install (HACS)

1. HACS → ⋮ → **Custom repositories** → add this repo's URL, category
   **Integration**.
2. Install **focs.cat Fire Alerts**, then restart Home Assistant.
3. **Settings → Devices & Services → Add Integration → focs.cat Fire Alerts**.
   Set the center point (defaults to your HA location), radius, and scan
   interval.

## Get notified

The integration only emits events/entities — it does not send messages itself
(so you choose phone vs. Telegram vs. anything). A blueprint is bundled:

1. **Settings → Automations & Scenes → Blueprints → Import blueprint** is *not*
   needed — because the blueprint ships inside the integration it appears under
   **Create automation → focs.cat fire alert** after install/restart.
2. Pick your notify service (e.g. `notify.mobile_app_my_phone` or
   `notify.telegram`), optionally a minimum `ops` threshold, and save.

> Why a separate step? An integration cannot know *which* phone or Telegram chat
> to message, so the notify target must be chosen by you. The blueprint reduces
> that to a one-field form.

### Or write your own automation

```yaml
automation:
  - alias: Fire alert
    trigger:
      - platform: event
        event_type: focs_fire_detected
    action:
      - service: notify.mobile_app_my_phone
        data:
          title: "🔥 Fire {{ trigger.event.data.distance_km }} km away"
          message: >
            {{ trigger.event.data.status }} — {{ trigger.event.data.location }}
            {{ trigger.event.data.url }}
```

## Dashboard

### Custom card (no setup)

The integration ships a custom Lovelace card and **auto-registers it** — no HACS
frontend plugin, no Lovelace resource, no YAML to paste. After installing/updating
and restarting HA, add it from **Add card → search "focs.cat Fire card"**, or with
one line:

```yaml
type: custom:focs-fire-card
# title: Fires nearby      # optional
# entity: binary_sensor.…  # optional; auto-detected otherwise
```

It renders each in-range fire with status, distance, resources, the bomberscat
description and photo, and links to focs.cat and the source tweet. Pair it with a
built-in **Map** card (`geo_location_sources: [focs]`) for positions.

> If the card type is "not found" right after updating, hard-refresh the browser
> (Ctrl/Cmd-Shift-R) to clear the cached frontend.

### Full YAML view (alternative)

A ready view is in [`dashboard/focs_dashboard.yaml`](dashboard/focs_dashboard.yaml):
a Map, a glance of the summary sensors, and a Markdown card. Add it via
**Dashboard → Edit → ⋮ → Raw configuration editor** (paste under `views:`).
Adjust the entity IDs if your device name differs.

## Notes

- On startup the integration seeds the "already seen" set from the first poll,
  so you are not flooded with events for the existing backlog — only fires that
  appear *after* setup trigger `focs_fire_detected`.
- Distance is computed to a single center point. To cover several reference
  points (the original script used Santa Coloma / Badalona / the Parc de la
  Serralada), widen the radius, or add a second config entry per point.
- The anon Supabase key is the public one shipped in the focs.cat frontend. If
  focs.cat rotates it, update `ANON_KEY` in `const.py`.
- Repo is assumed at `github.com/abate/ha-focs`; update URLs in `manifest.json`
  and the blueprint `source_url` if you name it differently.
