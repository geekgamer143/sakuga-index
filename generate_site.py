import sqlite3
import math
import json
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

MIN_COVERAGE = 50
MIN_SPREAD = 2

ranked = []        # has both scores, sortable either way
excluded = []      # not measurable for sustained craft

for title, s in shows.items():
    coverage = round(100 * s["with_ep"] / s["total"])
    spread = len(s["episodes"])
    log_scores = [math.log(x + 1) for x in s["scores"]]
    avg_log = sum(log_scores) / len(log_scores)
    peak = round(avg_log * math.log(len(s["scores"]) + 1), 2)

    measurable = coverage >= MIN_COVERAGE and spread >= MIN_SPREAD
    sustained = round(avg_log * math.log(spread + 1), 2) if measurable else None

    entry = {
        "title": title, "peak": peak, "sustained": sustained,
        "spread": spread, "coverage": coverage, "clips": s["total"],
        "measurable": measurable
    }
    ranked.append(entry)
    if not measurable:
        # fix the reason logic: check coverage first, then film/episodes
        if coverage < MIN_COVERAGE:
            reason = f"low coverage ({coverage}%)"
        else:
            reason = "film / no episodes"
        excluded.append({"title": title, "peak": peak, "reason": reason})

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
    body {{
        font-family: -apple-system, system-ui, sans-serif;
        background: #0f0f14; color: #e8e8ea;
        max-width: 1000px; margin: 40px auto; padding: 0 20px;
    }}
    h1 {{ font-size: 2.4em; margin-bottom: 2px; }}
    .tagline {{ color: #9a9aa8; margin-bottom: 8px; }}
    .lens-desc {{ color: #7a7a8a; font-size: 0.9em; margin-bottom: 24px; font-style: italic; }}
    .toggle {{ display: flex; gap: 8px; margin-bottom: 20px; }}
    .toggle button {{
        padding: 10px 18px; font-size: 0.95em; cursor: pointer;
        background: #1a1a22; border: 1px solid #3a3a48; border-radius: 8px;
        color: #9a9aa8; transition: all 0.2s;
    }}
    .toggle button.active {{ background: #7dd3a8; color: #0f0f14; border-color: #7dd3a8; font-weight: bold; }}
    #search {{
        width: 100%; padding: 12px 16px; font-size: 1em;
        background: #1a1a22; border: 1px solid #3a3a48; border-radius: 8px;
        color: #e8e8ea; margin-bottom: 20px; box-sizing: border-box;
    }}
    #search:focus {{ outline: none; border-color: #7dd3a8; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th {{ text-align: left; padding: 10px 12px; border-bottom: 2px solid #3a3a48;
          color: #b8b8c8; font-size: 0.8em; text-transform: uppercase; }}
    td {{ padding: 10px 12px; border-bottom: 1px solid #23232e; }}
    tr {{ transition: opacity 0.2s; }}
    tr:hover {{ background: #1a1a22; }}
    .rank {{ color: #6a6a7a; font-weight: bold; width: 40px; }}
    .title {{ font-weight: 600; }}
    .primary {{ color: #7dd3a8; font-weight: bold; }}
    .secondary {{ color: #7a7a8a; font-size: 0.9em; }}
    .flag {{ color: #e0a458; font-size: 0.8em; }}
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
        either they're films (no episodes) or too few of their clips carry episode data.
        We exclude them rather than rank them unfairly.</p>
        <div id="excluded-list"></div>
    </div>

<script>
    const shows = {data_json};
    const excluded = {excluded_json};
    let lens = 'peak';

    const descriptions = {{
        peak: "Peak Craft: the most celebrated individual cuts, viral or not. Rewards standout moments.",
        sustained: "Sustained Craft: quality spread across many episodes. Rewards consistency over a full run. Films and low-coverage shows are excluded below."
    }};

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
        // pick & sort by the active lens
        let list = shows.slice();
        if (lens === 'sustained') {{
            list = list.filter(s => s.measurable);
            list.sort((a, b) => b.sustained - a.sustained);
        }} else {{
            list.sort((a, b) => b.peak - a.peak);
        }}
        if (q) list = list.filter(s => s.title.toLowerCase().includes(q));

        // header
        const thead = document.getElementById('thead');
        if (lens === 'peak') {{
            thead.innerHTML = `<tr><th>#</th><th>Title</th><th>Peak Craft</th>
                <th>Spread</th><th>Coverage</th><th>Clips</th></tr>`;
        }} else {{
            thead.innerHTML = `<tr><th>#</th><th>Title</th><th>Sustained</th>
                <th>Peak</th><th>Spread</th><th>Coverage</th></tr>`;
        }}

        const tbody = document.getElementById('rankings');
        tbody.innerHTML = "";
        list.forEach((s, i) => {{
            if (lens === 'peak') {{
                const flag = s.coverage < 50 ? '<span class="flag">⚠ low-cov</span>' : '';
                tbody.innerHTML += `<tr>
                    <td class="rank">${{i+1}}</td>
                    <td class="title">${{s.title}}</td>
                    <td class="primary">${{s.peak}}</td>
                    <td>${{s.spread}}</td>
                    <td>${{s.coverage}}% ${{flag}}</td>
                    <td>${{s.clips}}</td></tr>`;
            }} else {{
                tbody.innerHTML += `<tr>
                    <td class="rank">${{i+1}}</td>
                    <td class="title">${{s.title}}</td>
                    <td class="primary">${{s.sustained}}</td>
                    <td class="secondary">${{s.peak}}</td>
                    <td>${{s.spread}}</td>
                    <td>${{s.coverage}}%</td></tr>`;
            }}
        }});
    }}

    // build excluded list once
    const exList = document.getElementById('excluded-list');
    excluded.forEach(e => {{
        exList.innerHTML += `<div class="excluded-item">
            <span class="title">${{e.title}}</span>
            <span class="why"> — ${{e.reason}} (peak craft ${{e.peak}})</span></div>`;
    }});

    document.getElementById('search').addEventListener('input', (e) => render(e.target.value));

    // initial
    setLens('peak');
</script>
</body>
</html>"""

with open("index.html", "w") as f:
    f.write(html)

print("Generated dual-ranking index.html — open it and try the Peak/Sustained toggle!")