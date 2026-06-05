import requests
import sqlite3
import time
import re
import json
import os

ANILIST_URL = "https://graphql.anilist.co"
SAKUGA_POST_URL = "https://www.sakugabooru.com/post.json"
SAKUGA_TAG_URL = "https://www.sakugabooru.com/tag.json"
headers = {"User-Agent": "SakugaIndex-StudentProject/0.1 (learning data project)"}

ANIME_QUERY = """
query ($search: String) {
  Media (search: $search, type: ANIME) {
    id
    title { romaji english }
    episodes
    startDate { year }
    averageScore
    studios { edges { node { name isAnimationStudio } } }
  }
}
"""

CACHE_FILE = "tag_type_cache.json"

# Load the cache from disk if it exists, so we don't re-query known tags
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE) as f:
        tag_type_cache = json.load(f)
    print(f"Loaded {len(tag_type_cache)} cached tag types from disk")
else:
    tag_type_cache = {}

# Collects shows that need manual review, printed at the end
flagged = []

def load_overrides():
    overrides = {}
    try:
        with open("tag_overrides.txt") as f:
            for line in f:
                line = line.strip()
                if line and "=" in line:
                    name, tag = line.split("=", 1)
                    overrides[name.strip()] = tag.strip()
    except FileNotFoundError:
        pass
    return overrides

def fetch_anime(search_term):
    variables = {"search": search_term}
    r = requests.post(ANILIST_URL, json={"query": ANIME_QUERY, "variables": variables})
    media = r.json()["data"]["Media"]
    if media is None:
        return None
    studio = None
    for edge in media["studios"]["edges"]:
        if edge["node"]["isAnimationStudio"]:
            studio = edge["node"]["name"]
            break
    return {
        "anime_id": media["id"],
        "title": media["title"]["romaji"],
        "year": media["startDate"]["year"],
        "episodes": media["episodes"],
        "score": media["averageScore"],
        "studio": studio,
    }

def clean_for_search(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def search_sakuga_tag(search_string):
    guess = search_string.replace(" ", "_")
    params = {"name": guess, "limit": 10, "order": "count"}
    r = requests.get(SAKUGA_TAG_URL, headers=headers, params=params)
    tags = r.json()
    if tags:
        return tags[0]["name"]
    return None

def find_best_tag(title):
    cleaned = clean_for_search(title)
    tag = search_sakuga_tag(cleaned)
    if tag:
        return tag
    words = cleaned.split()
    while len(words) > 1:
        words = words[:-1]
        tag = search_sakuga_tag(" ".join(words))
        if tag:
            return tag
    return None

def is_match_suspicious(search_term, anime_title, tag):
    """Decide if a resolved tag looks questionable and should be flagged for review.
    Returns a reason string if suspicious, or None if it looks fine."""
    cleaned_title = clean_for_search(anime_title).replace(" ", "_")
    cleaned_search = clean_for_search(search_term).replace(" ", "_")
    # Strip a trailing _series for comparison
    tag_base = tag.replace("_series", "")
    # If the tag shares NO word with either the title or the search term, it's suspicious
    title_words = set(cleaned_title.split("_"))
    search_words = set(cleaned_search.split("_"))
    tag_words = set(tag_base.split("_"))
    shared = (title_words | search_words) & tag_words
    if not shared:
        return f"tag '{tag}' shares no words with '{anime_title}'"
    return None

def is_artist_tag(name):
    if name in tag_type_cache:
        return tag_type_cache[name]
    params = {"name": name, "limit": 1}
    r = requests.get(SAKUGA_TAG_URL, headers=headers, params=params)
    results = r.json()
    is_artist = bool(results and results[0]["type"] == 1)
    tag_type_cache[name] = is_artist
    time.sleep(0.3)
    return is_artist

def fetch_posts(tag, max_clips):
    params = {"tags": tag, "limit": max_clips}
    posts = requests.get(SAKUGA_POST_URL, headers=headers, params=params).json()
    if not posts and tag.endswith("_series"):
        base = tag[:-len("_series")]
        params = {"tags": base, "limit": max_clips}
        posts = requests.get(SAKUGA_POST_URL, headers=headers, params=params).json()
    return posts

def load_one_anime(search_term, conn, overrides, max_clips=50):
    cursor = conn.cursor()

    anime = fetch_anime(search_term)
    if anime is None:
        print(f"  ✗ '{search_term}': not found on AniList — skipping")
        flagged.append((search_term, "NOT FOUND on AniList"))
        return

    studio_id = None
    if anime["studio"]:
        cursor.execute("INSERT OR IGNORE INTO studios (name) VALUES (?)", (anime["studio"],))
        cursor.execute("SELECT studio_id FROM studios WHERE name = ?", (anime["studio"],))
        studio_id = cursor.fetchone()[0]

    cursor.execute(
        """INSERT OR IGNORE INTO anime
           (anime_id, title, release_year, episodes, anilist_score, studio_id)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (anime["anime_id"], anime["title"], anime["year"],
         anime["episodes"], anime["score"], studio_id)
    )

    # Override first, else auto-match
    used_override = False
    if search_term in overrides:
        tag = overrides[search_term]
        used_override = True
        print(f"    (using manual override tag: {tag})")
    else:
        tag = find_best_tag(anime["title"])

    if tag is None:
        cursor.execute("UPDATE anime SET data_status = 'insufficient_data' WHERE anime_id = ?",
                       (anime["anime_id"],))
        conn.commit()
        print(f"  ⚠ '{anime['title']}': no sakuga tag found — marked insufficient_data")
        flagged.append((search_term, "NO TAG FOUND"))
        return

    # FLAG suspicious matches (skip the check if it was a manual override — we trust those)
    if not used_override:
        reason = is_match_suspicious(search_term, anime["title"], tag)
        if reason:
            flagged.append((search_term, reason))

    cursor.execute("UPDATE anime SET sakugabooru_tag = ? WHERE anime_id = ?",
                   (tag, anime["anime_id"]))

    # show-level idempotency
    cursor.execute("DELETE FROM clip_animators WHERE clip_id IN (SELECT clip_id FROM clips WHERE anime_id = ?)", (anime["anime_id"],))
    cursor.execute("DELETE FROM clips WHERE anime_id = ?", (anime["anime_id"],))

    posts = fetch_posts(tag, max_clips)

    for post in posts:
        cursor.execute(
            """INSERT OR IGNORE INTO clips
               (clip_id, anime_id, community_score, episode_source, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (post["id"], anime["anime_id"], post.get("score"),
             post.get("source"), post.get("created_at"))
        )
        for t in post["tags"].split():
            if is_artist_tag(t):
                cursor.execute("INSERT OR IGNORE INTO animators (name) VALUES (?)", (t,))
                cursor.execute("SELECT animator_id FROM animators WHERE name = ?", (t,))
                animator_id = cursor.fetchone()[0]
                cursor.execute(
                    "INSERT OR IGNORE INTO clip_animators (clip_id, animator_id) VALUES (?, ?)",
                    (post["id"], animator_id)
                )

    status = 'loaded' if posts else 'insufficient_data'
    cursor.execute("UPDATE anime SET data_status = ? WHERE anime_id = ?",
                   (status, anime["anime_id"]))
    conn.commit()

    # flag shows that found a tag but got zero clips (suspicious)
    if not posts:
        flagged.append((search_term, f"tag '{tag}' returned 0 clips"))

    print(f"  ✓ '{anime['title']}': {len(posts)} clips loaded (tag: {tag})")

def main():
    with open("anime_list.txt") as f:
        anime_list = [line.strip() for line in f if line.strip()]

    print(f"Loading {len(anime_list)} anime...\n")
    conn = sqlite3.connect("sakuga.db")
    overrides = load_overrides()

    for i, title in enumerate(anime_list, 1):
        print(f"[{i}/{len(anime_list)}] {title}")
        try:
            load_one_anime(title, conn, overrides)
        except Exception as e:
            print(f"  ✗ ERROR on '{title}': {e} — skipping")
            flagged.append((title, f"ERROR: {e}"))
        time.sleep(1)

    conn.close()

    # save cache for next run
    with open(CACHE_FILE, "w") as f:
        json.dump(tag_type_cache, f)

    # print the review list
    print(f"\n{'='*60}")
    print(f"Done! Cached {len(tag_type_cache)} tag types.")
    print(f"\n⚠ {len(flagged)} shows need REVIEW:")
    for name, reason in flagged:
        print(f"   • {name}: {reason}")
    print(f"{'='*60}")

main()