import re
import sqlite3

def parse_episode(source):
    """Extract a clean episode number from messy episode_source text.
    Returns an integer, or None if there's no episode number."""
    if not source:                      # handles None and empty string
        return None
    match = re.search(r"#(\d+)", source)   # find digits right after a '#'
    if match:
        return int(match.group(1))         # group(1) is the captured digits
    return None                            # no '#number' pattern -> not an episode

# --- TEST IT against real values before we touch the database ---
test_values = [
    "#08 (BD)",
    "#1163",
    "#06 (SB/AD: Kai Ikarashi)",
    "#087 (BD) (NC)",
    "NCED23",
    "OP",
    "https://www.youtube.com/watch?v=FLB_sLTgbPk",
    "",
    "#11 ",
]

for v in test_values:
    print(f"{v!r:50} -> {parse_episode(v)}")

def populate_episode_numbers():
    """Parse episode_source for every clip and store the clean number."""
    conn = sqlite3.connect("sakuga.db")
    cursor = conn.cursor()

    # get every clip's id and its raw source
    cursor.execute("SELECT clip_id, episode_source FROM clips")
    clips = cursor.fetchall()

    updated = 0
    skipped = 0
    for clip_id, source in clips:
        ep = parse_episode(source)
        if ep is not None:
            cursor.execute(
                "UPDATE clips SET episode_number = ? WHERE clip_id = ?",
                (ep, clip_id)
            )
            updated += 1
        else:
            skipped += 1

    conn.commit()
    conn.close()
    print(f"Episode numbers parsed: {updated} clips updated, {skipped} had no episode number")

populate_episode_numbers()
    