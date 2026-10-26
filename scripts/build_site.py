"""Render data/week.json into docs/index.html (today-first home page) and docs/week.ics,
plus the bits that make the page an installable app with its own notifications
(manifest.webmanifest, sw.js). The icons in docs/ are static and committed.
GitHub Pages serves docs/ from main (Pages can only publish / or /docs from a branch).

Usage: python scripts/build_site.py
Set REPO_URL env var to your GitHub repo URL so the chat link works.
"""
import json, os, datetime as dt, html

REPO = os.environ.get("REPO_URL", "https://github.com")
CHAT = os.environ.get("CHAT_URL", "https://claude.ai/code")
SECRETS = f"{REPO}/settings/secrets/actions/new" if REPO.count("/") > 3 else "https://github.com"
# Public half of the VAPID keypair (repo variable); the private half is the VAPID_PRIVATE_KEY secret.
# Both come from scripts/setup_secrets.py. Without it the page hides the notifications card.
VAPID_PUBLIC = os.environ.get("VAPID_PUBLIC_KEY") or ""
RACE = dt.date(2027, 9, 11)
APP_LINKS = {
    # URL scheme first, web fallback second. Schemes are best-effort; fix any that don't open.
    "runna": ("runna://", "https://www.runna.com"),
    "trainerroad": ("trainerroad://", "https://www.trainerroad.com/app"),
    "fitbod": ("fitbod://", "https://fitbod.me"),
    "none": (None, None),
}
APP_NAME = {"runna": "Runna", "trainerroad": "TrainerRoad", "fitbod": "Fitbod"}
SPORT_LABEL = {"run": "Run", "bike": "Bike", "strength": "Strength", "swim": "Swim", "rest": "Rest"}

def load():
    return json.load(open("data/week.json"))

def day_card(s, today):
    d = dt.date.fromisoformat(s["date"])
    is_today = d == today
    scheme, web = APP_LINKS.get(s["app"], (None, None))
    btn = ""
    if web:
        btn = f'<a class="go" href="{web}" data-scheme="{scheme or ""}">Open {APP_NAME.get(s["app"], s["app"])}</a>'
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
    weeks_out = (RACE - today).days // 7
    return f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Training">
<meta name="theme-color" content="#0f1a14">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icon-180.png">
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
.chat{{display:block;text-align:center;margin:20px 0 0;padding:14px;border:1px solid var(--line);border-radius:14px;color:var(--ink);text-decoration:none;font-weight:600}}
.push{{background:var(--card);border:1px dashed var(--line);border-radius:14px;padding:14px 16px;margin-bottom:12px;font-size:15px}}
.push button{{font:inherit;font-weight:600;background:var(--go);color:var(--go-ink);border:0;border-radius:10px;padding:10px 16px;margin-top:10px}}
.push textarea{{width:100%;height:96px;margin-top:10px;font:12px ui-monospace,Menlo,monospace;border-radius:8px;border:1px solid var(--line);background:var(--bg);color:var(--ink)}}
.push a{{color:var(--go)}}[hidden]{{display:none!important}}
.foot{{text-align:center;margin-top:16px;font-size:13px;color:var(--mute)}}.foot a{{color:inherit}}
</style></head><body>
<div class="top"><h1>Week of {dt.date.fromisoformat(week["week_of"]).strftime("%-d %b")}</h1><span>Phase {week["phase"]} · {weeks_out} weeks to Madison</span></div>
<div class="push" id="push-install" hidden>Get the morning brief as a notification: tap <b>Share → Add to Home Screen</b>, then open <b>Training</b> from your home screen.</div>
<div class="push" id="push-ask" hidden>Get the 6am brief as a notification from this app.<br><button id="push-on">Turn on notifications</button></div>
<div class="push" id="push-code" hidden>Last step: copy this code into the GitHub secret <b>PUSH_SUBSCRIPTION</b> (<a href="{SECRETS}">open secrets</a>).
<textarea id="push-json" readonly></textarea><button id="push-copy">Copy code</button></div>
{cards}
<a class="chat" href="{CHAT}">Ask the coach</a>
<p class="foot"><a href="{REPO}">repo</a> · <a href="#" id="push-show">notification code</a></p>
<script>
// Notifications from this page itself (iOS 16.4+ when opened from the home screen).
const VAPID = "{VAPID_PUBLIC}";
const $ = id => document.getElementById(id);
const standalone = matchMedia('(display-mode: standalone)').matches || navigator.standalone;
const b64 = s => {{ s = s.replace(/-/g,'+').replace(/_/g,'/'); const r = atob(s + '='.repeat((4 - s.length % 4) % 4)); return Uint8Array.from(r, c => c.charCodeAt(0)); }};
async function showCode(sub) {{ $('push-json').value = JSON.stringify(sub); $('push-code').hidden = false; $('push-ask').hidden = true; }}
async function subscribe() {{
  const reg = await navigator.serviceWorker.ready;
  if (await Notification.requestPermission() !== 'granted') return;
  const sub = await reg.pushManager.subscribe({{userVisibleOnly: true, applicationServerKey: b64(VAPID)}});
  showCode(sub);
}}
if (VAPID && 'serviceWorker' in navigator) {{
  navigator.serviceWorker.register('sw.js').then(async reg => {{
    if (!('PushManager' in window)) {{ if (!standalone) $('push-install').hidden = false; return; }}
    const sub = await reg.pushManager.getSubscription();
    if (!sub || Notification.permission !== 'granted') $('push-ask').hidden = false;
    $('push-show').onclick = e => {{ e.preventDefault(); sub ? showCode(sub) : ($('push-ask').hidden = false); }};
  }});
}}
$('push-on').onclick = () => subscribe().catch(e => alert('Could not turn on notifications: ' + e.message));
$('push-copy').onclick = () => {{ const t = $('push-json'); t.select(); navigator.clipboard ? navigator.clipboard.writeText(t.value) : document.execCommand('copy'); $('push-copy').textContent = 'Copied'; }};

// Try the app's URL scheme first; fall back to the web link if nothing opens.
document.querySelectorAll('a.go').forEach(a=>{{a.addEventListener('click',e=>{{const s=a.dataset.scheme;if(!s)return;e.preventDefault();const t=Date.now();location.href=s;setTimeout(()=>{{if(Date.now()-t<1500)location.href=a.href;}},1200);}});}});
</script>
</body></html>'''

def esc(t):
    return t.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

MANIFEST = {
    "name": "Training", "short_name": "Training", "start_url": "./", "scope": "./", "display": "standalone",
    "background_color": "#0f1a14", "theme_color": "#0f1a14",
    "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
              {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"}],
}

SW = """// Receives the 6am brief and opens the week page when tapped. No caching: the page is always fresh.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('push', e => {
  const d = e.data ? e.data.json() : {};
  e.waitUntil(self.registration.showNotification(d.title || 'Training',
    {body: d.body || '', icon: 'icon-192.png', badge: 'icon-192.png', tag: 'daily', data: {url: d.url || './'}}));
});
self.addEventListener('notificationclick', e => {
  e.notification.close();
  const url = e.notification.data.url;
  e.waitUntil(clients.matchAll({type: 'window', includeUncontrolled: true}).then(ws => {
    for (const w of ws) if ('focus' in w) return w.focus();
    return clients.openWindow(url);
  }));
});
"""

def ics(week):
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//Training HQ//EN","X-WR-CALNAME:Training","REFRESH-INTERVAL;VALUE=DURATION:PT6H"]
    for s in week["days"]:
        if s["sport"] == "rest":
            continue
        d = s["date"].replace("-", "")
        lines += ["BEGIN:VEVENT", f"UID:{s['date']}-{s['sport']}@training-hq", f"DTSTAMP:{stamp}", f"DTSTART;VALUE=DATE:{d}",
                  f"SUMMARY:{esc(s['title'])} · {s['minutes']} min · {s['venue']}", esc(f"DESCRIPTION:{APP_NAME.get(s['app'], s['app'])} {s['note']}".strip()), "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"

if __name__ == "__main__":
    os.makedirs("docs", exist_ok=True)
    week = load()
    open("docs/index.html", "w").write(render(week))
    open("docs/week.ics", "w").write(ics(week))
    open("docs/.nojekyll", "w").close()
    json.dump(MANIFEST, open("docs/manifest.webmanifest", "w"), indent=2)
    open("docs/sw.js", "w").write(SW)
    print("built docs/index.html and docs/week.ics")
