# Handoff: Training HQ → Claude Code

Paste the "Starting prompt" at the bottom as the first message. Commit this file to the repo root as `HANDOFF.md` so future sessions can read it too.

## Who and what

Steve, Evanston IL (60201). Training for IRONMAN 70.3 Wisconsin, Madison, Saturday 11 Sep 2027 (2027 date unconfirmed; 2026 was 12 Sep). This year is about getting fit, finishing, and enjoying it. Not a time goal.

Constraints Steve stated: under 5 hours/week right now; winter block should balance strength and endurance; no pool until spring; cold is fine, wet is not. Has trained for a marathon before. Likes how Runna works and wants that feel: one workout, pushed to the watch, adapts on its own, easy to move.

Apps that run workouts: Runna (run), Fitbod (strength), TrainerRoad planned for the bike. Bike: a Wahoo KICKR from his dad, older generation, direct drive, ERG capable; generation, cassette speed and axle type not yet confirmed. Everything syncs to Strava.

## What we decided, and why

1. **The problem is coordination, not execution.** Runna and Fitbod are great at running a workout. Nothing good coordinates the week across sports for a sub-5-hour athlete, and the indie apps that try (Athletica, IntervalCoach, AI Endurance, Transition) are small and have sync rough edges. Runna's triathlon plans are running-only. JOIN is cycling-only. So we build the thin coordinating layer and nothing else.
2. **Head coach owns the days; apps own the content.** The repo decides which day, what sport, what kind of session, what venue. It never writes intervals. "Runna: easy run, 30 min" is as specific as it gets. Steve sets Runna's and TrainerRoad's training days to match `data/week.json`; that's the one manual sync in the system.
3. **Files are state; conversation is for deciding.** `data/week.json` is the current week. `data/ledger.csv` is append-only, one row per planned session, status planned/done/skipped/modified. `data/decisions.md` logs every change with the reason in Steve's words. `PROFILE.md` changes only through conversation. The site, calendar feed and daily brief are generated from `week.json`, never hand-edited.
4. **Strava is the only read-back.** Everything flows into Strava already, so one Strava read replaces all logging. Runna/Fitbod/TrainerRoad have no public APIs; don't fight that.
5. **Low friction is the whole product.** Steve's words: "I need a low friction thing to look at or do the thing planned or ask for a modification and go." Three verbs: look, do, change. A home-screen page with today first and one tap to the right app, a morning push with one line, and the chat (Claude Code) for anything that needs words.
6. **Weather moves runs.** Outside when precipitation chance < 40% and dry; treadmill otherwise. Coach moves days around weather in winter, not just venues; a dry 45° Thursday in January is worth shifting a strength day for.
7. **Two crons.** Daily 6am CT: weather → venues → rebuild site → ntfy push. Sunday 6pm CT: Strava sync → mark ledger → forecast → open a GitHub issue with the week's data so the review is pre-started.
8. **Not in v1.** TrainingPeaks, Zwift, calendar write-back, charts, Strava import of workout detail, swim anything.

## The year (see PLAN.md for full detail)

- Phase 1, 26 Oct–31 Dec: habit and strength. 2 Fitbod, 2 easy runs, 1 bike once KICKR is live. ~4–4.5 h. No intensity.
- Phase 2, Jan–Mar: engine. TrainerRoad low-volume plan is the spine, 2 runs, strength 1–2×. 5–6 h.
- Phase 3, Apr–Jun: three sports. Pool opens, bike outdoors, Runna 70.3 plan starts ~May, tune-up race in June.
- Phase 4, Jul–race: specific. Long rides to 3 h, bricks, open water, 2-week taper.

Week one starts Mon 26 Oct 2026 and is already in `data/week.json`.

## What's in the repo and its state

- `CLAUDE.md`, `COACH.md` — read first. COACH.md is the standing instruction set for the coach.
- `PROFILE.md`, `PLAN.md`, `README.md` — context, plan, architecture and setup checklist.
- `data/week.json`, `data/ledger.csv`, `data/decisions.md` — seeded with week one and the decisions above.
- `scripts/build_site.py` — **tested**, renders `site/index.html` and `site/week.ics`.
- `scripts/weather.py` (Open-Meteo), `scripts/daily_brief.py` (ntfy), `scripts/strava_sync.py` — **written against documented APIs, never run**. Expect to debug each against a real response.
- `.github/workflows/daily.yml`, `sunday.yml` — written, never run. Cron hours are set for CDT; CST shift in November is unhandled.
- The app URL schemes in `build_site.py` (`runna://`, `trainerroad://`, `fitbod://`) are guesses. Verify on the phone.

## Open items Steve still owes

Current weekly run mileage and last race; injuries or anything fragile; off-limit days; KICKR generation, cassette speed vs his bike, axle type. Ask once, when natural, not all at once.

## Secrets and settings needed from Steve, in order

1. GitHub Pages enabled from `main`, folder `/site`. Then `SITE_URL` as a repo variable.
2. `NTFY_TOPIC` (he picks a private topic name, subscribes in the ntfy app).
3. Strava API app → `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, `STRAVA_REFRESH_TOKEN` (scope `activity:read_all`).

---

## Starting prompt

Read HANDOFF.md, then CLAUDE.md, then COACH.md, then PROFILE.md, PLAN.md and everything in data/. You are the head coach for this repo and its maintainer; HANDOFF.md explains the thinking behind every decision so far.

Today's job is to make the system real, in this order, and stop to ask me for anything only when you actually need it:

1. Run scripts/build_site.py and confirm the site renders. Tell me how to enable GitHub Pages from /site and what SITE_URL to set.
2. Run scripts/weather.py against the real Open-Meteo API, fix whatever breaks, and show me this week's venue decisions. Apply them to data/week.json if they differ.
3. Get scripts/daily_brief.py working. Ask me for an ntfy topic name when you reach it.
4. Walk me through the Strava API app setup and the one-time OAuth, then get scripts/strava_sync.py working against my real activities.
5. Make the two workflows run clean on workflow_dispatch before trusting the schedules.

Rules: edit data files surgically, append to the ledger and decisions log, log every plan change with the reason, and don't propose a schedule you haven't written to week.json. Commit as you go with short messages. When you're done, tell me in one line what tomorrow's session is and whether it's outside.
