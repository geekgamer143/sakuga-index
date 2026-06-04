import requests

URL = "https://www.sakugabooru.com/post.json"
headers = {"User-Agent": "SakugaIndex-StudentProject/0.1 (learning data project)"}

# try every Mob Psycho tag variant we found in the tag search
variants = [
    "mob_psycho_100",
    "mob_psycho_100_series",
    "mob_psycho_100_ii",
]

for tag in variants:
    params = {"tags": tag, "limit": 5}
    r = requests.get(URL, headers=headers, params=params)
    posts = r.json()
    print(f"{tag}  ->  {len(posts)} posts")