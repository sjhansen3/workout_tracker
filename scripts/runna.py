"""Runna owns the run days. Read Runna's calendar and fit the week around it.

Usage: python scripts/runna.py                 # reads RUNNA_ICS_URL
       python scripts/runna.py --ics FILE      # reads a local .ics (testing)

For every day from today to the end of week.json:
- Runna has a run, the plan doesn't  → add it (Runna's name and duration). A strength/bike session
  already on that day moves to the nearest free day, avoiding back-to-back same sport.
- The plan has a Runna run, Runna doesn't → drop it (ledger row marked modified, never deleted).
- Both have a run → take Runna's name and duration.
Past days and anything not 'planned' are never touched. Every change is logged in data/decisions.md.
"""
import csv, json, os, re, sys, datetime as dt
import requests
from weather import dump_week

def fetch(argv):
    if "--ics" in argv:
        return open(argv[argv.index("--ics") + 1]).read()
    url = os.environ.get("RUNNA_ICS_URL")
    if not url:
        print("::warning::RUNNA_ICS_URL not set; leaving run days as planned.")
        return None
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.text

def parse(ics):
    """All-day Runna events -> {date: {title, minutes}}. Minimal iCal: unfold lines, read VEVENTs."""
    lines = re.sub(r"\r?\n[ \t]", "", ics).splitlines()
    out, ev = {}, None
    for line in lines:
        if line == "BEGIN:VEVENT":
            ev = {}
        elif line == "END:VEVENT" and ev is not None:
            d = ev.get("DTSTART", "")[:8]
            if len(d) == 8 and d.isdigit():
                date = f"{d[:4]}-{d[4:6]}-{d[6:]}"
                # "🏃 3mi Easy Run • 3mi" -> "3mi Easy Run"
                title = re.sub(r"^\W+", "", ev.get("SUMMARY", "Run").split(" • ")[0]).strip() or "Run"
                # "Easy Run • 3mi • 30m - 40m" -> 30 (the low end of Runna's range)
                desc = ev.get("DESCRIPTION", "").replace("\\n", "\n").replace("\\,", ",")
                m = re.search(r"(?:(\d+)h)?(\d+)m\b", desc.split("\n")[0])
                minutes = (int(m.group(1) or 0) * 60 + int(m.group(2))) if m else 0
                out[date] = {"title": title, "minutes": minutes}
            ev = None
        elif ev is not None and ":" in line:
            k, v = line.split(":", 1)
            ev.setdefault(k.split(";")[0], v)
    return out

def apply(week, runs, today):
    days = week["days"]
    dates = sorted({d["date"] for d in days})
    window = [d for d in dates if d >= today]
    changes, ledger_ops = [], []
    planned = lambda d: d["status"] == "planned" and d["date"] >= today
    runna_run = lambda d: d["sport"] == "run" and d["app"] == "runna"
    on = lambda date: [d for d in days if d["date"] == date]
    dow = lambda date: dt.date.fromisoformat(date).strftime("%a")

    def make_rest(date):
        if not on(date):
            days.append({"date": date, "sport": "rest", "app": "none", "title": "Off", "minutes": 0,
                         "venue": "home", "status": "planned", "note": ""})
            ledger_ops.append(("add", days[-1]))

    # 1. Runs the plan has but Runna doesn't: drop.
    for d in [d for d in days if planned(d) and runna_run(d) and d["date"] not in runs]:
        days.remove(d)
        ledger_ops.append(("modified", d, "Runna has no run this day"))
        changes.append(f"{dow(d['date'])} run dropped: not in Runna")

    # 2. Runs Runna has: add or update, moving whatever else is on that day.
    for date in window:
        if date not in runs:
            continue
        r = runs[date]
        mine = [d for d in on(date) if runna_run(d)]
        if mine:
            d = mine[0]
            if planned(d) and (d["title"], d["minutes"]) != (r["title"], r["minutes"]):
                changes.append(f"{dow(date)} run now Runna's \"{r['title']}\", {r['minutes']} min")
                d["title"], d["minutes"] = r["title"], r["minutes"]
                ledger_ops.append(("update", d))
            continue
        for other in [d for d in on(date) if planned(d)]:
            if other["sport"] == "rest":
                days.remove(other)
                ledger_ops.append(("modified", other, "replaced by Runna run"))
                continue
            # Move to the nearest free day (no session, or only rest), not next to the same sport.
            free = [x for x in window if x != date and x not in runs
                    and all(d["sport"] == "rest" and planned(d) for d in on(x))]  # empty days count as free
            def score(x):
                i = dates.index(x)
                near = {d["sport"] for n in (i - 1, i + 1) if 0 <= n < len(dates) for d in on(dates[n])}
                return (other["sport"] in near, abs(i - dates.index(date)), x)
            if not free:
                changes.append(f"{dow(date)} Runna run doubles up with {other['title']} (no free day)")
                continue
            to = min(free, key=score)
            for rest in on(to):
                days.remove(rest)
                ledger_ops.append(("modified", rest, f"replaced by {other['title']} moved from {date}"))
            ledger_ops.append(("modified", dict(other), f"moved to {to} (Runna run on {date})"))
            other["date"] = to
            other["note"] = (other["note"] + f" Moved from {dow(date)}: Runna run that day.").strip()
            ledger_ops.append(("add", other))
            changes.append(f"{other['title']} moved {dow(date)}→{dow(to)} for Runna's run")
        new = {"date": date, "sport": "run", "app": "runna", "title": r["title"], "minutes": r["minutes"],
               "venue": "outside", "status": "planned", "note": ""}
        days.append(new)
        ledger_ops.append(("add", new))
        changes.append(f"{dow(date)} run added from Runna: \"{r['title']}\", {r['minutes']} min")
    for date in window:  # any day left empty becomes a rest day
        make_rest(date)
    days.sort(key=lambda d: (d["date"], d["sport"] == "rest"))
    return changes, ledger_ops

def write_ledger(ops, path="data/ledger.csv"):
    rows = list(csv.DictReader(open(path)))
    cols = list(rows[0].keys())
    def find(d):
        return next((r for r in rows if r["date"] == d["date"] and r["sport"] == d["sport"]
                     and r["app"] == d["app"] and r["status"] == "planned"), None)
    for op in ops:
        d = op[1]
        if op[0] == "add":
            rows.append({"date": d["date"], "sport": d["sport"], "app": d["app"], "title": d["title"],
                         "minutes": str(d["minutes"]), "venue": d["venue"], "status": "planned", "rpe": "", "note": ""})
        elif op[0] == "update" and (r := find(d)):
            r["title"], r["minutes"] = d["title"], str(d["minutes"])
        elif op[0] == "modified" and (r := find(d)):
            r["status"] = "modified"
            r["note"] = (r["note"] + " " + op[2]).strip()
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n"); w.writeheader(); w.writerows(rows)

def main():
    ics = fetch(sys.argv)
    if ics is None:
        return
    runs = parse(ics)
    week = json.load(open("data/week.json"))
    today = dt.date.today().isoformat()
    changes, ops = apply(week, runs, today)
    if not changes:
        print("Runna and the plan agree.")
        return
    dump_week(week)
    write_ledger(ops)
    with open("data/decisions.md", "a") as f:
        f.write("".join(f"- {today} (auto, Runna owns run days): {c}.\n" for c in changes))
    print("\n".join(changes))

if __name__ == "__main__":
    main()
