"""Pull the 7-day forecast for Evanston from Open-Meteo and decide run venues.

Usage: python scripts/weather.py            # prints forecast and venue decisions
       python scripts/weather.py --apply    # also writes venue changes into data/week.json

Rule (from PROFILE.md): cold is fine, wet is not. Outside if precipitation
probability < 40% and precipitation < 0.1 in for the day; otherwise treadmill.
"""
import json, sys, datetime as dt
import requests

LAT, LON = 42.045, -87.69  # Evanston, IL
WET_PROB = 40      # percent
WET_AMOUNT = 0.1   # inches

def forecast():
    r = requests.get("https://api.open-meteo.com/v1/forecast", params={
        "latitude": LAT, "longitude": LON,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,snowfall_sum",
        "temperature_unit": "fahrenheit", "precipitation_unit": "inch",
        "timezone": "America/Chicago", "forecast_days": 7,
    }, timeout=20)
    r.raise_for_status()
    d = r.json()["daily"]
    out = {}
    for i, day in enumerate(d["time"]):
        out[day] = {
            "hi": d["temperature_2m_max"][i], "lo": d["temperature_2m_min"][i],
            "precip_in": d["precipitation_sum"][i] or 0,
            "precip_prob": d["precipitation_probability_max"][i] or 0,
            "snow_in": d["snowfall_sum"][i] or 0,
        }
    return out

def decide(day):
    wet = day["precip_prob"] >= WET_PROB or day["precip_in"] >= WET_AMOUNT or day["snow_in"] > 0
    return "treadmill" if wet else "outside"

def main():
    fc = forecast()
    week = json.load(open("data/week.json"))
    changed = False
    for s in week["days"]:
        f = fc.get(s["date"])
        if not f:
            continue
        line = f'{s["date"]} {f["lo"]:.0f}–{f["hi"]:.0f}°F  rain {f["precip_prob"]}% {f["precip_in"]:.2f}in'
        if s["sport"] == "run":
            v = decide(f)
            line += f'  → run {v}'
            if s["venue"] != v and "--apply" in sys.argv:
                s["note"] = (s["note"] + f' Venue set to {v} by weather on {dt.date.today()}.').strip()
                s["venue"] = v
                changed = True
        print(line)
    if changed:
        json.dump(week, open("data/week.json", "w"), indent=2)
        print("week.json updated")

if __name__ == "__main__":
    main()
