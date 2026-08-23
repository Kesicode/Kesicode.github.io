"""
fetch_contributions.py
======================
Fetches 100% accurate per-day contribution counts across all years
directly from GitHub's public contribution graph HTML endpoints.

NO personal access tokens or secrets required!
Works directly with GitHub's public "Private contributions" enabled view.
"""
import re
import json
import requests
from datetime import datetime, timezone

USERNAME = "Kesicode"
OUTPUT_FILE = "contributions.json"
START_YEAR = 2024
CURRENT_YEAR = datetime.now(timezone.utc).year

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "text/html",
}

all_days = {}

for year in range(START_YEAR, CURRENT_YEAR + 1):
    url = f"https://github.com/users/{USERNAME}/contributions?from={year}-01-01&to={year}-12-31"
    print(f"Fetching {year} contributions from {url}...")
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        html = resp.text

        # Pattern matches:
        # data-date="YYYY-MM-DD" ... id="contribution-day-component-..."
        # followed by <tool-tip ... for="contribution-day-component-...">X contributions on ...</tool-tip>
        td_pattern = re.compile(
            r'data-date="([0-9]{4}-[0-9]{2}-[0-9]{2})"[^>]+id="(contribution-day-component-[^"]+)"'
        )
        td_matches = td_pattern.findall(html)

        year_count = 0
        for date_str, comp_id in td_matches:
            tip_pattern = re.compile(
                rf'for="{re.escape(comp_id)}"[^>]*>([^<]+)</tool-tip>'
            )
            tip_match = tip_pattern.search(html)
            count = 0
            if tip_match:
                tip_text = tip_match.group(1).strip()
                count_match = re.search(r'^(\d+)\s+contribution', tip_text)
                if count_match:
                    count = int(count_match.group(1))

            all_days[date_str] = count
            year_count += count

        print(f"  -> {year}: {year_count} contributions parsed ({len(td_matches)} days)")

    except Exception as e:
        print(f"  [ERROR] Failed to fetch {year}: {e}")

# Filter out future dates
today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
sorted_days = [
    {"date": k, "count": v}
    for k, v in sorted(all_days.items())
    if k <= today_str
]

grand_total = sum(d["count"] for d in sorted_days)

output = {
    "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "username": USERNAME,
    "total_contributions": grand_total,
    "days": sorted_days,
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print("\n" + "="*40)
print(f"Total contributions: {grand_total}")
print(f"Days tracked: {len(sorted_days)}")
best_day = max(sorted_days, key=lambda x: x["count"]) if sorted_days else {"date": "None", "count": 0}
print(f"Best day: {best_day['date']} with {best_day['count']} contributions")
print("="*40)
