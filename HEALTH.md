# Apple Health → coach

Apple Health has no cloud API, so the phone sends last night's numbers itself. Once a morning, a Shortcut posts sleep, resting heart rate and HRV to this repo. `.github/workflows/health.yml` logs them in `data/health.csv`. The brief and today's card then show a recovery line, and flag low recovery. Workouts don't go this way; they come through Strava.

## 1. A GitHub token for the phone (once)

github.com → Settings → Developer settings → **Fine-grained tokens** → Generate new token.
- Name: `training shortcut`. Expiration: 1 year.
- Repository access: **Only select repositories** → `workout_tracker`.
- Permissions → Repository → **Contents: Read and write**. Nothing else.
- Generate, and copy it **on the phone**. It only goes into the Shortcut, never into chat.

## 2. The Shortcut

Shortcuts app → **Automation** → **+** → **Focus** → **Sleep** → tick **When Turning Off** (untick When Turning On) → **Run Immediately** → Next → New Blank Automation. Add these actions:

1. **Find Health Samples**: Type **Sleep Analysis**. Add filters: *Start Date is in the last 12 hours*, *Value is not In Bed*, *Value is not Awake*.
2. **Get Details of Health Samples**: **Duration** (of the result above).
3. **Calculate Statistics**: **Sum** (of the Durations).
4. **Find Health Samples**: Type **Resting Heart Rate**, *Start Date is in the last 1 days*, Sort by **Start Date**, **Latest First**, Limit **1**.
5. **Find Health Samples**: Type **Heart Rate Variability**, same filters as step 4.
6. **Get Contents of URL**:
   - URL: `https://api.github.com/repos/sjhansen3/workout_tracker/dispatches`
   - Method: **POST**
   - Headers: `Authorization` = `Bearer ` + your token · `Accept` = `application/vnd.github+json`
   - Request Body: **JSON**
     - `event_type` (Text) = `health`
     - `client_payload` (Dictionary):
       - `sleep` = *Statistics* (step 3)
       - `rhr` = *Health Samples* (step 4)
       - `hrv` = *Health Samples* (step 5)

Tap ▶︎ once to test, then ask the coach to check it landed (Actions → **health** run, `data/health.csv`).

## Notes
- The receiver accepts loose shapes: "52 count/min", "7 hr 12 min", seconds, lists. If a value comes through odd, the coach fixes the parser; you don't change the Shortcut.
- Why "Sleep Focus turns off" and not a fixed time: iOS locks Health data while the phone is locked, so a timed run can find nothing. Sleep Focus ending means Steve is up and about to unlock. If numbers arrive after the 6am brief, they still show on today's card, and you get one extra push only when recovery is low.
- Low recovery means sleep under 6 h, resting HR more than 5 above your 7-day median, or HRV under 80% of it. The flag is advice, not an automatic plan change.
