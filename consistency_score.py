import sqlite3
import math
from collections import defaultdict

conn = sqlite3.connect("sakuga.db")
cursor = conn.cursor()

cursor.execute("""
    SELECT a.title, c.community_score, c.episode_number
    FROM anime a
    JOIN clips c ON a.anime_id = c.anime_id
    WHERE a.data_status = 'loaded'
""")
rows = cursor.fetchall()

shows = defaultdict(lambda: {"scores": [], "episodes": set(), "total": 0, "with_ep": 0})
for title, score, ep in rows:
    s = shows[title]
    s["scores"].append(score or 0)
    s["total"] += 1
    if ep is not None:
        s["episodes"].add(ep)
        s["with_ep"] += 1

MIN_COVERAGE = 50      # need at least 50% of clips episode-tagged to judge consistency
MIN_SPREAD = 2         # need at least 2 distinct episodes (a movie has 0-1)

ranked = []      # shows we CAN measure for consistency
not_measurable = []   # shows we honestly can't judge

for title, s in shows.items():
    coverage = round(100 * s["with_ep"] / s["total"])
    spread = len(s["episodes"])
    log_scores = [math.log(x + 1) for x in s["scores"]]
    avg_log = sum(log_scores) / len(log_scores)

    # Peak Craft (the existing score) for comparison
    peak = round(avg_log * math.log(len(s["scores"]) + 1), 2)

    if coverage >= MIN_COVERAGE and spread >= MIN_SPREAD:
        # Sustained Craft: quality x how broadly it's spread across episodes
        sustained = round(avg_log * math.log(spread + 1), 2)
        ranked.append((title, sustained, peak, spread, coverage))
    else:
        reason = "film/no episodes" if spread < MIN_SPREAD else f"low coverage ({coverage}%)"
        not_measurable.append((title, peak, reason))

# Sort by Sustained Craft, highest first
ranked.sort(key=lambda x: x[1], reverse=True)

print("="*72)
print("SUSTAINED CRAFT RANKING  (quality spread across episodes)")
print("Only shows with >=50% episode coverage and >=2 episodes")
print("="*72)
print(f"{'RANK':<5}{'TITLE':<34}{'SUSTAINED':<11}{'PEAK':<8}{'SPREAD':<8}{'COV'}")
print("-"*72)
for i, (title, sustained, peak, spread, coverage) in enumerate(ranked, 1):
    print(f"{i:<5}{title[:33]:<34}{sustained:<11}{peak:<8}{spread:<8}{coverage}%")

print(f"\n{len(not_measurable)} shows NOT rankable for sustained craft (honest exclusions):")
for title, peak, reason in sorted(not_measurable, key=lambda x: x[1], reverse=True):
    print(f"   • {title[:33]:<34} (peak {peak}) — {reason}")

conn.close()