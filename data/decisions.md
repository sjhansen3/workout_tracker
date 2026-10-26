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
- Morning brief comes from the site itself (installed as "Training", own icon) instead of ntfy. Steve wanted it to look cooler and not come from ntfy. iOS web push can't show buttons, so tapping opens the week, which has an "Ask the coach" link.
- Steve ran the Chicago Marathon (11 Oct) and hasn't run since. Week one stays as written: easy volume is the right restart two weeks out. Runna's Tue progression run and next week's repeats are too much for phase 1; Steve to switch Runna to easy runs on Tue/Sat.
- Secrets go straight from Steve's computer into GitHub via `scripts/setup_secrets.py`, never through chat. Steve: "isnt that safer?" The keys pasted in chat today are retired: a new notification keypair, and a regenerated Strava client secret.
- 2026-10-26 (auto, Runna owns run days): Sat run dropped: not in Runna.
- 2026-10-26 (auto, Runna owns run days): Fitbod full body moved Mon→Sat for Runna's run.
- 2026-10-26 (auto, Runna owns run days): Mon run added from Runna: "3mi Easy Run", 30 min.
- 2026-10-26 (auto, Runna owns run days): Tue run now Runna's "4.5mi Progressive Long Run", 45 min.
- Runna owns run days; the repo follows Runna's calendar and moves strength/bike around it. Steve: "this is the sorta thing thats unhelpful to do. its systems fighting each other." Replaces the manual "set Runna's training days" step from the handoff. Wednesday's no-KICKR fallback is now a day off instead of an extra run, since runs come from Runna.
- Runna dropped. Steve: "the issue is you need to be able to schedule things. honestly I am tempted to dump runna." Phase 1 runs are easy and unstructured, recorded on the watch. Week restored to the coach's plan: Fitbod tonight, easy 30 Tue, easy 45 Sat. Rule from now on: any app we use takes its schedule from the repo.
- Bike tooling deferred to a mid-December checkpoint. Phase 1 rides are a single easy 45 min a week and need no app to run them. Steve: "holy complexity."
- Page redesigned like Runna's Today view (week strip with sport-colour dots, today's card with a colour bar, week overview). Steve: "i really like this bar with color coding."
- "Ask the coach" opens one standing Claude Code session ("Coach") on this repo, not a blank chat. Steve: "just opens claude app - not any conversation with any history or context."
- The home page gets a "From the coach" card (data/coach.md): the coach's own words on what's going on and why, rewritten whenever something changes. Steve: "we are missing a connection to the coach - leave it pretty wide open since we are going pretty ai first."
- Weekly AI review: a Claude Code routine ("Coach: Sunday review", Sun 18:45 Chicago) wakes the Coach session after the Strava sync. It decides, writes next week, rewrites the coach note and pushes, without asking or messaging. No AI runs mid-week. Steve: "idk if we want smart ai running in a loop without me in it because that becomes a nag."
- Apple Health Shortcut shelved. Steve: "we already have strava... what new info is here that strava doesnt have?" It only adds recovery (sleep/RHR/HRV), which matters little while phase 1 is all easy work. The receiver stays in the repo, dormant (no data = no recovery line). Revisit in spring if intensity makes recovery worth tracking. "I'm wrecked" in chat is the recovery signal for now.
- Check-in: week one load is about right (Steve). No days off-limits; the Tuesday "Trainer" calendar event is from an old trainer. Race is probably 70.3 Wisconsin, 11 Sep 2027, not registered yet. Steve has "something minor" to protect; details pending.
