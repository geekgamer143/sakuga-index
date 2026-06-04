import sqlite3
import math

conn = sqlite3.connect("sakuga.db")
cursor = conn.cursor()

# Pull each anime with ALL its individual clip scores (so we can log-transform per clip)
cursor.execute("""
    SELECT a.anime_id, a.title, c.community_score
    FROM anime a
    JOIN clips c ON a.anime_id = c.anime_id
""")
rows = cursor.fetchall()

# Group clip scores by anime
from collections import defaultdict
shows = defaultdict(list)
for anime_id, title, score in rows:
    shows[title].append(score or 0)

# Compute v2 craft score: mean of log(score+1) per clip, times log(clip_count+1)
results = []
for title, scores in shows.items():
    log_scores = [math.log(s + 1) for s in scores]      # log-transform each clip
    avg_log = sum(log_scores) / len(log_scores)          # average the logged scores
    count_factor = math.log(len(scores) + 1)             # volume, with diminishing returns
    craft = avg_log * count_factor
    results.append((title, round(craft, 2), round(avg_log, 2), len(scores)))

results.sort(key=lambda x: x[1], reverse=True)

print(f"{'RANK':<5}{'TITLE':<35}{'CRAFT':<9}{'AVG_LOG':<9}{'CLIPS'}")
print("-" * 64)
for i, (title, craft, avg_log, count) in enumerate(results, 1):
    print(f"{i:<5}{title[:34]:<35}{craft:<9}{avg_log:<9}{count}")

conn.close()