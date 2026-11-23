# Setup: the few manual steps

Everything is already built. This file lists what only **you** can do (accounts, links, switches in GitHub's settings).

## 1. Create the repository

The profile README only shows on your profile if the repo is named **exactly** like your username, and is **public**.

1. On GitHub: **New repository** > name `GPHL125241O` > **Public**. Do **not** tick "Add a README".
2. From this folder:

```bash
git init -b main
git add .
git commit -m "feat: haunted profile"
git remote add origin https://github.com/GPHL125241O/GPHL125241O.git
git push -u origin main
```

Your profile page will now show `README.md`.

## 2. Fill in the placeholders

Everything you still need to provide is marked `TODO`. List them all:

```bash
grep -rn "TODO" README.md site/index.html
```

| Where | What to replace |
|---|---|
| `README.md`, "Let's Connect" | `TODO_LINKEDIN_URL`, `TODO_X_URL`, `TODO_EMAIL`, `TODO_TRYHACKME_URL`, `TODO_HACKTHEBOX_URL`, `TODO_DISCORD_URL`. Delete any badge you don't want. |
| `site/index.html`, `#connect` | The same six values. Cards that still contain `TODO_` are **hidden automatically** on the site, so nothing broken is shown. |
| `README.md`, `site/index.html` | The skills and tech stack are sensible defaults. Edit them to match what you really do. |
| `README.md` | Add a line about what you are working on right now. |

The Ghost Protocol Labs link (`https://github.com/Ghost-Protocol-Lab`) and the five `Damn_Practical_*` repo links are already filled in.

## 3. Turn on GitHub Pages

1. **Settings > Pages > Build and deployment > Source: GitHub Actions**.
2. **Actions > Deploy Website > Run workflow**.
3. When it finishes, the URL shows under Settings > Pages. It should be `https://gphl125241o.github.io/GPHL125241O/`. If it is different (custom domain, renamed repo), update the website badge in `README.md` and the three absolute URLs in `site/index.html` (`canonical`, `og:url`, `og:image`).

After that the site redeploys by itself whenever `site/**` changes or the nightly stats job finishes.

## 4. Run the stats workflow once

1. **Actions > Update Graveyard Stats > Run workflow** (leave "log_type" as `none`).
2. It regenerates the charts and the real contribution graph, then commits them.

If the **contribution graph** step shows a warning, the default token could not read your contributions. Fix it:

1. GitHub > Settings > Developer settings > Personal access tokens. Create a token with the **`read:user`** scope.
2. Repo > Settings > Secrets and variables > Actions > **New repository secret**: name `GH_PAT`, value is the token.
3. Optional, to count private work too: your profile > Settings > tick **"Include private contributions on my profile"**.

The workflow already prefers `GH_PAT` when it exists, so nothing else changes. The other charts are committed even if this step fails.

**Fallbacks** if you would rather not use a token: [Platane/snk](https://github.com/Platane/snk) (a snake that eats your contributions) or [github-profile-summary-cards](https://github.com/vn7n24fzkq/github-profile-summary-cards). Both are GitHub Actions that generate an SVG; point an `<img>` in the README at their output.

If a run fails with a **403 on push**, open Settings > Actions > General > Workflow permissions and choose **Read and write permissions**.

## 5. Replace the sample data with your own

`data/modules.json` and `data/ctfs.json` ship with a few entries marked `"sample": true`. The charts show a red **SAMPLE DATA** badge until they are gone.

```bash
python scripts/log.py clear-samples
```

## 6. Daily use: logging what you completed

Pick whichever is easiest that day. All three end up in the same two JSON files.

**A. Command line** (Python 3.9+, no installs; run `git pull` first because the bot also commits):

```bash
python scripts/log.py module "Burp Suite Basics" --platform THM --category Web
python scripts/log.py ctf "Cap" --platform HTB --difficulty easy --category Linux --points 20
python scripts/log.py module "Old module" --platform HTB --date 2026-11-20    # back-date
git add -A && git commit -m "log: today" && git push
```

Platform shortcuts expand automatically (`THM` becomes TryHackMe, `HTB` HackTheBox, `PICO` picoCTF, `PSA` PortSwigger).

**B. Edit the JSON** on github.com (pencil icon on `data/modules.json`) and commit. The push triggers the workflow.

**C. No computer needed:** Actions > **Update Graveyard Stats** > **Run workflow**, set `log_type` to `module` or `ctf`, fill in name and platform, and run. This works from the GitHub website in any mobile browser.

Whatever the route, the charts refresh within a minute or two, and everything is rebuilt automatically every night at **00:05 IST** (cron `35 18 * * *`, which is UTC). "Today" and streaks are counted in IST.

## 7. Preview locally

```bash
python scripts/preview.py          # http://localhost:8000
python scripts/charts.py           # regenerate the module/CTF charts
python scripts/contributions.py --demo --out /tmp/demo.svg --json-out none   # preview with fake data
```

## 8. Changing the look

- **Colors and fonts:** `scripts/theme.py` (the SVGs) and the `:root` block in `site/css/style.css` (the website).
- **Hero text, rotating titles, section headers:** the top of `scripts/make_static_assets.py` (`TAGLINE`, `TITLES`, `HEADERS`), then run `python scripts/make_static_assets.py`. For the site's typing line, edit `roles` in `site/js/main.js`.
- GitHub caches README images for a few minutes, so new art can take a moment to show up.

## What's in the repo

```
README.md                  your profile page
SETUP.md                   this file
assets/                    hero, headers, divider, footer, plus the generated charts
data/                      modules.json, ctfs.json (you edit)  |  contributions.json (the bot writes)
scripts/                   log.py (CLI), charts.py, contributions.py, make_static_assets.py, preview.py, theme.py
site/                      the GitHub Pages website (plain HTML, CSS, JS)
.github/workflows/         update-stats.yml (nightly + on demand)  |  pages.yml (deploys the site)
```

## Security notes

- No secrets live in the repo. The only optional secret is `GH_PAT`, scope `read:user`.
- Workflow inputs are passed through environment variables, never interpolated into shell commands, so a crafted module name cannot run code.
- The stats workflow has `contents: write` and nothing else; the Pages workflow has only the permissions Pages needs.
- Keep real client or engagement data out of the repo, including the JSON files and screenshots.
