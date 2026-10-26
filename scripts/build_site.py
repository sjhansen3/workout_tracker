"""Render data/week.json into docs/index.html (today-first home page) and docs/week.ics,
plus the bits that make the page an installable app with its own notifications
(manifest.webmanifest, sw.js). The icons in docs/ are static and committed.
GitHub Pages serves docs/ from main (Pages can only publish / or /docs from a branch).

Usage: python scripts/build_site.py
Set REPO_URL env var to your GitHub repo URL so the chat link works.
"""
import json, os, datetime as dt, html

REPO = os.environ.get("REPO_URL", "https://github.com")
# The standing "Coach" Claude Code session on this repo: one conversation with history.
CHAT = os.environ.get("CHAT_URL") or "https://claude.ai/code/session_01D1JheBwhYgigUFzvCCM8eX"
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

START = dt.date(2026, 10, 26)  # week 1 of the plan
PHASE_NAME = {1: "Habit & strength", 2: "Engine", 3: "Three sports", 4: "Race specific"}
# Sport colours: the bar down a card fades top→bottom; the dot uses the second colour.
COLOR = {"run": ("#e8c61a", "#4cc35a"), "bike": ("#b98cf6", "#7b61f0"), "strength": ("#f7b23b", "#f0703c"),
         "swim": ("#47cdf2", "#2f7cf0"), "rest": ("#4a5560", "#4a5560")}

def coach_html(path="data/coach.md"):
    """The coach's own words, free text. Minimal markdown: paragraphs, **bold**, '- ' bullets.
    The first paragraph shows; the rest folds under 'more'."""
    import re
    if not os.path.exists(path) or not open(path).read().strip():
        return ""
    blocks = [b.strip() for b in open(path).read().strip().split("\n\n") if b.strip()]
    def fmt(b):
        b = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html.escape(b))
        lines = b.split("\n")
        if all(l.startswith("- ") for l in lines):
            return "<ul>" + "".join(f"<li>{l[2:]}</li>" for l in lines) + "</ul>"
        return "<p>" + "<br>".join(lines) + "</p>"
    first, rest = fmt(blocks[0]), "".join(fmt(b) for b in blocks[1:])
    more = f'<details><summary>more</summary>{rest}</details>' if rest else ""
    return f'<section class="coach"><h3>From the coach</h3>{first}{more}</section>'

def recovery_html(date):
    import health  # last night's Apple Health numbers, shown on today's card
    line, low = health.recovery(date)
    if not line:
        return ""
    return f'<p class="rec{" low" if low else ""}">{html.escape(line).replace(chr(10), "<br>")}</p>'

def hero(s, today):
    d = dt.date.fromisoformat(s["date"])
    top, bottom = COLOR.get(s["sport"], COLOR["rest"])
    scheme, web = APP_LINKS.get(s["app"], (None, None))
    btn = f'<a class="go" href="{web}" data-scheme="{scheme or ""}">Open {APP_NAME.get(s["app"], s["app"])}</a>' if web else ""
    when = d.strftime("%A, %b %-d") + (f' · {s["minutes"]} min' if s["minutes"] else "")
    what = SPORT_LABEL.get(s["sport"], s["sport"]) + ("" if s["sport"] == "rest" else f' · {s["venue"]}')
    note = f'<p class="note">{html.escape(s["note"])}</p>' if s["note"] else ""
    rec = recovery_html(s["date"]) if d == today else ""
    badge = {"done": '<span class="badge">✓ Done</span>', "skipped": '<span class="badge off">Skipped</span>',
             "modified": '<span class="badge off">Changed</span>'}.get(s["status"], "")
    return f'''<article class="hero {s["status"]}" data-date="{s["date"]}" style="--c1:{top};--c2:{bottom}" hidden>
  <div class="bar"></div>
  <div class="body">
    <h2>{html.escape(s["title"])}{badge}</h2>
    <p class="when">{when}</p>
    <p class="what">{what}</p>
    {note}{rec}{btn}
  </div>
</article>'''

def render(week):
    today = dt.date.today()
    days = sorted(week["days"], key=lambda s: s["date"])
    dates = sorted({s["date"] for s in days})
    pick = today.isoformat() if today.isoformat() in dates else dates[0]
    total_weeks = (RACE - START).days // 7 + 1
    wk = max(1, min(total_weeks, (today - START).days // 7 + 1))
    ring = 2 * 3.1416 * 15
    strip = ""
    for date in dates:
        d = dt.date.fromisoformat(date)
        dots = "".join(f'<i class="dot {s["status"]}" style="--c:{COLOR.get(s["sport"], COLOR["rest"])[1]}"></i>'
                       for s in days if s["date"] == date and s["sport"] != "rest")
        cls = " ".join(c for c in ["day", "today" if d == today else "", "past" if d < today else ""] if c)
        strip += f'<button class="{cls}" data-date="{date}"><span class="dow">{d.strftime("%a").upper()}</span><span class="num">{d.day}</span><span class="dots">{dots}</span></button>'
    heroes = "\n".join(hero(s, today) for s in days)
    work = [s for s in days if s["sport"] != "rest"]
    done = [s for s in work if s["status"] == "done"]
    segs = "".join(f'<i class="seg{" on" if s["status"] == "done" else ""}" style="--c:{COLOR[s["sport"]][1]}"></i>' for s in work)
    hm = lambda m: f"{m // 60}h {m % 60:02d}m" if m >= 60 else f"{m}m"
    mins_done, mins_plan = sum(s["minutes"] for s in done), sum(s["minutes"] for s in work)
    return f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Training">
<meta name="theme-color" content="#12181d">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icon-180.png">
<title>Training HQ</title>
<style>
:root{{color-scheme:dark;--bg:#12181d;--card:#1c242b;--card2:#141b20;--line:#2a343c;--ink:#eef2f0;--mute:#8b98a1;--accent:#6fd39a;--warn:#f0a35a}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:17px/1.4 -apple-system,"SF Pro Text",Helvetica,Arial,sans-serif;
  padding:calc(env(safe-area-inset-top,0px) + 12px) 16px calc(env(safe-area-inset-bottom,0px) + 32px)}}
.top{{display:flex;align-items:center;justify-content:center;gap:12px;margin:4px 0 2px}}
.top svg{{flex:none}}.top h1{{margin:0;font-size:24px;font-weight:700}}
.sub{{text-align:center;color:var(--mute);font-size:14px;margin:0 0 14px}}
.strip{{display:grid;grid-template-columns:repeat(7,1fr);gap:2px;background:var(--card2);border-radius:18px;padding:10px 4px 12px;margin:0 -4px 18px}}
.strip button{{all:unset;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:6px;padding:4px 0}}
.dow{{font-size:12px;color:var(--mute);letter-spacing:.04em}}
.num{{width:40px;height:40px;border-radius:50%;display:grid;place-items:center;font-size:19px;font-weight:600;border:2px solid transparent}}
.day.today .num{{background:var(--ink);color:var(--bg)}}
.day.sel:not(.today) .num{{border-color:var(--mute)}}
.day.past .num{{color:var(--mute)}}
.dots{{display:flex;gap:3px;min-height:9px}}
.dot{{width:9px;height:9px;border-radius:3px;background:var(--c)}}
.dot.planned{{opacity:.95}}.dot.skipped,.dot.modified{{background:transparent;box-shadow:inset 0 0 0 2px var(--c);opacity:.6}}
.dot.done{{box-shadow:0 0 0 2px var(--bg),0 0 0 3px var(--c)}}
.hero{{display:flex;background:var(--card);border:1px solid var(--line);border-radius:22px;overflow:hidden;margin-bottom:14px}}
.hero .bar{{flex:none;width:14px;background:linear-gradient(var(--c1),var(--c2))}}
.hero .body{{padding:20px 20px 22px}}
.hero h2{{margin:0;font-size:28px;line-height:1.15;font-weight:700}}
.when{{margin:6px 0 0;color:var(--mute);font-size:15px}}
.what{{margin:14px 0 0;font-size:17px}}
.note{{margin:10px 0 0;font-size:15px;color:var(--ink);opacity:.85}}
.rec{{margin:12px 0 0;padding:10px 12px;border-radius:12px;background:var(--card2);font-size:14px;color:var(--mute)}}
.rec.low{{color:var(--warn)}}
.badge{{display:inline-block;vertical-align:middle;margin-left:10px;font-size:13px;font-weight:600;padding:3px 8px;border-radius:8px;background:var(--accent);color:var(--bg)}}
.badge.off{{background:var(--line);color:var(--mute)}}
.hero.skipped h2{{text-decoration:line-through;opacity:.6}}
.go{{display:inline-block;margin-top:16px;background:var(--ink);color:var(--bg);text-decoration:none;padding:11px 18px;border-radius:12px;font-weight:600}}
.coach{{background:var(--card2);border-radius:18px;padding:16px 18px;margin-bottom:14px;font-size:15px;line-height:1.5}}
.coach h3{{margin:0 0 6px;font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:var(--accent)}}
.coach p{{margin:0 0 8px}}.coach ul{{margin:0 0 8px;padding-left:20px}}.coach b{{color:var(--ink)}}
.coach details summary{{cursor:pointer;color:var(--mute);font-size:14px;list-style:none;margin-top:2px}}
.coach details[open] summary{{display:none}}
.overview{{background:var(--card);border:1px solid var(--line);border-radius:22px;padding:18px 20px;margin-bottom:14px}}
.overview h3{{margin:0 0 14px;font-size:18px;font-weight:600}}
.segs{{display:flex;gap:6px}}.seg{{flex:1;height:8px;border-radius:4px;background:var(--line)}}.seg.on{{background:var(--c)}}
.stats{{display:flex;justify-content:space-between;margin-top:10px;font-size:15px;color:var(--mute)}}.stats b{{color:var(--ink)}}
.legend{{display:flex;gap:14px;flex-wrap:wrap;margin-top:12px;font-size:13px;color:var(--mute)}}
.legend i{{display:inline-block;width:9px;height:9px;border-radius:3px;margin-right:5px;background:var(--c)}}
.chat{{display:flex;align-items:center;justify-content:center;gap:10px;margin:22px 0 0;padding:16px;border-radius:999px;background:var(--ink);color:var(--bg);text-decoration:none;font-weight:700;font-size:18px}}
.push{{background:var(--card);border:1px dashed var(--line);border-radius:18px;padding:14px 16px;margin-bottom:14px;font-size:15px}}
.push button{{font:inherit;font-weight:600;background:var(--ink);color:var(--bg);border:0;border-radius:10px;padding:10px 16px;margin-top:10px}}
.push textarea{{width:100%;height:96px;margin-top:10px;font:12px ui-monospace,Menlo,monospace;border-radius:8px;border:1px solid var(--line);background:var(--bg);color:var(--ink)}}
.push a{{color:var(--accent)}}[hidden]{{display:none!important}}
.foot{{text-align:center;margin-top:16px;font-size:13px;color:var(--mute)}}.foot a{{color:inherit}}
</style></head><body>
<div class="top">
  <svg width="34" height="34" viewBox="0 0 36 36" aria-hidden="true"><circle cx="18" cy="18" r="15" fill="none" stroke="#2a343c" stroke-width="4"/>
  <circle cx="18" cy="18" r="15" fill="none" stroke="#6fd39a" stroke-width="4" stroke-linecap="round" stroke-dasharray="{ring * wk / total_weeks:.1f} {ring:.1f}" transform="rotate(-90 18 18)"/></svg>
  <h1>Week {wk}/{total_weeks}</h1>
</div>
<p class="sub">Phase {week["phase"]} · {PHASE_NAME.get(week["phase"], "")} · {(RACE - today).days // 7} weeks to Madison</p>
<nav class="strip">{strip}</nav>
<div class="push" id="push-install" hidden>Get the morning brief as a notification: tap <b>Share → Add to Home Screen</b>, then open <b>Training</b> from your home screen.</div>
<div class="push" id="push-ask" hidden>Get the 6am brief as a notification from this app.<br><button id="push-on">Turn on notifications</button></div>
<div class="push" id="push-code" hidden>Last step: copy this code into the GitHub secret <b>PUSH_SUBSCRIPTION</b> (<a href="{SECRETS}">open secrets</a>).
<textarea id="push-json" readonly></textarea><button id="push-copy">Copy code</button></div>
{coach_html()}
{heroes}
<section class="overview">
  <h3>Week {wk} overview</h3>
  <div class="segs">{segs}</div>
  <div class="stats"><span>Sessions: <b>{len(done)}/{len(work)}</b></span><span>Time: <b>{hm(mins_done)}/{hm(mins_plan)}</b></span></div>
  <div class="legend">{"".join(f'<span><i style="--c:{COLOR[k][1]}"></i>{SPORT_LABEL[k]}</span>' for k in ("run", "bike", "strength") if any(s["sport"] == k for s in work))}</div>
</section>
<a class="chat" href="{CHAT}">💬 Ask the coach</a>
<p class="foot"><a href="{REPO}">repo</a> · <a href="#" id="push-show">notification code</a></p>
<script>
// Week strip: tap a day to show its card. Today is selected by default.
const pick = d => {{
  document.querySelectorAll('.hero').forEach(h => h.hidden = h.dataset.date !== d);
  document.querySelectorAll('.strip .day').forEach(b => b.classList.toggle('sel', b.dataset.date === d));
}};
document.querySelectorAll('.strip .day').forEach(b => b.onclick = () => pick(b.dataset.date));
pick("{pick}");
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
