import requests

URL = "https://www.sakugabooru.com/tag.json"
headers = {
    "User-Agent": "SakugaIndex-StudentProject/0.1 (learning data project)"
}

# Deliberately testing the THIN end: older + more niche titles
searches = ["gurren_lagann", "dennou_coil", "kemono_friends", "tatami_galaxy"]

for term in searches:
    params = {"name": term, "limit": 5, "order": "count"}
    r = requests.get(URL, headers=headers, params=params)
    tags = r.json()
    print(f"\n--- search: {term} ---")
    if not tags:
        print("  no matching tags")
    for t in tags:
        print(f"  {t['name']}  ->  {t['count']} posts")