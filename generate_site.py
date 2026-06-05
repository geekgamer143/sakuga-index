import sqlite3
import math
import json
from collections import defaultdict

conn = sqlite3.connect("sakuga.db")
cursor = conn.cursor()

# now also pulling a.episodes so we can tell real films from data-thin series
cursor.execute("""
    SELECT a.title, a.episodes, c.community_score, c.episode_number
    FROM anime a
    JOIN clips c ON a.anime_id = c.anime_id
    WHERE a.data_status = 'loaded'
""")
rows = cursor.fetchall()

shows = defaultdict(lambda: {"scores": [], "episodes_set": set(), "total": 0, "with_ep": 0, "ep_count": None})
for title, ep_count, score, ep in rows:
    s = shows[title]
    s["scores"].append(score or 0)
    s["total"] += 1
    s["ep_count"] = ep_count          # AniList episode count (1 = film)
    if ep is not None:
        s["episodes_set"].add(ep)
        s["with_ep"] += 1

MIN_COVERAGE = 50
MIN_SPREAD = 2

def make_label(peak, sustained, spread, coverage, measurable, ep_count):
    """Recommendation-style label. Answers 'why would I care?' — stays honest about what the data supports."""
    is_film = ep_count is not None and ep_count <= 1
    if is_film:
        return "Film — Worth Seeing"
    # Series with strong buzz but we can't verify episodic craft (promo/social-driven clips)
    if not measurable:
        if peak >= 16:
            return "Hyped — Hard to Verify"
        return "Modest Sakuga Presence"
    # Measurable shows — judge by sustained (consistency) primarily
    if sustained is not None and sustained >= 14:
        return "Must-Watch Sakuga"
    if sustained is not None and sustained >= 10:
        return "Great Throughout"
    if peak >= 18 and spread <= 5:
        return "Worth It for a Few Episodes"
    if spread >= 8:
        return "Big Moments, Less Consistent"
    return "Modest Sakuga Presence"

def stars(value, lo, hi):
    """Map a score in [lo, hi] to 1-5 stars (filled count)."""
    if value is None:
        return 0
    frac = (value - lo) / (hi - lo)
    frac = max(0.0, min(1.0, frac))
    return round(1 + frac * 4)   # 1..5

def consistency_phrase(spread, coverage, measurable, ep_count):
    """Warm, concrete phrase — keeps real episode counts as the value-add."""
    if ep_count is not None and ep_count <= 1:
        return "Single film"
    if not measurable:
        if coverage < MIN_COVERAGE and coverage > 0:
            return "Mostly viral / promo clips"
        return "Mostly clips we can't tie to episodes"
    if spread >= 15:
        return f"Great across {spread} episodes"
    if spread >= 8:
        return f"Strong in {spread} episodes"
    if spread >= 5:
        return f"Solid in {spread} episodes"
    return f"Shines in {spread} key episode" + ("s" if spread != 1 else "")

# find score ranges for star scaling
all_peaks = []
all_sustained = []
tmp = []
for title, s in shows.items():
    coverage = round(100 * s["with_ep"] / s["total"])
    spread = len(s["episodes_set"])
    log_scores = [math.log(x + 1) for x in s["scores"]]
    avg_log = sum(log_scores) / len(log_scores)
    peak = round(avg_log * math.log(len(s["scores"]) + 1), 2)
    measurable = coverage >= MIN_COVERAGE and spread >= MIN_SPREAD
    sustained = round(avg_log * math.log(spread + 1), 2) if measurable else None
    all_peaks.append(peak)
    if sustained is not None:
        all_sustained.append(sustained)
    tmp.append((title, s, coverage, spread, peak, sustained, measurable))

PEAK_LO, PEAK_HI = min(all_peaks), max(all_peaks)
SUS_LO, SUS_HI = (min(all_sustained), max(all_sustained)) if all_sustained else (0, 1)

ranked = []
excluded = []
for title, s, coverage, spread, peak, sustained, measurable in tmp:
    label = make_label(peak, sustained, spread, coverage, measurable, s["ep_count"])
    entry = {
        "title": title, "peak": peak, "sustained": sustained,
        "spread": spread, "coverage": coverage, "clips": s["total"],
        "measurable": measurable, "label": label,
        "peakStars": stars(peak, PEAK_LO, PEAK_HI),
        "sustainedStars": stars(sustained, SUS_LO, SUS_HI) if sustained is not None else 0,
        "phrase": consistency_phrase(spread, coverage, measurable, s["ep_count"]),
        "isFilm": s["ep_count"] is not None and s["ep_count"] <= 1
    }
    ranked.append(entry)
    if not measurable:
        if s["ep_count"] is not None and s["ep_count"] <= 1:
            reason = "film — no episodes to spread across"
        elif coverage < MIN_COVERAGE:
            reason = f"only {coverage}% of clips tied to episodes"
        else:
            reason = "too few episodes"
        excluded.append({"title": title, "peak": peak, "reason": reason, "label": label})

data_json = json.dumps(ranked)
excluded_json = json.dumps(sorted(excluded, key=lambda x: x["peak"], reverse=True))
conn.close()

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sakuga Index</title>
<style>
    body {{ font-family: -apple-system, system-ui, sans-serif; background: #0f0f14;
            color: #e8e8ea; max-width: 1000px; margin: 40px auto; padding: 0 20px; }}
    h1 {{ font-size: 2.4em; margin-bottom: 2px; }}
    .tagline {{ color: #9a9aa8; margin-bottom: 8px; }}
    .lens-desc {{ color: #7a7a8a; font-size: 0.9em; margin-bottom: 24px; font-style: italic; }}
    .toggle {{ display: flex; gap: 8px; margin-bottom: 20px; }}
    .toggle button {{ padding: 10px 18px; font-size: 0.95em; cursor: pointer; background: #1a1a22;
            border: 1px solid #3a3a48; border-radius: 8px; color: #9a9aa8; transition: all 0.2s; }}
    .toggle button.active {{ background: #7dd3a8; color: #0f0f14; border-color: #7dd3a8; font-weight: bold; }}
    #search {{ width: 100%; padding: 12px 16px; font-size: 1em; background: #1a1a22;
            border: 1px solid #3a3a48; border-radius: 8px; color: #e8e8ea; margin-bottom: 20px; box-sizing: border-box; }}
    #search:focus {{ outline: none; border-color: #7dd3a8; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th {{ text-align: left; padding: 10px 12px; border-bottom: 2px solid #3a3a48;
          color: #b8b8c8; font-size: 0.8em; text-transform: uppercase; }}
    td {{ padding: 12px; border-bottom: 1px solid #23232e; vertical-align: middle; }}
    tr:hover {{ background: #1a1a22; }}
    .rank {{ color: #6a6a7a; font-weight: bold; width: 40px; }}
    .title {{ font-weight: 600; }}
    .stars {{ color: #f5c518; font-size: 1.05em; letter-spacing: 1px; white-space: nowrap; }}
    .stars .empty {{ color: #3a3a44; }}
    .score-num {{ color: #6a6a7a; font-size: 0.75em; margin-left: 6px; }}
    .phrase {{ color: #9a9aa8; font-size: 0.85em; }}
    .label {{ display: inline-block; padding: 3px 10px; border-radius: 12px;
              font-size: 0.72em; font-weight: 600; margin-left: 8px; vertical-align: middle; }}
    .label-brilliant  {{ background: #1e3a2a; color: #7dd3a8; }}
    .label-viral      {{ background: #3a2a1e; color: #e0a458; }}
    .label-peak       {{ background: #2a1e3a; color: #b88ad8; }}
    .label-film       {{ background: #1e2a3a; color: #7da8d3; }}
    .label-steady     {{ background: #2a2a1e; color: #d3d37d; }}
    .label-solid      {{ background: #1e2a2a; color: #7dd3d3; }}
    .label-modest     {{ background: #25252e; color: #8a8a9a; }}
    .excluded-section {{ margin-top: 40px; padding: 20px; background: #15151c;
                         border: 1px solid #2a2a36; border-radius: 10px; }}
    .excluded-section h2 {{ font-size: 1.1em; margin-top: 0; }}
    .excluded-note {{ color: #9a9aa8; font-size: 0.9em; margin-bottom: 14px; }}
    .excluded-item {{ padding: 6px 0; border-bottom: 1px solid #23232e; font-size: 0.9em; }}
    .excluded-item .why {{ color: #7a7a8a; }}
    .hidden {{ display: none; }}
</style>
</head>
<body>
    <h1>Sakuga Index</h1>
    <p class="tagline">Ranking anime by animation craft — not story or popularity.</p>
    <p class="lens-desc" id="lens-desc"></p>

    <div class="toggle">
        <button id="btn-peak" class="active" onclick="setLens('peak')">Peak Craft</button>
        <button id="btn-sustained" onclick="setLens('sustained')">Sustained Craft</button>
    </div>

    <input type="text" id="search" placeholder="Search for an anime..." />

    <table>
        <thead id="thead"></thead>
        <tbody id="rankings"></tbody>
    </table>

    <div id="excluded-block" class="excluded-section hidden">
        <h2>Not rankable for Sustained Craft</h2>
        <p class="excluded-note">These shows can't be fairly measured for sustained craft —
        either they're films, or too few of their clips could be tied to specific episodes.
        We leave them out rather than rank them unfairly.</p>
        <div id="excluded-list"></div>
    </div>

<script>
    const shows = {data_json};
    const excluded = {excluded_json};
    let lens = 'peak';

    const descriptions = {{
        peak: "Peak Craft: the most celebrated individual cuts, viral or not. Rewards standout moments.",
        sustained: "Sustained Craft: quality spread across many episodes. Rewards consistency over a full run. Films and data-thin shows are listed separately below."
    }};

   function labelClass(label) {{
        const map = {{
            "Must-Watch Sakuga": "label-brilliant",
            "Great Throughout": "label-steady",
            "Worth It for a Few Episodes": "label-peak",
            "Big Moments, Less Consistent": "label-solid",
            "Hyped — Hard to Verify": "label-viral",
            "Film — Worth Seeing": "label-film",
            "Modest Sakuga Presence": "label-modest"
        }};
        return map[label] || "label-modest";
    }}

    function starHtml(n) {{
        let h = "";
        for (let i = 1; i <= 5; i++) h += i <= n ? "★" : '<span class="empty">★</span>';
        return `<span class="stars">${{h}}</span>`;
    }}

    function setLens(which) {{
        lens = which;
        document.getElementById('btn-peak').classList.toggle('active', which === 'peak');
        document.getElementById('btn-sustained').classList.toggle('active', which === 'sustained');
        document.getElementById('lens-desc').textContent = descriptions[which];
        document.getElementById('excluded-block').classList.toggle('hidden', which !== 'sustained');
        render(document.getElementById('search').value);
    }}

    function render(query = "") {{
        const q = query.toLowerCase();
        let list = shows.slice();
        if (lens === 'sustained') {{
            list = list.filter(s => s.measurable);
            list.sort((a, b) => b.sustained - a.sustained);
        }} else {{
            list.sort((a, b) => b.peak - a.peak);
        }}
        if (q) list = list.filter(s => s.title.toLowerCase().includes(q));

        document.getElementById('thead').innerHTML =
            `<tr><th>#</th><th>Title</th><th>Rating</th><th>Consistency</th></tr>`;

        const tbody = document.getElementById('rankings');
        tbody.innerHTML = "";
        list.forEach((s, i) => {{
            const badge = `<span class="label ${{labelClass(s.label)}}">${{s.label}}</span>`;
            const starN = lens === 'peak' ? s.peakStars : s.sustainedStars;
            const num = lens === 'peak' ? s.peak : s.sustained;
            tbody.innerHTML += `<tr>
                <td class="rank">${{i+1}}</td>
                <td class="title">${{s.title}}${{badge}}</td>
                <td>${{starHtml(starN)}}<span class="score-num">${{num}}</span></td>
                <td class="phrase">${{s.phrase}}</td></tr>`;
        }});
    }}

    const exList = document.getElementById('excluded-list');
    excluded.forEach(e => {{
        exList.innerHTML += `<div class="excluded-item">
            <span class="title">${{e.title}}</span>
            <span class="label ${{labelClass(e.label)}}">${{e.label}}</span>
            <span class="why"> — ${{e.reason}}</span></div>`;
    }});

    document.getElementById('search').addEventListener('input', (e) => render(e.target.value));
    setLens('peak');
</script>
</body>
</html>"""

with open("index.html", "w") as f:
    f.write(html)

print("Generated index.html with stars, fixed labels, and human-readable columns!")