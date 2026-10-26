"""One-time setup, run on your own computer. Puts every key straight into GitHub; nothing is pasted into chat.

    brew install gh && gh auth login        # once
    pip3 install requests cryptography
    python3 scripts/setup_secrets.py         # all steps
    python3 scripts/setup_secrets.py strava  # or just one: site | push | strava | runna

site    sets SITE_URL.
push    makes a fresh notification keypair: VAPID_PRIVATE_KEY (secret) + VAPID_PUBLIC_KEY (variable),
        then rebuilds the site so the page uses the new key. Re-tap "Turn on notifications" afterwards.
runna   stores RUNNA_ICS_URL, the private iCal address of the Runna calendar, so the coach can follow Runna's run days.
strava  asks for the Client ID/Secret (hidden), opens Strava to authorize, and stores
        STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN.
"""
import base64, getpass, subprocess, sys, webbrowser
from urllib.parse import urlsplit, parse_qs

REPO = "sjhansen3/workout_tracker"
SITE = "https://sjhansen3.github.io/workout_tracker/"

def gh(*args, value=None):
    subprocess.run(["gh", *args, "-R", REPO], input=value, text=True, check=True, capture_output=value is not None)

def secret(name, value):
    gh("secret", "set", name, value=value)  # value goes over stdin, never on the command line
    print(f"  secret   {name} set")

def variable(name, value):
    gh("variable", "set", name, "--body", value)
    print(f"  variable {name} set")

def site():
    variable("SITE_URL", SITE)

def push():
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import serialization
    b64 = lambda b: base64.urlsafe_b64encode(b).rstrip(b"=").decode()
    key = ec.generate_private_key(ec.SECP256R1())
    secret("VAPID_PRIVATE_KEY", b64(key.private_numbers().private_value.to_bytes(32, "big")))
    variable("VAPID_PUBLIC_KEY", b64(key.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)))
    gh("workflow", "run", "daily.yml")
    print("  site rebuilding with the new key (~2 min). Then on the phone: open Training, tap 'Turn on notifications',\n"
          "  and paste the code into the PUSH_SUBSCRIPTION secret (the card links to the page).")

def strava():
    import requests
    print("  strava.com/settings/api → if the Client Secret was ever shared, click 'Generate New Client Secret' first.")
    cid = input("  Client ID: ").strip()
    csecret = getpass.getpass("  Client Secret (hidden): ").strip()
    url = (f"https://www.strava.com/oauth/authorize?client_id={cid}&response_type=code"
           "&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=read,activity:read_all")
    print(f"  Opening Strava. Click Authorize; the page after won't load, that's fine.\n  {url}")
    webbrowser.open(url)
    back = input("  Paste the full localhost address from the browser: ").strip()
    q = parse_qs(urlsplit(back).query)
    if "activity:read_all" not in q.get("scope", [""])[0]:
        sys.exit("  Strava didn't grant activity:read_all; tick the box to view activities and try again.")
    r = requests.post("https://www.strava.com/oauth/token", data={
        "client_id": cid, "client_secret": csecret, "code": q["code"][0], "grant_type": "authorization_code"}, timeout=20)
    r.raise_for_status()
    j = r.json()
    print(f"  authorized as {j['athlete'].get('firstname')} {j['athlete'].get('lastname')}")
    secret("STRAVA_CLIENT_ID", cid)
    secret("STRAVA_CLIENT_SECRET", csecret)
    secret("STRAVA_REFRESH_TOKEN", j["refresh_token"])

def runna():
    print("  Google Calendar on the web → Settings (gear) → under 'Settings for my calendars' click Runna →\n"
          "  'Integrate calendar' → copy 'Secret address in iCal format'.")
    url = getpass.getpass("  Paste it (hidden): ").strip()
    if not url.startswith("https://") or ".ics" not in url:
        sys.exit("  That doesn't look like an iCal address (https://…/basic.ics).")
    secret("RUNNA_ICS_URL", url)

STEPS = {"site": site, "push": push, "runna": runna, "strava": strava}

if __name__ == "__main__":
    for name in sys.argv[1:] or STEPS:
        print(f"[{name}]")
        STEPS[name]()
    print("done. Nothing was printed or pasted anywhere but GitHub.")
