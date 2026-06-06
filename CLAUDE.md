# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

Sakuga Index ranks anime by animation craft using data from two sources:
- **Sakugabooru** — a community site that tags and scores individual animation clips
- **AniList** — for canonical metadata (title, episode count, studio, score)

The core insight: Sakugabooru community scores conflate animation quality with fandom size and viral/promotional buzz. The project builds two honest metrics:
- **Peak Craft** — `avg_log(score+1) × log(clip_count+1)` — rewards celebrated individual cuts
- **Sustained Craft** — `avg_log(score+1) × log(episode_spread+1)` — rewards consistency across episodes; requires ≥50% episode coverage and ≥2 episodes to be measurable

## Pipeline (run in order)

```bash
# 1. Populate the database from Sakugabooru + AniList (slow — hits external APIs)
python build_database.py

# 2. Parse episode numbers out of the messy episode_source strings
python parse_episodes.py

# 3. Generate the static site
python generate_site.py
# → writes index.html
```

### Other analysis scripts (not part of the main pipeline)
```bash
python craft_score.py        # prints peak-craft rankings to stdout
python consistency_score.py  # prints sustained-craft rankings to stdout
python combined_analysis.py  # prints both metrics + coverage flag to stdout
```

## Database

SQLite file: `sakuga.db`. Schema in `schema.sql`.

Key columns:
- `clips.episode_source` — raw text from Sakugabooru (e.g. `"#08 (BD)"`, `"NCED23"`, `"https://…"`)
- `clips.episode_number` — parsed integer; populated by `parse_episodes.py` using the `#NNN` pattern; NULL for OP/ED/URLs/promos
- `anime.data_status` — `'loaded'`, `'insufficient_data'`, or `'pending'`
- `anime.sakugabooru_tag` — resolved tag used to query the Sakugabooru API

## Tag resolution

`build_database.py` auto-resolves Sakugabooru tags by fuzzy-matching the anime title, with truncating fallback (drops trailing words). Manual overrides live in `tag_overrides.txt` as `SearchTerm=sakugabooru_tag` pairs. Resolved tag types are cached in `tag_type_cache.json` to avoid redundant API calls.

Known limitation: shows whose Sakugabooru tag contains a numeral (e.g. Mob Psycho 100) may fail to resolve via the post API — mark as `insufficient_data`.

## Site output

`generate_site.py` reads from `sakuga.db`, computes all metrics, serializes them to JSON, and writes a single self-contained `index.html`. The site has:
- Toggle between Peak Craft and Sustained Craft rankings
- Per-show labels (e.g. "Must-Watch Sakuga", "Hyped — Hard to Verify") derived from peak/sustained/spread/coverage combo
- "Not rankable" exclusions section for films and low-coverage shows
- Compare mode with natural-language verdicts

The site is pure HTML/JS — no build step, no framework. All data is inlined as a JS constant.

## Key scoring thresholds

| Threshold | Value | Purpose |
|---|---|---|
| `MIN_COVERAGE` | 50% | Min % of clips with episode numbers to call a show "measurable" |
| `MIN_SPREAD` | 2 | Min distinct episodes to rank for Sustained Craft |
| Sustained ≥ 14 | — | "Must-Watch Sakuga" label |
| Sustained ≥ 10 | — | "Great Throughout" label |
| Peak ≥ 18 + spread ≤ 5 | — | "Worth It for a Few Episodes" label |
