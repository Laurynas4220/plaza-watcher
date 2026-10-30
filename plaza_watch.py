"""Plaza Resident Services watcher.

Checks Plaza's public listings feed and raises a loud alarm on your phone
when a new living place appears in one of the cities you care about.
Runs every ~10 minutes on GitHub Actions (see .github/workflows/watch.yml).

Settings come from environment variables (GitHub "Secrets" / "Variables"):
  NTFY_TOPIC         required  your secret ntfy topic name (alarm on your phone)
  CITIES             optional  comma-separated, default "Eindhoven"
  MAX_RENT           optional  max total rent in euros, e.g. 1100 (default: no limit)
  CALLMEBOT_USER     optional  your Telegram @username -> also places a Telegram voice call
  TEST_ALARM         optional  "1" sends a test alarm and exits
"""

import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

FEED = (
    "https://mosaic-plaza-aanbodapi.zig365.nl/api/v1/actueel-aanbod"
    "?limit=200&locale=en_GB&page=0&sort=%2BreactionData.aangepasteTotaleHuurprijs"
)
DETAIL = "https://plaza.newnewnew.space/en/availables-places/living-place/details/{}"
STATE_FILE = Path(__file__).with_name("seen.json")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (personal listing watcher)",
    "Accept": "application/json",
    "Origin": "https://plaza.newnewnew.space",
    "Referer": "https://plaza.newnewnew.space/",
}


def env(name, default=""):
    return (os.environ.get(name) or default).strip()


def fetch_listings():
    req = urllib.request.Request(FEED, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r).get("data", [])


def matches(item, cities, max_rent):
    city = ((item.get("city") or {}).get("name") or "").lower()
    if city not in cities:
        return False
    # Only living places, not parking spaces or storage
    if (item.get("dwellingType") or {}).get("categorie") != "woning":
        return False
    rent = item.get("totalRent") or 0
    return max_rent is None or rent <= max_rent


def describe(item):
    kind = (item.get("dwellingType") or {}).get("localizedName") or "Place"
    city = (item.get("city") or {}).get("name", "")
    street = " ".join(
        str(p) for p in (item.get("street"), item.get("houseNumber"), item.get("houseNumberAddition")) if p
    )
    rent = item.get("totalRent")
    area = item.get("areaDwelling")
    bits = [f"{kind} in {city}", street]
    if rent:
        bits.append(f"EUR {rent:,.2f}/month")
    if area:
        bits.append(f"{area} m2")
    return " - ".join(bits)


def ntfy(topic, title, message, url=None):
    headers = {
        "Title": title,
        "Priority": "5",  # max/urgent: rings through Do Not Disturb when allowed
        "Tags": "rotating_light,house",
    }
    if url:
        headers["Click"] = url
        headers["Actions"] = f"view, Open listing, {url}"
    req = urllib.request.Request(
        f"https://ntfy.sh/{urllib.parse.quote(topic)}",
        data=message.encode("utf-8"),
        headers=headers,
        method="POST",
    )
    urllib.request.urlopen(req, timeout=20).read()


def telegram_call(user, text):
    q = urllib.parse.urlencode({"user": user, "text": text, "lang": "en-GB-Standard-B", "rpt": "2"})
    urllib.request.urlopen(f"https://api.callmebot.com/start.php?{q}", timeout=60).read()


def alarm(title, message, url=None):
    topic = env("NTFY_TOPIC")
    tg_user = env("CALLMEBOT_USER")
    if topic:
        try:
            ntfy(topic, title, message, url)
        except Exception as e:  # keep going so the call can still happen
            print("ntfy failed:", e)
    if tg_user:
        try:
            telegram_call(tg_user, f"{title}. {message}")
        except Exception as e:
            print("Telegram call failed:", e)
    print(f"ALARM: {title} | {message} | {url or ''}")


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"seen": [], "initialised": False, "last_check_day": ""}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def main():
    if env("TEST_ALARM") == "1":
        alarm("Plaza watcher test", "If your phone is ringing, the alarm works!",
              "https://plaza.newnewnew.space/en/availables-places/living-place")
        return

    if not env("NTFY_TOPIC") and not env("CALLMEBOT_USER"):
        sys.exit("Set NTFY_TOPIC (and/or CALLMEBOT_USER) so the watcher can alert you.")

    cities = {c.strip().lower() for c in env("CITIES", "Eindhoven").split(",") if c.strip()}
    max_rent = float(env("MAX_RENT")) if env("MAX_RENT") else None

    listings = fetch_listings()
    state = load_state()
    seen = set(state.get("seen", []))
    wanted = [i for i in listings if matches(i, cities, max_rent)]
    new = [i for i in wanted if str(i.get("id")) not in seen]

    print(f"{len(listings)} listings on Plaza, {len(wanted)} match {sorted(cities)}, {len(new)} new")

    # Ring for new matches. On the very first run there is nothing to compare
    # against, so anything already matching is announced once as well.
    if new:
        if len(new) == 1:
            item = new[0]
            alarm("NEW Plaza listing!", describe(item), DETAIL.format(item.get("urlKey", "")))
        else:
            lines = "\n".join(describe(i) for i in new[:5])
            alarm(f"{len(new)} NEW Plaza listings!", lines, DETAIL.format(new[0].get("urlKey", "")))

    state["seen"] = sorted(seen | {str(i.get("id")) for i in listings})
    state["initialised"] = True
    # A once-a-day change keeps GitHub from pausing the schedule for inactivity
    state["last_check_day"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    save_state(state)


if __name__ == "__main__":
    main()
