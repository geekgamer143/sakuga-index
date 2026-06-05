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

results = []
for title, s in shows.items():
    log_scores = [math.log(x + 1) for x in s["scores"]]
    avg_log = sum(log_scores) / len(log_scores)
    craft = round(avg_log * math.log(len(s["scores"]) + 1), 2)
    spread = len(s["episodes"])
    coverage = round(100 * s["with_ep"] / s["total"])
    results.append({
        "title": title, "craft": craft, "spread": spread,
        "coverage": coverage, "clips": s["total"]
    })

results.sort(key=lambda x: x["craft"], reverse=True)
conn.close()

data_json = json.dumps(results)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Sakuga Index</title>
    <style>
        body {{
            font-family: -apple-system, system-ui, sans-serif;
            background: #0f0f14; color: #e8e8ea;
            max-width: 900px; margin: 40px auto; padding: 0 20px;
        }}
        h1 {{ font-size: 2.2em; margin-bottom: 4px; }}
        h2 {{ font-size: 1.3em; margin: 0 0 12px 0; }}
        .tagline {{ color: #9a9aa8; margin-bottom: 24px; }}
        #search {{
            width: 100%; padding: 12px 16px; font-size: 1em;
            background: #1a1a22; border: 1px solid #3a3a48;
            border-radius: 8px; color: #e8e8ea; margin-bottom: 24px;
            box-sizing: border-box;
        }}
        #search:focus {{ outline: none; border-color: #7dd3a8; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{
            text-align: left; padding: 10px 12px;
            border-bottom: 2px solid #3a3a48;
            color: #b8b8c8; font-size: 0.85em; text-transform: uppercase;
        }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #23232e; }}
        .rank {{ color: #6a6a7a; font-weight: bold; width: 40px; }}
        .title {{ font-weight: 600; }}
        .craft {{ color: #7dd3a8; font-weight: bold; }}
        .flag {{ color: #e0a458; font-size: 0.8em; }}
        tr {{ transition: opacity 0.2s; }}
        /* NEW: styling for the compare dropdowns + section */
        #compare-section {{
            background: #15151c; border: 1px solid #2a2a36;
            border-radius: 10px; padding: 20px; margin-bottom: 30px;
        }}
        select {{
            padding: 10px 12px; font-size: 0.95em; margin-right: 10px;
            background: #1a1a22; border: 1px solid #3a3a48;
            border-radius: 8px; color: #e8e8ea;
        }}
        select:focus {{ outline: none; border-color: #7dd3a8; }}
    </style>
</head>
<body>
    <h1>Sakuga Index</h1>
    <p class="tagline">Ranking anime by animation craft — not story or popularity.</p>

    <input type="text" id="search" placeholder="Search for an anime..." />

    <!-- NEW: compare section -->
    <div id="compare-section">
        <h2>Compare Two Anime</h2>
        <select id="showA"></select>
        <select id="showB"></select>
        <div id="compare-result"></div>
    </div>

    <table>
        <thead>
            <tr>
                <th>#</th><th>Title</th><th>Craft Score</th>
                <th>Spread</th><th>Coverage</th><th>Clips</th>
            </tr>
        </thead>
        <tbody id="rankings"></tbody>
    </table>

    <script>
        const shows = {data_json};

        function renderTable(list) {{
            const tbody = document.getElementById("rankings");
            tbody.innerHTML = "";
            list.forEach((show, i) => {{
                const flag = show.coverage < 50
                    ? '<span class="flag">⚠ low coverage</span>' : '';
                tbody.innerHTML += `
                    <tr>
                        <td class="rank">${{i + 1}}</td>
                        <td class="title">${{show.title}}</td>
                        <td class="craft">${{show.craft}}</td>
                        <td>${{show.spread}}</td>
                        <td>${{show.coverage}}% ${{flag}}</td>
                        <td>${{show.clips}}</td>
                    </tr>`;
            }});
        }}

        renderTable(shows);

        document.getElementById("search").addEventListener("input", (e) => {{
            const query = e.target.value.toLowerCase();
            const filtered = shows.filter(s =>
                s.title.toLowerCase().includes(query)
            );
            renderTable(filtered);
        }});

        // NEW: ---- COMPARE MODE ----
        const selA = document.getElementById("showA");
        const selB = document.getElementById("showB");
        shows.forEach(s => {{
            selA.innerHTML += `<option value="${{s.title}}">${{s.title}}</option>`;
            selB.innerHTML += `<option value="${{s.title}}">${{s.title}}</option>`;
        }});
        // start the two dropdowns on different shows so the comparison isn't identical
        if (shows.length > 1) selB.selectedIndex = 1;

        function renderComparison() {{
            const a = shows.find(s => s.title === selA.value);
            const b = shows.find(s => s.title === selB.value);
            if (!a || !b) return;
            document.getElementById("compare-result").innerHTML = `
                <table style="margin-top: 16px;">
                    <tr><th>Metric</th><th>${{a.title}}</th><th>${{b.title}}</th></tr>
                    <tr><td>Craft Score</td><td class="craft">${{a.craft}}</td><td class="craft">${{b.craft}}</td></tr>
                    <tr><td>Episode Spread</td><td>${{a.spread}}</td><td>${{b.spread}}</td></tr>
                    <tr><td>Coverage</td><td>${{a.coverage}}%</td><td>${{b.coverage}}%</td></tr>
                    <tr><td>Clips</td><td>${{a.clips}}</td><td>${{b.clips}}</td></tr>
                </table>`;
        }}

        selA.addEventListener("change", renderComparison);
        selB.addEventListener("change", renderComparison);
        renderComparison();
    </script>
</body>
</html>"""

with open("index.html", "w") as f:
    f.write(html)

print("Generated index.html with compare mode — open it and try the dropdowns!")