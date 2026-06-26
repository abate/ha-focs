// focs.cat Fire Alerts — custom Lovelace card.
// Served and auto-registered by the integration; no manual resource needed.
// Usage:  type: custom:focs-fire-card
// Options: entity (optional, auto-detected), title (optional).

const IMG_RE = /\.(jpe?g|png)(\?|$)/i;

class FocsFireCard extends HTMLElement {
  setConfig(config) {
    this._config = config || {};
    this._lastKey = null;
  }

  set hass(hass) {
    this._hass = hass;
    const entityId = this._resolveEntity(hass);
    const state = entityId ? hass.states[entityId] : undefined;
    const fires = (state && state.attributes && state.attributes.fires) || [];
    // Only re-render when the fire data actually changes.
    const key = JSON.stringify([entityId, state && state.state, fires]);
    if (key === this._lastKey) return;
    this._lastKey = key;
    this._render(entityId, state, fires);
  }

  _resolveEntity(hass) {
    if (this._config.entity) return this._config.entity;
    // Auto-detect: a binary_sensor exposing a `fires` attribute.
    for (const id of Object.keys(hass.states)) {
      if (
        id.startsWith("binary_sensor.") &&
        Array.isArray(hass.states[id].attributes.fires)
      ) {
        return id;
      }
    }
    return undefined;
  }

  _render(entityId, state, fires) {
    if (!this._card) {
      this._card = document.createElement("ha-card");
      this._body = document.createElement("div");
      this._body.style.padding = "8px 16px 16px";
      this._card.appendChild(this._body);
      this.innerHTML = "";
      this.appendChild(this._card);
    }
    this._card.header = this._config.title || "Fires nearby";

    if (!entityId) {
      this._body.innerHTML =
        '<p style="color:var(--secondary-text-color)">' +
        "No focs.cat fire entity found. Set <code>entity:</code> in the card config." +
        "</p>";
      return;
    }

    if (!fires.length) {
      this._body.innerHTML =
        '<p style="color:var(--secondary-text-color)">✅ No fires within range.</p>';
      return;
    }

    this._body.innerHTML = fires.map((f) => this._fireHtml(f)).join("");
  }

  _fireHtml(f) {
    const esc = (s) =>
      String(s == null ? "" : s).replace(
        /[&<>"]/g,
        (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])
      );
    const photos = (f.media || []).filter((u) => IMG_RE.test(u));
    const res = [];
    if (f.fire_trucks) res.push(`🚒 ${f.fire_trucks}`);
    if (f.firefighters) res.push(`🧑‍🚒 ${f.firefighters}`);
    if (f.helicopters) res.push(`🚁 ${f.helicopters}`);
    if (f.planes) res.push(`✈️ ${f.planes}`);
    if (f.burnt_area) res.push(`🌍 ${esc(f.burnt_area)}`);

    const links = [`<a href="${esc(f.url)}" target="_blank" rel="noopener">focs.cat</a>`];
    if (f.tweet_url)
      links.push(
        `<a href="${esc(f.tweet_url)}" target="_blank" rel="noopener">@bomberscat</a>`
      );

    return `
      <div style="padding:12px 0;border-bottom:1px solid var(--divider-color)">
        <div style="font-weight:600;font-size:1.05em">🔥 ${esc(f.location)}</div>
        <div style="color:var(--secondary-text-color);margin:2px 0 6px">
          <b>${esc(f.status)}</b> · ${esc(f.type || "Incendi")} ·
          <b>${esc(f.distance_km)} km</b>${f.ops ? ` · ${esc(f.ops)} resources` : ""}
        </div>
        ${res.length ? `<div style="margin-bottom:6px">${res.join(" · ")}</div>` : ""}
        ${
          f.description
            ? `<div style="font-style:italic;margin:6px 0;white-space:pre-wrap">${esc(
                f.description
              )}</div>`
            : ""
        }
        ${
          photos.length
            ? `<img src="${esc(
                photos[0]
              )}" style="max-width:100%;border-radius:8px;margin:6px 0" />`
            : ""
        }
        <div style="margin-top:4px">${links.join(" · ")}</div>
      </div>`;
  }

  getCardSize() {
    const fires = (this._lastKey && JSON.parse(this._lastKey)[2]) || [];
    return 1 + Math.max(1, fires.length) * 3;
  }

  static getConfigElement() {
    return document.createElement("div");
  }

  static getStubConfig() {
    return { title: "Fires nearby" };
  }
}

customElements.define("focs-fire-card", FocsFireCard);

// Make it appear in the dashboard "Add card" picker.
window.customCards = window.customCards || [];
window.customCards.push({
  type: "focs-fire-card",
  name: "focs.cat Fire card",
  description: "Nearby focs.cat fires with detail, photos, and links.",
});
