import requests
import sqlite3

SAKUGA_TAG_URL = "https://www.sakugabooru.com/tag.json"
headers = {"User-Agent": "SakugaIndex-StudentProject/0.1 (learning data project)"}

def title_to_tag_guess(title):
    """Turn an AniList title into a likely Sakugabooru tag format."""
    # lowercase, strip spaces to underscores: "Kimetsu no Yaiba" -> "kimetsu_no_yaiba"
    return title.lower().replace(" ", "_")

def find_best_tag(title):
    """Search Sakugabooru for the tag matching this title, return the best candidate."""
    guess = title_to_tag_guess(title)

    # Search the tag endpoint for tags containing our guess, ordered by post count
    params = {"name": guess, "limit": 10, "order": "count"}
    response = requests.get(SAKUGA_TAG_URL, headers=headers, params=params)
    tags = response.json()

    if not tags:
        # nothing matched — this anime may have insufficient sakuga data
        return None, 0

    # tags come back ordered by count (most posts first); take the top one
    best = tags[0]
    return best["name"], best["count"]

# --- test it on Demon Slayer ---
title = "Kimetsu no Yaiba"
tag, count = find_best_tag(title)
print(f"Title: {title}")
print(f"  guess: {title_to_tag_guess(title)}")
print(f"  best matching tag: {tag}  ({count} posts)")

def save_tag_to_db(anime_id, tag):
    """Write the resolved Sakugabooru tag into the anime row."""
    conn = sqlite3.connect("sakuga.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE anime SET sakugabooru_tag = ? WHERE anime_id = ?",
        (tag, anime_id)
    )
    conn.commit()
    conn.close()
    print(f"Saved tag '{tag}' for anime_id {anime_id}")

# Demon Slayer's anime_id is 101922 (from AniList)
save_tag_to_db(101922, tag)