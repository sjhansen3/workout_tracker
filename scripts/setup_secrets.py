"""One-time setup, run on your own computer. Puts every key straight into GitHub; nothing is pasted into chat.

    gh auth login                            (once; needs `brew install gh`)
    python3 scripts/setup_secrets.py         all steps
    python3 scripts/setup_secrets.py strava  or just one: site | push | strava | hevy
Standard library + the system `openssl` only, so there is nothing to pip install.

site    sets SITE_URL.
push    makes a fresh notification keypair: VAPID_PRIVATE_KEY (secret) + VAPID_PUBLIC_KEY (variable),
        then rebuilds the site so the page uses the new key. Re-tap "Turn on notifications" afterwards.
strava  asks for the Client ID/Secret (hidden), opens Strava to authorize, and stores
        STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN.
hevy    asks for the Hevy API key (hidden; hevy.com → Settings → Developer, needs Pro) and stores HEVY_API_KEY.
"""
import base64, getpass, json, re, subprocess, sys, webbrowser
from urllib.parse import urlsplit, parse_qs, urlencode
from urllib.request import urlopen

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
    # P-256 keypair via the system openssl; pull the raw private scalar and public point from its text dump.
    pem = subprocess.run(["openssl", "ecparam", "-name", "prime256v1", "-genkey", "-noout"],
                         capture_output=True, text=True, check=True).stdout
    dump = subprocess.run(["openssl", "ec", "-text", "-noout"], input=pem,
                          capture_output=True, text=True, check=True).stdout
    def block(label):
        m = re.search(label + r":\s*\n((?:\s+[0-9a-f:]+\n)+)", dump)
        return bytes.fromhex(re.sub(r"[\s:]", "", m.group(1)))
    priv, pub = block("priv"), block("pub")
    priv = priv[-32:].rjust(32, b"\0")  # openssl may prefix a 00 byte or drop leading zeros
    assert len(pub) == 65 and pub[0] == 4, "unexpected public key format"
    b64 = lambda b: base64.urlsafe_b64encode(b).rstrip(b"=").decode()
    secret("VAPID_PRIVATE_KEY", b64(priv))
    variable("VAPID_PUBLIC_KEY", b64(pub))
    gh("workflow", "run", "daily.yml")
    print("  site rebuilding with the new key (~2 min). Then on the phone: open Training, tap 'Turn on notifications',\n"
          "  and paste the code into the PUSH_SUBSCRIPTION secret (the card links to the page).")

def strava():
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
    body = urlencode({"client_id": cid, "client_secret": csecret, "code": q["code"][0],
                      "grant_type": "authorization_code"}).encode()
    with urlopen("https://www.strava.com/oauth/token", data=body, timeout=20) as r:
        j = json.load(r)
    print(f"  authorized as {j['athlete'].get('firstname')} {j['athlete'].get('lastname')}")
    secret("STRAVA_CLIENT_ID", cid)
    secret("STRAVA_CLIENT_SECRET", csecret)
    secret("STRAVA_REFRESH_TOKEN", j["refresh_token"])

def hevy():
    print("  hevy.com → Settings → Developer → generate an API key (Hevy Pro). Made on the website, not in the phone app.")
    key = getpass.getpass("  API key (hidden): ").strip()
    if not key:
        sys.exit("  no key entered")
    secret("HEVY_API_KEY", key)

STEPS = {"site": site, "push": push, "strava": strava, "hevy": hevy}

if __name__ == "__main__":
    for name in sys.argv[1:] or STEPS:
        print(f"[{name}]")
        STEPS[name]()
    print("done. Nothing was printed or pasted anywhere but GitHub.")
