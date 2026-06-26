# focs.cat Fire Alerts — Home Assistant integration

Polls the [focs.cat](https://focs.cat) backend and alerts you to wildfires near
a location. Built to be installed via [HACS](https://hacs.xyz).

## What you get

- **Entities** (for dashboards / state automations):
  - `binary_sensor.<name>_fire_nearby` — on when ≥1 fire is in range. Attributes
    include `count`, `nearest_distance_km`, `nearest_location` and the full
    `fires` list.
  - `sensor.<name>_fires_in_range` — count of in-range fires.
  - `sensor.<name>_nearest_fire_distance` — km to the closest fire.
- **Events** (for per-fire notifications): `focs_fire_detected` is fired on the
  HA event bus for each newly-detected fire, with this data:

  ```
  id, status, type, location, latitude, longitude, ops,
  distance_km, when_last_time, url
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
```
