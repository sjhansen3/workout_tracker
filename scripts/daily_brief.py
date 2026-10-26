"""Compose today's brief from data/week.json and push it to the phone as a web push.

The notification comes from the site itself (installed to the home screen as "Training"),
not from a third-party app. Tapping it opens the week page.

Env: PUSH_SUBSCRIPTION (the JSON the site shows after "Turn on notifications"),
     VAPID_PRIVATE_KEY, SITE_URL. Without the first two it just prints the brief.
Run weather.py --apply before this so venues are current.
"""
import json, os, sys, datetime as dt

APP_NAME = {"runna": "Runna", "trainerroad": "TrainerRoad", "fitbod": "Fitbod"}
EMOJI = {"run": "🏃", "bike": "🚴", "strength": "🏋️", "swim": "🏊", "rest": "😴"}
RACE = dt.date(2027, 9, 11)
SITE = os.environ.get("SITE_URL") or "https://sjhansen3.github.io/workout_tracker/"

def weather_bit(date):
    # Best effort: a failed forecast never blocks the brief.
    try:
        import weather
        f = weather.forecast().get(date)
    except Exception as e:
        print(f"weather unavailable: {e}", file=sys.stderr)
        return ""
    if not f:
        return ""
    sky = "dry" if weather.decide(f) == "outside" else f"wet, rain {f['precip_prob']}%"
    return f"{f['lo']:.0f}–{f['hi']:.0f}°F {sky}"

def compose(week, today):
    s = next((x for x in week["days"] if x["date"] == today.isoformat()), None)
    weeks = f"{(RACE - today).days // 7} weeks to Madison"
    dow = today.strftime("%a")
    if not s:
        return "📋 No plan for today", f"Time for a Sunday review · {weeks}"
    if s["sport"] == "rest":
        return f"😴 {dow} · {s['title']}", " · ".join(x for x in [s["note"], weeks] if x)
    app = APP_NAME.get(s["app"], s["app"])
    what = s["title"].removeprefix(app).strip()
    title = f"{EMOJI.get(s['sport'], '•')} {dow} · {what[0].upper() + what[1:]}, {s['minutes']} min"
    where = s["venue"]
    if s["sport"] in ("run", "bike") and s["venue"] == "outside":
        w = weather_bit(s["date"])
        where = f"outside, {w}" if w else where
    body = " · ".join([app, where, weeks])
    if s["note"]:
        body += f"\n{s['note']}"
    return title, body

def send(title, body):
    from pywebpush import webpush, WebPushException
    try:
        webpush(subscription_info=json.loads(os.environ["PUSH_SUBSCRIPTION"]),
                data=json.dumps({"title": title, "body": body, "url": SITE}),
                vapid_private_key=os.environ["VAPID_PRIVATE_KEY"],
                vapid_claims={"sub": SITE.rstrip("/")}, ttl=12 * 3600)
    except WebPushException as e:
        code = getattr(e.response, "status_code", None)
        if code in (404, 410):
            sys.exit("::error::Phone subscription expired. Open Training on the phone, tap 'Turn on notifications', "
                     "and paste the new code into the PUSH_SUBSCRIPTION secret.")
        raise

def main():
    week = json.load(open("data/week.json"))
    title, body = compose(week, dt.date.today())
    print(title); print(body)
    if os.environ.get("PUSH_SUBSCRIPTION") and os.environ.get("VAPID_PRIVATE_KEY"):
        send(title, body)
        print("sent")
    else:
        print("::warning::PUSH_SUBSCRIPTION / VAPID_PRIVATE_KEY not set; brief not sent.")

if __name__ == "__main__":
    main()
