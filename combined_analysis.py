import sqlite3
import math
from collections import defaultdict

conn = sqlite3.connect("sakuga.db")
cursor = conn.cursor()

# Pull every clip with its score and episode number (NULL if unparsed)
cursor.execute("""
    SELECT a.title, c.community_score, c.episode_number
    FROM anime a
    JOIN clips c ON a.anime_id = c.anime_id
""")
rows = cursor.fetchall()

# Group by show
shows = defaultdict(lambda: {"scores": [], "episodes": set(), "total": 0, "with_ep": 0})
for title, score, ep in rows:
    s = shows[title]
    s["scores"].append(score or 0)
    s["total"] += 1
    if ep is not None:
        s["episodes"].add(ep)
        s["with_ep"] += 1

# Compute the combined metrics
results = []
for title, s in shows.items():
    # quality: log-transformed craft score (v2 formula)
    log_scores = [math.log(x + 1) for x in s["scores"]]
    avg_log = sum(log_scores) / len(log_scores)
    craft = round(avg_log * math.log(len(s["scores"]) + 1), 2)

    # consistency: how many distinct episodes the craft spreads across
    spread = len(s["episodes"])

    # coverage: what % of clips have an episode number (honesty flag)
    coverage = round(100 * s["with_ep"] / s["total"])

    results.append((title, craft, spread, coverage, s["total"]))

# sort by craft score (quality) as the primary ranking
results.sort(key=lambda x: x[1], reverse=True)

print(f"{'RANK':<5}{'TITLE':<32}{'CRAFT':<8}{'SPREAD':<8}{'COVERAGE':<10}{'CLIPS'}")
print("-" * 70)
for i, (title, craft, spread, coverage, total) in enumerate(results, 1):
    # flag low-coverage shows so consistency isn't misread
    flag = "  ⚠ low-cov" if coverage < 50 else ""
    print(f"{i:<5}{title[:31]:<32}{craft:<8}{spread:<8}{str(coverage)+'%':<10}{total}{flag}")

conn.close()