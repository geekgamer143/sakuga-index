import requests

ANILIST_URL = "https://graphql.anilist.co"

# Upgraded query: note 'isAnimationStudio' inside studios.
# That flag tells us which studio actually ANIMATED the show
# vs. which just produced/licensed it.
ANIME_QUERY = """
query ($search: String) {
  Media (search: $search, type: ANIME) {
    id
    title { romaji english }
    episodes
    startDate { year }
    averageScore
    studios {
      edges {
        isMain
        node {
          name
          isAnimationStudio
        }
      }
    }
  }
}
"""

def fetch_anime(search_term):
    """Pull one anime's metadata from AniList and return clean values."""
    variables = {"search": search_term}
    response = requests.post(ANILIST_URL, json={"query": ANIME_QUERY, "variables": variables})
    data = response.json()

    media = data["data"]["Media"]   # dig into the nested response

    # --- extract the simple fields ---
    anime_id = media["id"]
    title = media["title"]["romaji"]   # romaji is the reliable one (spike lesson)
    year = media["startDate"]["year"]
    episodes = media["episodes"]
    score = media["averageScore"]

    # --- find the REAL animation studio ---
    animation_studio = None
    for edge in media["studios"]["edges"]:
        if edge["node"]["isAnimationStudio"]:   # only true animation studios
            animation_studio = edge["node"]["name"]
            break   # take the first animation studio and stop

    # return everything as a tidy dictionary
    return {
        "anime_id": anime_id,
        "title": title,
        "year": year,
        "episodes": episodes,
        "score": score,
        "studio": animation_studio,
    }

# test it
result = fetch_anime("Kimetsu no Yaiba")
print(result)


import sqlite3

def load_into_db(anime):
    """Take the clean anime dictionary and insert studio + anime into the database."""
    conn = sqlite3.connect("sakuga.db")
    cursor = conn.cursor()

    # --- STUDIO: insert if new, then look up its id ---
    cursor.execute(
        "INSERT OR IGNORE INTO studios (name) VALUES (?)",
        (anime["studio"],)
    )
    # Now fetch the studio_id by name (works whether it was just inserted OR already existed)
    cursor.execute(
        "SELECT studio_id FROM studios WHERE name = ?",
        (anime["studio"],)
    )
    studio_id = cursor.fetchone()[0]   # fetchone() returns a row like (1,); [0] gets the number

    # --- ANIME: insert using the studio_id as the foreign key ---
    cursor.execute(
        """INSERT OR IGNORE INTO anime
           (anime_id, title, release_year, episodes, anilist_score, studio_id)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (anime["anime_id"], anime["title"], anime["year"],
         anime["episodes"], anime["score"], studio_id)
    )

    conn.commit()
    conn.close()
    print(f"Loaded: {anime['title']} (studio_id={studio_id})")

# run it on the result we already fetched
load_into_db(result)