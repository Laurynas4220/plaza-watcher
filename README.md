# Plaza watcher

Checks Plaza Resident Services every ~10 minutes and makes your phone **ring like an alarm** (and optionally **calls you on Telegram**) the moment a new living place appears in Eindhoven. Runs free on GitHub, so your laptop can be off.

It ignores parking spaces and storage, and only rings once per listing.

---

## Setup (about 10 minutes)

### 1. Put the files on GitHub
1. Make a free account at github.com (if you don't have one).
2. Click **+ → New repository**, name it `plaza-watcher`, choose **Public**, click **Create**.
   *Public matters: GitHub Actions is unlimited for public repos. A private repo would run out of free minutes in about two weeks. Nothing personal is stored in it; your alarm topic stays secret (step 3).*
3. On the new repo page click **uploading an existing file** and drag in `plaza_watch.py` and `README.md`. Commit.
4. Click **Add file → Create new file**, type the name `.github/workflows/watch.yml` (the slashes create the folders), paste the contents of `watch.yml`, commit.

### 2. Set up the alarm on your phone (ntfy, free)
1. Install the **ntfy** app (Play Store / App Store).
2. Tap **+**, subscribe to a topic with a long random name nobody can guess, e.g. `laurynas-plaza-8k2qz7w` (anyone who knows the name could send you notifications).
3. **Android – make it ring like an alarm:**
   - ntfy → Settings → turn on **"Keep alerting for highest priority"** (insistent alerts: keeps ringing until you tap it).
   - Long-press the topic → notification settings → allow it to **override Do Not Disturb**, pick a loud sound.
4. **iPhone:** iOS won't let ntfy ring through silent mode. Enable notifications for ntfy, and also do step 4 (Telegram call) so you actually get woken up.

### 3. Tell GitHub your topic
Repo → **Settings → Secrets and variables → Actions**:
- **Secrets** tab → *New repository secret*: name `NTFY_TOPIC`, value = your topic name.
- *(optional)* **Variables** tab:
  - `CITIES` = `Eindhoven,Geldrop` to include Geldrop (borders Eindhoven, currently has many studios). Default is just Eindhoven.
  - `MAX_RENT` = e.g. `1100` to skip anything more expensive.

### 4. (Optional) Real phone call via Telegram — recommended on iPhone
1. Go to callmebot.com, open the **Telegram Call** instructions and do the one-time step that allows their bot to call your Telegram account.
2. Add a secret `CALLMEBOT_USER` = your Telegram username including the @, e.g. `@laurynas`.

### 5. Test it
Repo → **Actions** tab → if asked, click *I understand… enable workflows* → **Plaza watcher** → **Run workflow** → tick **Send a test alarm** → Run.
Your phone should ring within a minute. After that it runs by itself every ~10 minutes.

---

## Good to know
- GitHub sometimes starts scheduled runs a few minutes late, so the real gap is roughly 10–15 minutes.
- The first run records what's already listed; after that only *new* listings ring.
- To pause it: Actions → Plaza watcher → **⋯ → Disable workflow**.
- If GitHub ever emails that the schedule was disabled for inactivity, just re-enable it there (the watcher makes a small daily update to prevent this).
