"""Hevy: the coach writes strength sessions in, and reads back what Steve lifted.

    python scripts/hevy.py whoami                       checks the key (prints name, unit, pro)
    python scripts/hevy.py push data/hevy/2026-10-29.json   creates the routine, or updates the one with the same title
    python scripts/hevy.py pull [days]                  prints workouts from the last N days (default 7)
    python scripts/hevy.py find "goblet"                searches Hevy's exercise templates by name

Needs HEVY_API_KEY (Hevy Pro; hevy.com → Settings → Developer; stored via scripts/setup_secrets.py hevy).
Runs in the `hevy` workflow, where the secret lives. The API can't delete: a wrong routine is removed by hand in the app.

Session file, kept in data/hevy/<date>.json. Weights in lb (Steve's unit); converted to kg for the API.
{
  "title": "Thu 29 Oct · Full body",
  "notes": "shown at the top of the routine",
  "exercises": [
    {"name": "Goblet Squat", "sets": "3x10", "lb": 30, "rest": 90, "note": "shown under the exercise"},
    {"name": "Plank", "sets": "3x30s", "rest": 45}
  ]
}
`sets`: "3x10", "3x8-12" (rep range), "3x30s" (seconds). `lb` optional: leave it out and Steve picks the weight in the app.
`warmup`: "1x8" adds warm-up sets first. `name` must match a Hevy exercise title (case-insensitive); `find` helps.
"""
import datetime as dt, json, os, re, sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

API = "https://api.hevyapp.com/v1"
LB = 0.45359237

def call(method, path, body=None, **params):
    key = os.environ.get("HEVY_API_KEY")
    if not key:
        sys.exit("HEVY_API_KEY is not set")
    q = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
    req = Request(f"{API}{path}{'?' + q if q else ''}", method=method,
                  data=json.dumps(body).encode() if body is not None else None,
                  headers={"api-key": key, "accept": "application/json", "content-type": "application/json"})
    try:
        with urlopen(req, timeout=30) as r:
            return json.load(r)
    except HTTPError as e:
        sys.exit(f"{method} {path} → {e.code}: {e.read().decode()[:500]}")

def pages(path, item_key, page_size=10, **params):
    """Walk a paginated list endpoint (page / page_count). Hevy caps pageSize at 10, except exercise templates (100)."""
    page = 1
    while True:
        j = call("GET", path, page=page, pageSize=page_size, **params)
        yield from j.get(item_key, [])
        if page >= j.get("page_count", 1):
            return
        page += 1

def templates():
    return list(pages("/exercise_templates", "exercise_templates", page_size=100))

def resolve(name, cache):
    """Exact title match first (case-insensitive), then a single substring match; otherwise fail with candidates."""
    n = name.lower().strip()
    exact = [t for t in cache if t["title"].lower() == n]
    if exact:
        return exact[0]
    near = [t for t in cache if n in t["title"].lower()]
    if len(near) == 1:
        return near[0]
    sys.exit(f'no unique Hevy exercise for "{name}": ' + (", ".join(t["title"] for t in near[:12]) or "nothing close"))

def parse_sets(spec, lb=None, kind="normal"):
    """'3x10' → 3 sets of 10; '3x8-12' → rep range; '3x30s' → 30 seconds."""
    m = re.fullmatch(r"(\d+)x(\d+)(?:-(\d+))?(s?)", spec.replace(" ", ""))
    if not m:
        sys.exit(f"bad sets spec: {spec}")
    n, a, b, secs = int(m[1]), int(m[2]), m[3], m[4]
    out = []
    for _ in range(n):
        s = {"type": kind, "weight_kg": round(lb * LB, 2) if lb else None, "reps": None,
             "distance_meters": None, "duration_seconds": None, "custom_metric": None, "rep_range": None}
        if secs:
            s["duration_seconds"] = a
        elif b:
            s["rep_range"] = {"start": a, "end": int(b)}
        else:
            s["reps"] = a
        out.append({k: v for k, v in s.items() if v is not None})  # PUT rejects rep_range: null
    return out

def build(session, cache):
    exercises = []
    for e in session["exercises"]:
        t = resolve(e["name"], cache)
        sets = parse_sets(e["warmup"], e.get("warmup_lb"), "warmup") if e.get("warmup") else []
        sets += parse_sets(e["sets"], e.get("lb"))
        exercises.append({"exercise_template_id": t["id"], "superset_id": e.get("superset"),
                          "rest_seconds": e.get("rest", 60), "notes": e.get("note"), "sets": sets})
        print(f'  {t["title"]}: {len(sets)} sets' + (f' @ {e["lb"]} lb' if e.get("lb") else ""))
    return {"routine": {"title": session["title"], "folder_id": None, "notes": session.get("notes", ""), "exercises": exercises}}

def push(path):
    session = json.load(open(path))
    print(f'routine "{session["title"]}"')
    body = build(session, templates())
    existing = [r for r in pages("/routines", "routines") if r["title"] == session["title"]]
    if existing:
        r = call("PUT", f"/routines/{existing[0]['id']}", body)["routine"]
        print(f"updated routine {r['id']}")
    else:
        r = call("POST", "/routines", body)["routine"]
        print(f"created routine {r['id']}")

def pull(days=7):
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)).isoformat()
    for w in pages("/workouts", "workouts"):
        if w["start_time"] < since:
            break
        mins = (dt.datetime.fromisoformat(w["end_time"].replace("Z", "+00:00"))
                - dt.datetime.fromisoformat(w["start_time"].replace("Z", "+00:00"))).seconds // 60
        print(f"{w['start_time'][:10]}  {w['title']}  {mins} min")
        for e in w["exercises"]:
            done = [s for s in e["sets"] if s.get("type") != "warmup"]
            lifted = sorted({f"{s['weight_kg'] / LB:.0f}" for s in done if s.get("weight_kg")})
            reps = "/".join(str(s["reps"]) for s in done if s.get("reps") is not None)
            secs = "/".join(f"{s['duration_seconds']}s" for s in done if s.get("duration_seconds"))
            print(f"    {e['title']}: {len(done)} sets  {reps or secs}" + (f"  @ {'/'.join(lifted)} lb" if lifted else ""))

def whoami():
    u = call("GET", "/user/info")["data"]
    print(f"{u.get('name')} (@{u.get('username')})  unit={u.get('weight_unit')}  pro={u.get('is_pro')}")

def find(q):
    for t in templates():
        if q.lower() in t["title"].lower():
            print(f"{t['id']}  {t['title']}  [{t['primary_muscle_group']}, {t['equipment']}]")

if __name__ == "__main__":
    cmd, args = (sys.argv[1] if len(sys.argv) > 1 else "whoami"), sys.argv[2:]
    {"whoami": lambda: whoami(), "push": lambda: push(args[0]), "find": lambda: find(" ".join(args)),
     "pull": lambda: pull(int(args[0]) if args else 7)}[cmd]()
