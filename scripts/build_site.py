"""Render data/week.json into site/index.html (today-first home page) and site/week.ics.

Usage: python scripts/build_site.py
Set REPO_URL env var to your GitHub repo URL so the chat link works.
"""
import json, os, datetime as dt, html

REPO = os.environ.get("REPO_URL", "https://github.com")
APP_LINKS = {
    # URL scheme first, web fallback second. Schemes are best-effort; fix any that don't open.
    "runna": ("runna://", "https://www.runna.com"),
    "trainerroad": ("trainerroad://", "https://www.trainerroad.com/app"),
    "fitbod": ("fitbod://", "https://fitbod.me"),
    "none": (None, None),
}
SPORT_LABEL = {"run": "Run", "bike": "Bike", "strength": "Strength", "swim": "Swim", "rest": "Rest"}

def load():
    return json.load(open("data/week.json"))

def day_card(s, today):
    d = dt.date.fromisoformat(s["date"])
    is_today = d == today
    scheme, web = APP_LINKS.get(s["app"], (None, None))
    btn = ""
    if web:
        btn = f'<a class="go" href="{web}" data-scheme="{scheme or ""}">Open {s["app"].capitalize()}</a>'
    venue = "" if s["sport"] == "rest" else f'<span class="venue">{html.escape(s["venue"])}</span>'
    note = f'<p class="note">{html.escape(s["note"])}</p>' if s["note"] else ""
    mins = f'{s["minutes"]} min' if s["minutes"] else ""
    return f'''
<section class="day {s["status"]}{" today" if is_today else ""}" id="d{s["date"]}">
  <header><span class="dow">{d.strftime("%a")}</span><span class="date">{d.strftime("%-d %b")}</span>{venue}</header>
  <h2>{html.escape(s["title"])}</h2>
  <p class="meta">{SPORT_LABEL.get(s["sport"], s["sport"])} {mins}</p>
  {note}
  {btn}
</section>'''

def render(week):
    today = dt.date.today()
    days = sorted(week["days"], key=lambda s: s["date"])
    # today first, then the rest of the week in order
    ordered = [s for s in days if s["date"] >= today.isoformat()] + [s for s in days if s["date"] < today.isoformat()]
    cards = "\n".join(day_card(s, today) for s in ordered)
    race = dt.date(2027, 9, 11)
    weeks_out = (race - today).days // 7
    return f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Training">
<meta name="theme-color" content="#0f1a14">
<title>Training HQ</title>
<style>
:root{{color-scheme:light dark;--bg:#f3f1ec;--ink:#17201b;--mute:#6a7570;--card:#fff;--line:#dcd8cf;--go:#1d5c3a;--go-ink:#fff;--today:#1d5c3a;
  box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}
@media(prefers-color-scheme:dark){{:root{{--bg:#0f1a14;--ink:#eef2ee;--mute:#9aa79f;--card:#162419;--line:#243528;--go:#6fd39a;--go-ink:#0f1a14;--today:#6fd39a}}}}
*{{box-sizing:inherit}}html{{scroll-padding-top:env(safe-area-inset-top,0px)}}
body{{margin:0;background:var(--bg);color:var(--ink);font:17px/1.4 -apple-system,"SF Pro Text",Helvetica,Arial,sans-serif;padding:16px 16px 48px}}
.top{{display:flex;justify-content:space-between;align-items:baseline;margin:4px 0 16px}}
.top h1{{font-size:20px;margin:0;font-weight:600}}.top span{{color:var(--mute);font-size:14px}}
.day{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px;margin-bottom:10px}}
.day.today{{border:2px solid var(--today);padding:20px 16px}}
.day.today h2{{font-size:28px}}
.day.done{{opacity:.55}}.day.skipped{{opacity:.45;text-decoration:line-through}}
header{{display:flex;gap:10px;align-items:baseline;font-size:14px;color:var(--mute)}}
.dow{{font-weight:600;color:var(--ink)}}.venue{{margin-left:auto}}
h2{{margin:6px 0 2px;font-size:20px;font-weight:600}}
.meta{{margin:0;color:var(--mute)}}.note{{margin:8px 0 0;font-size:15px}}
.go{{display:inline-block;margin-top:12px;background:var(--go);color:var(--go-ink);text-decoration:none;padding:10px 16px;border-radius:10px;font-weight:600}}
.chat{{display:block;text-align:center;margin:24px auto 0;color:var(--mute);text-decoration:none;font-size:15px}}
</style></head><body>
<div class="top"><h1>Week of {dt.date.fromisoformat(week["week_of"]).strftime("%-d %b")}</h1><span>Phase {week["phase"]} · {weeks_out} weeks to Madison</span></div>
{cards}
<a class="chat" href="{REPO}">Talk to the coach · open the repo</a>
<script>
// Try the app's URL scheme first; fall back to the web link if nothing opens.
document.querySelectorAll('a.go').forEach(a=>{{a.addEventListener('click',e=>{{const s=a.dataset.scheme;if(!s)return;e.preventDefault();const t=Date.now();location.href=s;setTimeout(()=>{{if(Date.now()-t<1500)location.href=a.href;}},1200);}});}});
</script>
</body></html>'''

def ics(week):
    lines = ["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//Training HQ//EN","X-WR-CALNAME:Training","REFRESH-INTERVAL;VALUE=DURATION:PT6H"]
    for s in week["days"]:
        if s["sport"] == "rest":
            continue
        d = s["date"].replace("-", "")
        lines += ["BEGIN:VEVENT", f"UID:{s['date']}-{s['sport']}@training-hq", f"DTSTART;VALUE=DATE:{d}",
                  f"SUMMARY:{s['title']} · {s['minutes']} min · {s['venue']}", f"DESCRIPTION:{s['app']} {s['note']}".strip(), "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"

if __name__ == "__main__":
    os.makedirs("site", exist_ok=True)
    week = load()
    open("site/index.html", "w").write(render(week))
    open("site/week.ics", "w").write(ics(week))
    print("built site/index.html and site/week.ics")
