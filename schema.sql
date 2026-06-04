-- studios: anime production companies (the "one" side)
CREATE TABLE studios (
    studio_id   INTEGER PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE
);

-- anime: the shows (metadata spine from AniList)
CREATE TABLE anime (
    anime_id          INTEGER PRIMARY KEY,
    title             TEXT NOT NULL,
    release_year      INTEGER,
    episodes          INTEGER,
    anilist_score     INTEGER,
    studio_id         INTEGER,
    sakugabooru_tag   TEXT,
    data_status       TEXT DEFAULT 'pending',
    FOREIGN KEY (studio_id) REFERENCES studios(studio_id)
);
-- clips: individual sakuga posts from Sakugabooru
CREATE TABLE clips (
    clip_id          INTEGER PRIMARY KEY,
    anime_id         INTEGER,
    community_score  INTEGER,
    episode_source   TEXT,
    created_at       INTEGER,
    FOREIGN KEY (anime_id) REFERENCES anime(anime_id)
);
-- animators: individual animators (from Sakugabooru artist tags)
CREATE TABLE animators (
    animator_id   INTEGER PRIMARY KEY,
    name          TEXT NOT NULL UNIQUE
);
-- clip_animators: bridge table linking clips to animators (many-to-many)
CREATE TABLE clip_animators (
    clip_id       INTEGER,
    animator_id   INTEGER,
    PRIMARY KEY (clip_id, animator_id),
    FOREIGN KEY (clip_id) REFERENCES clips(clip_id),
    FOREIGN KEY (animator_id) REFERENCES animators(animator_id)
);