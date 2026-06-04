import requests
import json
import time   # for polite delays between requests

URL = "https://www.sakugabooru.com/post.json"
headers = {
    "User-Agent": "SakugaIndex-StudentProject/0.1 (learning data project)"
}

def count_sakuga(tag, max_posts=100):
    """
    Fetch up to max_posts for a given tag and measure coverage:
    - total posts found
    - how many have at least one community score
    - how many appear to have animator/craft tags beyond just the title
    """
    params = {"tags": tag, "limit": max_posts}
    response = requests.get(URL, headers=headers, params=params)

    if response.status_code != 200:
        print(f"  [error] status {response.status_code} for tag '{tag}'")
        return

    posts = response.json()
    total = len(posts)

    # Count posts that have MORE than just the title tags —
    # i.e. posts carrying extra descriptive/animator tags (richer data).
    rich_posts = 0
    for post in posts:
        tag_list = post["tags"].split()
        # crude heuristic: more than 2 tags suggests animator/craft detail
        if len(tag_list) > 2:
            rich_posts += 1

    print(f"Tag: {tag}")
    print(f"  Total posts found: {total}")
    print(f"  Posts with richer tagging (>2 tags): {rich_posts}")
    print()

# Test across the spectrum: famous -> mid -> obscure
test_tags = [
    "kimetsu_no_yaiba",        # very popular
    "mob_psycho_100",          # sakuga darling
    "jujutsu_kaisen",          # popular recent
]

for tag in test_tags:
    count_sakuga(tag)
    time.sleep(1)   # be polite: wait 1 second between requests