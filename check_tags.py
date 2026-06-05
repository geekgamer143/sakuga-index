import requests
URL = "https://www.sakugabooru.com/tag.json"
headers = {"User-Agent": "SakugaIndex-StudentProject/0.1 (learning data project)"}

searches = ["fire_force", "to_your_eternity", "fumetsu", "mind_game", "whisker", "naki"]

for term in searches:
    params = {"name": term, "limit": 6, "order": "count"}
    r = requests.get(URL, headers=headers, params=params)
    tags = r.json()
    print(f"\n--- {term} ---")
    for t in tags:
        print(f"  {t['name']}  ->  {t['count']} posts  (type {t['type']})")