#!/usr/bin/env python3
"""Filter focs.cat fires near Santa Coloma de Gramenet / Badalona / Parc de
la Serralada de la Marina.

Data source: focs.cat backend (public Supabase REST endpoint). The anon key
below is the one shipped in the site's frontend JS, so it is public.

Usage:
    python3 focs_filter.py                 # active fires, within 6 km
    python3 focs_filter.py --radius 10     # widen the radius (km)
    python3 focs_filter.py --all           # include non-active fires too
    python3 focs_filter.py --json          # raw JSON output
"""

import argparse
import json
import math
import urllib.request

SUPABASE_URL = "https://rycezpzfezvoahdqafjj.supabase.co"
ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ5Y2V6cHpmZXp2b2FoZHFhZmpqIiwicm9sZSI6"
    "ImFub24iLCJpYXQiOjE2ODM4MDcyMzgsImV4cCI6MTk5OTM4MzIzOH0."
    "FHfEQcrG0YT5vtZ7biV7c5ZUDG5hws51upgKomA1nDM"
)

# Reference points covering the area of interest (lat, lon).
TARGETS = {
    "Santa Coloma de Gramenet": (41.4517, 2.2080),
    "Badalona": (41.4469, 2.2452),
    "Parc de la Serralada de la Marina": (41.4700, 2.2550),
}


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def fetch_fires():
    url = (
        f"{SUPABASE_URL}/rest/v1/fires"
        "?select=id,where_geolocation,where_geolocation_full,status,type,"
        "latitude,longitude,ops,when_last_time,radius"
        "&order=when_last_time.desc&limit=2000"
    )
    req = urllib.request.Request(
        url, headers={"apikey": ANON_KEY, "Authorization": f"Bearer {ANON_KEY}"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def nearest_target(lat, lon):
    best_name, best_dist = None, float("inf")
    for name, (tlat, tlon) in TARGETS.items():
        d = haversine_km(lat, lon, tlat, tlon)
        if d < best_dist:
            best_name, best_dist = name, d
    return best_name, best_dist


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--radius", type=float, default=6.0, help="km radius (default 6)")
    ap.add_argument("--all", action="store_true", help="include non-active fires")
    ap.add_argument("--json", action="store_true", help="raw JSON output")
    args = ap.parse_args()

    matches = []
    for f in fetch_fires():
        lat, lon = f.get("latitude"), f.get("longitude")
        if lat is None or lon is None:
            continue
        try:
            lat, lon = float(lat), float(lon)
        except (TypeError, ValueError):
            continue
        if not args.all and (f.get("status") or "").lower() != "actiu":
            continue
        name, dist = nearest_target(lat, lon)
        if dist <= args.radius:
            f["_nearest"] = name
            f["_distance_km"] = round(dist, 2)
            matches.append(f)

    matches.sort(key=lambda x: x["_distance_km"])

    if args.json:
        print(json.dumps(matches, ensure_ascii=False, indent=2))
        return

    if not matches:
        print(f"No fires within {args.radius} km of the target area.")
        return

    print(f"{len(matches)} fire(s) within {args.radius} km:\n")
    for f in matches:
        when = ""
        if f.get("when_last_time"):
            import datetime

            when = datetime.datetime.fromtimestamp(
                f["when_last_time"] / 1000
            ).strftime("%Y-%m-%d %H:%M")
        print(
            f"- [{f.get('status')}] {f.get('type') or 'Incendi'} — "
            f"{f.get('where_geolocation_full') or f.get('where_geolocation')}\n"
            f"    {f['_distance_km']} km from {f['_nearest']} | "
            f"ops={f.get('ops')} | last update {when}\n"
            f"    https://focs.cat/fire/{f.get('id')}"
        )


if __name__ == "__main__":
    main()
