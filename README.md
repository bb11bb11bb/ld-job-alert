# Liquid Death Job Alert

Checks Liquid Death's Greenhouse job board (`liquiddeath`) once a day around
5pm US Eastern and emails you when new roles are posted.

Data source (no scraping, no auth needed): Greenhouse's public Job Board API
```
https://boards-api.greenhouse.io/v1/boards/liquiddeath/jobs
```

## How it works
- `check_jobs.py` fetches the current job list, compares it to `seen_jobs.json`
  (the state from the last run, committed in the repo), and emails you only
  the *new* postings.
- The very first run emails you the full current list (so you have a baseline)
  and saves it as "seen."
- `.github/workflows/check_jobs.yml` runs the script daily via GitHub Actions
  and commits the updated state file back to the repo so tomorrow's run knows
  what's already been reported.

## One-time setup (~10 minutes)

### 1. Create a Gmail App Password
Regular Gmail passwords won't work with SMTP. You need an App Password:
1. Turn on 2-Step Verification on your Google account, if not already on:
   https://myaccount.google.com/security
2. Go to https://myaccount.google.com/apppasswords
3. Create a new app password (name it e.g. "job-alert"), copy the 16-character
   code it gives you. You won't be able to see it again.

### 2. Create a new GitHub repo
1. Go to https://github.com/new, create a repo (can be private), e.g.
   `liquiddeath-job-alert`.
2. Upload these files into it (or `git push` them — see below), keeping the
   folder structure intact, especially `.github/workflows/check_jobs.yml`.

### 3. Add your secrets
In your new repo: **Settings → Secrets and variables → Actions → New
repository secret**. Add three:

| Name | Value |
|---|---|
| `GMAIL_USER` | your full Gmail address, e.g. `you@gmail.com` |
| `GMAIL_APP_PASSWORD` | the 16-character app password from step 1 |
| `RECIPIENT_EMAIL` | the email address you want alerts sent to (can be the same Gmail address, or a different one) |

### 4. Enable Actions and test it
1. Go to the **Actions** tab of your repo, and enable workflows if prompted.
2. Click **Check Liquid Death Jobs** in the left sidebar, click **Run
   workflow** to trigger it manually and confirm it works end-to-end.
3. Check your email — first run should send you the full current list of
   open Liquid Death roles.

After that, it runs automatically every day and only emails you when
something new is posted.

## Pushing this project to GitHub from your computer
If you'd rather use git directly instead of uploading via the web UI:

```bash
cd liquiddeath-job-alert
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/liquiddeath-job-alert.git
git push -u origin main
```

## Notes
- GitHub Actions' free tier includes 2,000 minutes/month for private repos
  (unlimited for public repos) — this job takes well under a minute a day,
  so it costs nothing.
- The workflow is scheduled at both 21:00 and 22:00 UTC because GitHub
  Actions cron doesn't account for daylight saving time; the script checks
  the real US/Eastern clock and silently skips the "wrong" one of the two,
  so you'll still only get one email a day, right around 5pm ET.
- GitHub's cron scheduler can run a few minutes late during high load — it's
  "around 5pm ET," not guaranteed to the second.
- If you ever want to reset and get a fresh "full list" baseline, just
  delete `seen_jobs.json` from the repo.
