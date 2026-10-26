"""Pull the 7-day forecast for Evanston from Open-Meteo and decide run venues.

Usage: python scripts/weather.py            # prints forecast and venue decisions
       python scripts/weather.py --apply    # also writes venue changes into data/week.json

Rule (from PROFILE.md): cold is fine, wet is not. Outside if precipitation
probability < 40%, precipitation < 0.1 in, no snowfall and no snow on the ground;
otherwise treadmill. Only planned runs from today on are touched.
"""
import json, sys, time, datetime as dt
import requests

LAT, LON = 42.045, -87.69  # Evanston, IL
WET_PROB = 40      # percent
WET_AMOUNT = 0.1   # inches
SNOW_GROUND = 0.5  # inches of snow depth that makes paths wet
DEPTH_TO_IN = {"m": 39.37, "cm": 0.3937, "ft": 12.0, "inch": 1.0, "in": 1.0}

def get(url, params, tries=4):
    # Open-Meteo rate-limits shared IPs (CI runners); back off and retry.
    for i in range(tries):
        try:
            r = requests.get(url, params=params, timeout=20)
            if r.status_code != 429 and r.status_code < 500:
                r.raise_for_status()
                return r.json()
        except (requests.ConnectionError, requests.Timeout):
            if i == tries - 1:
                raise
        time.sleep(5 * 2 ** i)
    r.raise_for_status()

def dump_week(week, path="data/week.json"):
    # Keep one day per line so diffs stay surgical.
    head = {k: v for k, v in week.items() if k != "days"}
    lines = ["{"] + [f'  {json.dumps(k)}: {json.dumps(v)},' for k, v in head.items()] + ['  "days": [']
    lines += ["    " + json.dumps(d, ensure_ascii=False) + ("," if i < len(week["days"]) - 1 else "") for i, d in enumerate(week["days"])]
    lines += ["  ]", "}"]
    open(path, "w").write("\n".join(lines) + "\n")

def forecast():
    j = get("https://api.open-meteo.com/v1/forecast", {
        "latitude": LAT, "longitude": LON,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,snowfall_sum",
        "hourly": "snow_depth",
        "temperature_unit": "fahrenheit", "precipitation_unit": "inch",
        "timezone": "America/Chicago", "forecast_days": 7,
    })
    d = j["daily"]
    # Morning snow depth (6–9am) per day, in inches.
    k = DEPTH_TO_IN.get(j.get("hourly_units", {}).get("snow_depth"), 39.37)
    depth = {}
    for t, v in zip(j["hourly"]["time"], j["hourly"]["snow_depth"]):
        if 6 <= int(t[11:13]) <= 9:
            depth[t[:10]] = max(depth.get(t[:10], 0), (v or 0) * k)
    out = {}
    for i, day in enumerate(d["time"]):
        out[day] = {
            "hi": d["temperature_2m_max"][i], "lo": d["temperature_2m_min"][i],
            "precip_in": d["precipitation_sum"][i] or 0,
            "precip_prob": d["precipitation_probability_max"][i] or 0,
            "snow_in": d["snowfall_sum"][i] or 0,
            "ground_in": depth.get(day, 0),
        }
    return out

def decide(day):
    wet = day["precip_prob"] >= WET_PROB or day["precip_in"] >= WET_AMOUNT or day["snow_in"] > 0 or day["ground_in"] >= SNOW_GROUND
    return "treadmill" if wet else "outside"

def main():
    fc = forecast()
    week = json.load(open("data/week.json"))
    today = dt.date.today().isoformat()
    changed = False
    for s in week["days"]:
        f = fc.get(s["date"])
        if not f:
            continue
        line = f'{s["date"]} {f["lo"]:.0f}–{f["hi"]:.0f}°F  rain {f["precip_prob"]}% {f["precip_in"]:.2f}in'
        if f["snow_in"] or f["ground_in"]:
            line += f'  snow {f["snow_in"]:.1f}in, ground {f["ground_in"]:.1f}in'
        if s["sport"] == "run" and s["status"] == "planned" and s["date"] >= today:
            v = decide(f)
            line += f'  → run {v}'
            if s["venue"] != v and "--apply" in sys.argv:
                note = s["note"].split(" Venue set to ")[0] if not s["note"].startswith("Venue set to ") else ""
                s["note"] = (note + f' Venue set to {v} by weather on {today}.').strip()
                s["venue"] = v
                changed = True
        print(line)
    if changed:
        dump_week(week)
        print("week.json updated")

if __name__ == "__main__":
    main()
