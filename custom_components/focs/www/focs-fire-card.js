// focs.cat Fire Alerts — custom Lovelace card.
// Served and auto-registered by the integration; no manual resource needed.
// Usage:  type: custom:focs-fire-card
// Options: entity (optional, auto-detected), title (optional),
//          plans_entity (optional, auto-detected), show_plans (default true).

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
    const plansId =
      this._config.show_plans === false
        ? undefined
        : this._config.plans_entity || this._findEntity(hass, "plans");
    const plansState = plansId ? hass.states[plansId] : undefined;
    const plans = (plansState && plansState.attributes.plans) || [];
    // Only re-render when the fire or plan data actually changes.
    const key = JSON.stringify([entityId, state && state.state, fires, plans]);
    if (key === this._lastKey) return;
    this._lastKey = key;
    this._render(entityId, state, fires, plans);
  }

  _resolveEntity(hass) {
    return this._config.entity || this._findEntity(hass, "fires");
  }

  // Auto-detect: a binary_sensor exposing a list attribute of this name.
  _findEntity(hass, attr) {
    for (const id of Object.keys(hass.states)) {
      if (
        id.startsWith("binary_sensor.") &&
        Array.isArray(hass.states[id].attributes[attr])
      ) {
        return id;
      }
    }
    return undefined;
  }

  _render(entityId, state, fires, plans) {
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

    const plansHtml = plans.map((p) => this._planHtml(p)).join("");
    if (!fires.length) {
      this._body.innerHTML =
        plansHtml +
        '<p style="color:var(--secondary-text-color)">✅ No fires within range.</p>';
      return;
    }

    this._body.innerHTML = plansHtml + fires.map((f) => this._fireHtml(f)).join("");
  }

  _planHtml(p) {
    const esc = this._esc;
    const colour =
      p.phase_rank >= 3
        ? "var(--error-color)"
        : p.phase_rank === 2
          ? "var(--warning-color)"
          : "var(--secondary-text-color)";
    const since = p.since
      ? new Date(p.since).toLocaleString([], {
          day: "2-digit",
          month: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
        })
      : "";
    const links = [];
    if (p.bulletin_url)
      links.push(
        `<a href="${esc(p.bulletin_url)}" target="_blank" rel="noopener">comunicat</a>`
      );
    if (p.url)
      links.push(`<a href="${esc(p.url)}" target="_blank" rel="noopener">Protecció Civil</a>`);
    return `
      <div style="padding:12px 0 12px 10px;border-left:4px solid ${colour};
                  border-bottom:1px solid var(--divider-color)">
        <div style="font-weight:600;font-size:1.05em">🚨 ${esc(p.plan)} ·
          <span style="color:${colour}">${esc(p.phase)}</span></div>
        <div style="color:var(--secondary-text-color);margin:2px 0 6px">
          ${esc(p.risk || "Pla de protecció civil")}${since ? ` · des de ${esc(since)}` : ""}
        </div>
        ${p.description ? `<div style="margin:6px 0">${esc(p.description)}</div>` : ""}
        ${links.length ? `<div style="margin-top:4px">${links.join(" · ")}</div>` : ""}
      </div>`;
  }

  _esc(s) {
    return String(s == null ? "" : s).replace(
      /[&<>"]/g,
      (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])
    );
  }

  _fireHtml(f) {
    const esc = this._esc;
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
    const [, , fires = [], plans = []] = (this._lastKey && JSON.parse(this._lastKey)) || [];
    return 1 + Math.max(1, fires.length) * 3 + plans.length * 2;
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
  description:
    "Nearby focs.cat fires with detail, photos, and links, plus active Catalan civil protection plans.",
});
