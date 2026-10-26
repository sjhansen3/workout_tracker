"""Log one morning's recovery numbers from Apple Health into data/health.csv.

The iPhone Shortcut (see HEALTH.md) posts a repository_dispatch with client_payload
{"sleep": ..., "rhr": ..., "hrv": ...}; .github/workflows/health.yml passes it here as HEALTH_PAYLOAD.
Shortcuts hands over values in loose shapes ("52 count/min", "7 hr 12 min", seconds), so parsing is forgiving.
Standard library only.
"""
import csv, json, os, re, statistics, datetime as dt

PATH = "data/health.csv"
COLS = ["date", "sleep_h", "rhr", "hrv"]

def first_number(v):
    if isinstance(v, list):
        nums = [first_number(x) for x in v]
        nums = [n for n in nums if n is not None]
        return sum(nums) if nums else None
    if isinstance(v, (int, float)):
        return float(v)
    m = re.search(r"-?\d+(?:\.\d+)?", str(v or ""))
    return float(m.group()) if m else None

def sleep_hours(v):
    s = str(v or "")
    hm = re.search(r"(\d+)\s*h(?:r|ours?)?\D+(\d+)\s*m", s)
    if hm:
        return int(hm.group(1)) + int(hm.group(2)) / 60
    n = first_number(v)
    if n is None:
        return None
    # Unitless: guess from size. Seconds (a night is ~20-40k), minutes (~300-600), or hours.
    return n / 3600 if n > 1000 else n / 60 if n > 24 else n

def read():
    if not os.path.exists(PATH):
        return []
    return list(csv.DictReader(open(PATH)))

def write(rows):
    with open(PATH, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, lineterminator="\n"); w.writeheader(); w.writerows(rows)

def recovery(today, rows=None):
    """One-line summary for the brief, plus whether to flag low recovery against the last 7 days."""
    rows = rows if rows is not None else read()
    day = next((r for r in rows if r["date"] == today), None)
    if not day:
        return None, False
    prior = [r for r in rows if r["date"] < today][-7:]
    med = lambda k: statistics.median([float(r[k]) for r in prior if r[k]]) if sum(1 for r in prior if r[k]) >= 4 else None
    bits, low = [], []
    if day["sleep_h"]:
        bits.append(f"Slept {float(day['sleep_h']):.1f}h")
        if float(day["sleep_h"]) < 6:
            low.append("short sleep")
    if day["rhr"]:
        bits.append(f"RHR {float(day['rhr']):.0f}")
        if (m := med("rhr")) and float(day["rhr"]) > m + 5:
            low.append("resting HR up")
    if day["hrv"]:
        bits.append(f"HRV {float(day['hrv']):.0f}")
        if (m := med("hrv")) and float(day["hrv"]) < 0.8 * m:
            low.append("HRV down")
    line = " · ".join(bits)
    if low:
        line += f"\nLow recovery ({', '.join(low)}): keep it easy, or ask the coach to swap."
    return line, bool(low)

def main():
    p = json.loads(os.environ.get("HEALTH_PAYLOAD") or "{}")
    today = p.get("date") or dt.date.today().isoformat()
    row = {"date": today,
           "sleep_h": f"{h:.2f}" if (h := sleep_hours(p.get("sleep"))) else "",
           "rhr": f"{n:.0f}" if (n := first_number(p.get("rhr"))) else "",
           "hrv": f"{n:.0f}" if (n := first_number(p.get("hrv"))) else ""}
    rows = [r for r in read() if r["date"] != today] + [row]  # one row per day; a re-run replaces it
    rows.sort(key=lambda r: r["date"])
    write(rows)
    print(f"logged {row}")
    line, low = recovery(today, rows)
    print(line or "")
    # Arrived after the 6am brief went out? Only ping again if it matters.
    if low and os.environ.get("PUSH_SUBSCRIPTION") and os.environ.get("VAPID_PRIVATE_KEY"):
        import daily_brief
        daily_brief.send("⚠️ Low recovery", line)
        print("sent low-recovery push")

if __name__ == "__main__":
    main()
