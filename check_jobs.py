#!/usr/bin/env python3
"""
Checks Liquid Death's Greenhouse job board for new listings and emails
the recipient when something new shows up (or, optionally, every run).

Data source: Greenhouse's public Job Board API (no auth needed).
  https://boards-api.greenhouse.io/v1/boards/liquiddeath/jobs

State: a JSON file (seen_jobs.json) committed back to the repo by the
GitHub Actions workflow, so the script "remembers" what it already
reported across daily runs.
"""

import json
import os
import smtplib
import sys
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from zoneinfo import ZoneInfo

import requests

BOARD_TOKEN = "liquiddeath"
JOBS_API_URL = f"https://boards-api.greenhouse.io/v1/boards/{BOARD_TOKEN}/jobs"
STATE_FILE = "seen_jobs.json"

TARGET_HOUR_ET = 17
# Only enforce the 5pm-ET gate on the automatic daily "schedule" trigger.
# Manual runs (workflow_dispatch, e.g. clicking "Run workflow" to test)
# should always run fully, regardless of what time it is.
GITHUB_EVENT_NAME = os.environ.get("GITHUB_EVENT_NAME", "")
ENFORCE_TARGET_HOUR = GITHUB_EVENT_NAME == "schedule"


def fetch_jobs():
    resp = requests.get(JOBS_API_URL, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    jobs = data.get("jobs", [])
    # Normalize to the fields we care about
    normalized = {}
    for job in jobs:
        job_id = str(job["id"])
        normalized[job_id] = {
            "id": job_id,
            "title": job.get("title", "Untitled role"),
            "location": (job.get("location") or {}).get("name", "Unspecified location"),
            "url": job.get("absolute_url", f"https://job-boards.greenhouse.io/{BOARD_TOKEN}"),
            "updated_at": job.get("updated_at"),
        }
    return normalized


def load_previous_state():
    if not os.path.exists(STATE_FILE):
        return None  # signals "first run ever"
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(jobs):
    with open(STATE_FILE, "w") as f:
        json.dump(jobs, f, indent=2, sort_keys=True)


def build_email_body(new_jobs, all_jobs, first_run):
    lines = []
    if first_run:
        lines.append("First run — here's everything currently open at Liquid Death:\n")
        listing = all_jobs
    else:
        lines.append(f"{len(new_jobs)} new Liquid Death job posting(s) since yesterday:\n")
        listing = new_jobs

    for job in sorted(listing.values(), key=lambda j: j["title"]):
        lines.append(f"- {job['title']} ({job['location']})\n  {job['url']}")

    lines.append(f"\nFull board: https://job-boards.greenhouse.io/{BOARD_TOKEN}")
    lines.append(f"Checked: {datetime.now(ZoneInfo('America/New_York')).strftime('%Y-%m-%d %I:%M %p %Z')}")
    return "\n".join(lines)


def send_email(subject, body):
    gmail_user = os.environ["GMAIL_USER"]
    gmail_app_password = os.environ["GMAIL_APP_PASSWORD"]
    recipient = os.environ.get("RECIPIENT_EMAIL", gmail_user)

    msg = MIMEMultipart()
    msg["From"] = gmail_user
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(gmail_user, gmail_app_password)
        server.sendmail(gmail_user, recipient, msg.as_string())


def main():
    now_et = datetime.now(ZoneInfo("America/New_York"))
    if ENFORCE_TARGET_HOUR and now_et.hour != TARGET_HOUR_ET:
        print(f"Current ET hour is {now_et.hour}, not {TARGET_HOUR_ET}. Skipping this run.")
        return

    current_jobs = fetch_jobs()
    previous_jobs = load_previous_state()
    first_run = previous_jobs is None

    if first_run:
        new_jobs = {}
    else:
        new_jobs = {
            job_id: job
            for job_id, job in current_jobs.items()
            if job_id not in previous_jobs
        }

    should_email = first_run or len(new_jobs) > 0

    if should_email:
        subject = (
            "Liquid Death Careers: initial job list"
            if first_run
            else f"Liquid Death Careers: {len(new_jobs)} new job(s) posted"
        )
        body = build_email_body(new_jobs, current_jobs, first_run)
        send_email(subject, body)
        print(f"Email sent: {subject}")
    else:
        print("No new jobs. No email sent.")

    save_state(current_jobs)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
