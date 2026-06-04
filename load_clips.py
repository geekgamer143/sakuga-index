import requests
import sqlite3
import time

SAKUGA_POST_URL = "https://www.sakugabooru.com/post.json"
SAKUGA_TAG_URL = "https://www.sakugabooru.com/tag.json"
headers = {"User-Agent": "SakugaIndex-StudentProject/0.1 (learning data project)"}

def get_artist_tags(tag_names):
    """Given a set of tag names, ask Sakugabooru which ones are 'artist' type.
    Returns a set of the names that are artists (animators)."""
    artist_tags = set()
    # Sakugabooru tag types: 1 = artist, 3 = copyright(series), 0 = general, etc.
    for name in tag_names:
        params = {"name": name, "limit": 1}
        r = requests.get(SAKUGA_TAG_URL, headers=headers, params=params)
        results = r.json()
        if results and results[0]["type"] == 1:   # type 1 == artist
            artist_tags.add(name)
        time.sleep(0.3)   # be polite between calls
    return artist_tags

def load_clips_for_anime(anime_id, tag, max_clips=20):
    """Pull clips for a given Sakugabooru tag and load clips + animators + bridge."""
    conn = sqlite3.connect("sakuga.db")
    cursor = conn.cursor()

    # 1. Fetch the posts (clips) for this anime's tag
    params = {"tags": tag, "limit": max_clips}
    response = requests.get(SAKUGA_POST_URL, headers=headers, params=params)
    posts = response.json()
    print(f"Fetched {len(posts)} clips for tag '{tag}'")

    # 2. Collect ALL tag names across all posts, so we can look up types in one pass
    all_tag_names = set()
    for post in posts:
        all_tag_names.update(post["tags"].split())

    # 3. Figure out which of those are artist (animator) tags
    print("Identifying animator tags... (this takes a moment)")
    artist_tags = get_artist_tags(all_tag_names)
    print(f"Found {len(artist_tags)} animator tags")

    # 4. Insert each clip, its animators, and the bridge rows
    for post in posts:
        clip_id = post["id"]
        score = post.get("score")
        episode = post.get("source")
        created = post.get("created_at")

        # insert the clip (linked to anime via anime_id)
        cursor.execute(
            """INSERT OR IGNORE INTO clips
               (clip_id, anime_id, community_score, episode_source, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (clip_id, anime_id, score, episode, created)
        )

        # for each tag on this clip that is an animator, link it
        for t in post["tags"].split():
            if t in artist_tags:
                # insert animator if new
                cursor.execute(
                    "INSERT OR IGNORE INTO animators (name) VALUES (?)",
                    (t,)
                )
                # look up the animator's id
                cursor.execute("SELECT animator_id FROM animators WHERE name = ?", (t,))
                animator_id = cursor.fetchone()[0]
                # fill the bridge table
                cursor.execute(
                    "INSERT OR IGNORE INTO clip_animators (clip_id, animator_id) VALUES (?, ?)",
                    (clip_id, animator_id)
                )

    conn.commit()
    conn.close()
    print("Done loading clips and animators.")

# run it for Demon Slayer
load_clips_for_anime(101922, "kimetsu_no_yaiba_series", max_clips=20)