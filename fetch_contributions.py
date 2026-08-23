"""
fetch_contributions.py
======================
Run by GitHub Actions daily using the auto-provided GITHUB_TOKEN.
Fetches 100% accurate per-day contribution counts via GitHub GraphQL API
and writes contributions.json to the repo root.

No personal access token needed — GITHUB_TOKEN is automatically available
in every GitHub Actions workflow run.
"""
import os
import json
import requests
from datetime import datetime, timezone

USERNAME = "Kesicode"
OUTPUT_FILE = "contributions.json"

token = os.environ.get("GITHUB_TOKEN")
if not token:
    raise SystemExit("ERROR: GITHUB_TOKEN environment variable not set")

headers = {
    "Authorization": f"bearer {token}",
    "Content-Type": "application/json",
}

QUERY = """
{
  user(login: "%s") {
    contributionsCollection(from: "%s-01-01T00:00:00Z", to: "%s-12-31T23:59:59Z") {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

all_days = {}
grand_total = 0
current_year = datetime.now(timezone.utc).year

# Fetch each year separately (GitHub GraphQL max range = 1 year per query)
for year in range(2024, current_year + 1):
    payload = {"query": QUERY % (USERNAME, year, year)}
    resp = requests.post("https://api.github.com/graphql", json=payload, headers=headers)
    resp.raise_for_status()
    data = resp.json()

    if "errors" in data:
        print(f"  [WARN] GraphQL errors for {year}: {data['errors']}")
        continue

    cal = (
        data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    )
    year_total = cal["totalContributions"]
    grand_total += year_total
    print(f"  {year}: {year_total} contributions")

    for week in cal["weeks"]:
        for day in week["contributionDays"]:
            all_days[day["date"]] = day["contributionCount"]

# Sort chronologically
sorted_days = [
    {"date": k, "count": v}
    for k, v in sorted(all_days.items())
]

output = {
    "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "username": USERNAME,
    "total_contributions": grand_total,
    "days": sorted_days,
}

with open(OUTPUT_FILE, "w") as f:
    json.dump(output, f)

print(f"\nDone! Wrote {OUTPUT_FILE}")
print(f"Total contributions: {grand_total}")
print(f"Days tracked: {len(sorted_days)}")
