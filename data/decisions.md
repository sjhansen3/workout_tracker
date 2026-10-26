# Decisions

## 2026-10-25
- Plan starts Mon 26 Oct. Four phases to race day, under 5 h/week in phase 1. Steve: "for now this is about getting fit and having goals and sub goals."
- Winter block is balanced strength and endurance, not strength-first. Steve's choice.
- No swimming until pool access in spring. Steve's constraint.
- Runs go outside when dry; treadmill when wet. Steve: "I can run in cold but wet kinda sucks."
- Bike sessions depend on the KICKR being set up (generation, cassette, axle unconfirmed). Until then, Wednesday's bike becomes a second easy run.
- Architecture: this repo is the head coach; Runna/Fitbod/TrainerRoad run workouts; Strava is the only read-back; weather from Open-Meteo; daily brief via ntfy; site on GitHub Pages; two crons (daily brief, Sunday review).

## 2026-10-26
- Site publishes from `docs/`, not `site/`: GitHub Pages can only serve a branch's root or `/docs`. No plan change.
- Crons hold 6:00 / Sun 18:00 Chicago through the November clock change (each fires at both UTC hours; a gate keeps the right one). No plan change.
- Weather check, first live run: Tue and Sat runs stay outside (dry, 50s–60s°F). No change to the week.
- ntfy and Google Calendar do different jobs; no duplication. ntfy is the one morning nudge, with buttons to the week and to the coach chat. Steve: "calendar is just a different thing." The calendar shows the plan and carries no reminders.
- The coach can read Steve's Runna, personal and work calendars in chat sessions (Google Calendar connector). Crons can't yet; that needs a service account.
