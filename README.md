# Training HQ

Head-coach layer for a 70.3 build. Apps run the workouts; this repo owns the week.

**Race:** IRONMAN 70.3 Wisconsin, Madison — Saturday 11 Sep 2027 (2027 date unconfirmed; 2026 was 12 Sep). Confirm at ironman.com and update `PROFILE.md`.

## The one rule

The head coach decides *which days* and *what kind* of session. The apps decide the *content* and run it.

| Sport    | App         | Who picks the day | Who writes the workout | Result lands in |
|----------|-------------|-------------------|------------------------|-----------------|
| Run      | Watch (phase 1) | this repo     | this repo (easy, unstructured) | Strava |
| Bike     | TrainerRoad | this repo         | TrainerRoad            | Strava          |
| Strength | Fitbod      | this repo         | Fitbod                 | Strava (via Apple Health) |
| Swim     | TBD (spring)| this repo         | TBD                    | Strava          |

The repo decides every day. Any app we use must take its schedule from the repo, never own one of its own.

## Files that are the source of truth

- `PROFILE.md` — who the athlete is. Edited only through coaching conversations.
- `PLAN.md` — the year: phases, sub-goals, rules.
- `COACH.md` — standing instructions for every Claude Code session.
- `data/week.json` — the current week. The site, the calendar feed and the daily brief are all generated from this.
- `data/ledger.csv` — one row per planned session, append-only. Status: planned / done / skipped / modified.
- `data/decisions.md` — dated log of why the plan changed.

## Integrations (and what each one actually costs)

**Weather — Open-Meteo.** Free, no key. `scripts/weather.py` pulls the 7-day forecast for Evanston and decides outside/treadmill per run using the rule in `PROFILE.md`. Used by the daily brief and the Sunday review.

**Strava — read completed activities.** Register an API app at strava.com/settings/api (free). OAuth once, store refresh token as a repo secret. `scripts/strava_sync.py` pulls the last 7 days of activities and marks matching ledger rows done. This is the only integration that needs setup; everything flows into Strava already, so it's the one read that replaces all logging.

**Fitbod / TrainerRoad — no API.** Don't fight it. They're execution-only. Their output reaches us through Strava.

**Delivery — web push from the site.** The site installs to the home screen as "Training" and sends its own notifications (iOS 16.4+), no third-party app. One-time: open Training from the home screen, tap "Turn on notifications", paste the code into the `PUSH_SUBSCRIPTION` secret. `VAPID_PRIVATE_KEY` is the matching signing key. Tapping the notification opens the week.

**Site — GitHub Pages.** `scripts/build_site.py` renders `data/week.json` into `docs/index.html` (today-first, tap to open the right app, links back here for chat) and `docs/week.ics`. Subscribe to the `.ics` from the iPhone calendar and the week shows up there too, no sync code.

**Chat — Claude Code in this repo.** Every session starts by reading `COACH.md`. The coach edits the data files directly, logs decisions, and commits. The Sunday review is a Claude Code session the cron opens for you.

## Crons (`.github/workflows/`)

- `daily.yml` — 6:00 CT every day: weather → decide venues → rebuild site → web push brief.
- `sunday.yml` — 18:00 CT Sundays: strava sync → mark ledger → rebuild site → draft next week into `data/week.next.json` and open an issue titled "Week of …" with the draft for review.

## Setup checklist

1. Push this repo. Enable GitHub Pages: deploy from branch `main`, folder `/docs`.
2. `pip install -r requirements.txt`; run `python scripts/build_site.py` locally to confirm it renders.
3. On your computer, run `python3 scripts/setup_secrets.py` (needs `gh auth login`). It sets SITE_URL, a fresh notification keypair, and the Strava secrets straight into GitHub; nothing gets pasted into chat. Create the Strava API app at strava.com/settings/api first.
4. On the phone: add the site to the home screen, open it from there, tap "Turn on notifications", and save the code as the `PUSH_SUBSCRIPTION` secret.
5. Add the site to the iPhone home screen (Share → Add to Home Screen). Subscribe to `week.ics`.
7. Identify the KICKR generation, check cassette speed vs your bike, check axle type.
