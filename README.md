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
  event bus when a fire **enters range** (`change: "new"`) and when a tracked
  fire's **status changes** (`change: "status_change"`, with `previous_status`
  set). See [When you get notified](#when-you-get-notified) for the details.

Every fire (event payload, `fires` attribute, and map-marker attributes) carries
the same normalized fields, derived from the focs.cat / bomberscat data:

```
id, status, type, location, latitude, longitude, distance_km,
ops, radius, fire_trucks, firefighters, helicopters, planes, burnt_area,
is_forest_fire, is_controlled, is_stabilized, is_extinguished,
description (bomberscat tweet text), tweet_url, media (photo/video URLs),
source, last_update (epoch ms), url (focs.cat fire page)
```

The event payload additionally carries `change` (`"new"` | `"status_change"`)
and `previous_status` (the prior status on a change, else `null`).

### When you get notified

`focs_fire_detected` fires once per **new** fire entering range, and again each
time a tracked fire's **status changes**. On startup the last-seen state is
seeded from the first poll, so the existing backlog never notifies — only fires
that appear or change *after* setup do. A fire that leaves range and later
re-enters is treated as new again.

> **Status changes are only seen for fires that stay in the tracked set.** In the
> default *active-only* mode the integration keeps only `Actiu` fires, so a fire
> going `Actiu → Controlat` **drops out** of the set and the transition isn't
> reported (you still get the initial "new active fire" alert). To receive
> status-change notifications, enable **Include non-active fires** in the
> integration's *Configure* so fires are tracked across transitions, then use the
> blueprint's **Statuses** filter to limit which ones notify (e.g. `Actiu`,
> `Controlat`, `Estabilitzat`, `Extingit` — excluding `Falsa Alarma`).

## Install (HACS)

1. HACS → ⋮ → **Custom repositories** → add this repo's URL, category
   **Integration**.
2. Install **focs.cat Fire Alerts**, then restart Home Assistant.
3. **Settings → Devices & Services → Add Integration → focs.cat Fire Alerts**.
   Set the center point (defaults to your HA location), radius, and scan
   interval.

## Get notified

The integration only emits events/entities — it does not send messages itself,
so you choose where alerts go. A blueprint, `focs.cat fire alert`, is bundled.

**Add the blueprint.** Import it by URL (the most reliable way for a custom
integration) — **Settings → Automations & Scenes → Blueprints → Import
Blueprint**, paste:

```
https://raw.githubusercontent.com/abate/ha-focs/main/custom_components/focs/blueprints/automation/focs/focs_fire_alert.yaml
```

Then **Create Automation → from blueprint → focs.cat fire alert**. It has three
groups:

- **Notification action** — an action selector (the service field autocompletes).
  The default sends a **Telegram bot** message (`telegram_bot.send_message`) to
  all allowed chat IDs of the `telegram_bot` integration. Edit it to target a
  specific chat (add `target: <chat_id>`) or to send a phone push
  (`notify.mobile_app_*`) instead. *(The Telegram default needs the
  [`telegram_bot`](https://www.home-assistant.io/integrations/telegram_bot/)
  integration configured.)*
- **Filters** — notify only when the fire matches: **Statuses** (multi-select;
  empty = any) and **Forest fires only**.
- **Message** — **Title** and **Message** templates. Both are rendered into the
  `title` / `message` variables (with the `fire.*` fields resolved) and the
  default action injects them via `{{ title }}` / `{{ message }}`. Editing these
  fields changes what Telegram sends — **as long as the action keeps those
  references**. If you replace the action with a literal message, the Message
  section is no longer used. The default title shows the transition on a status
  change (e.g. `🔥 …: Actiu → Controlat`) via `fire.change` / `fire.previous_status`.

This triggers on both new fires and status changes — see
[When you get notified](#when-you-get-notified) for how to actually receive the
status-change alerts.

The templates and the action can use the full `fire.*` object (see the field
list above) plus `photos` (image URLs only).

> Telegram note: `telegram_bot` defaults to Markdown parse mode, so `*` `_` `[`
> in a tweet description can break formatting — add `parse_mode: html` (or
> `text`) to the action's `data` if needed.

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
