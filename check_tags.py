import requests
URL = "https://www.sakugabooru.com/tag.json"
headers = {"User-Agent": "SakugaIndex-StudentProject/0.1 (learning data project)"}

searches = ["yojouhan_shinwa", "tatami", "ghost_in_the_shell", "koukaku_kidoutai", "monster_(2004)"]

for term in searches:
    params = {"name": term, "limit": 6, "order": "count"}
    r = requests.get(URL, headers=headers, params=params)
    tags = r.json()
    print(f"\n--- {term} ---")
    if not tags:
        print("  (nothing)")
    for t in tags:
        print(f"  {t['name']}  ->  {t['count']} posts  (type {t['type']})")