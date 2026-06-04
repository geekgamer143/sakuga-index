import requests

URL = "https://www.sakugabooru.com/tag.json"
headers = {"User-Agent": "SakugaIndex-StudentProject/0.1 (learning data project)"}

# search terms for the 4 problem shows
searches = ["one-punch", "wanpanman", "saitama"]

for term in searches:
    params = {"name": term, "limit": 8, "order": "count"}
    r = requests.get(URL, headers=headers, params=params)
    tags = r.json()
    print(f"\n--- search: {term} ---")
    if not tags:
        print("  no matching tags")
    for t in tags:
        # type 3 = copyright (show), type 1 = artist — we want show tags here
        print(f"  {t['name']}  ->  {t['count']} posts  (type {t['type']})")