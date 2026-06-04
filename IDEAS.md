# Sakuga Index — v3 Ideas & Findings

## Key findings (from Craft Score analysis)
- Sakugabooru community scores entangle animation QUALITY with FANDOM SIZE/virality.
  Acknowledged classics (Frieren, Naruto: Shippuuden) rank lower than reputation
  because their fanbases upvote less than viral-hit fandoms. Documented limitation.
- Craft is UNEVEN within a show. Boruto ranks high almost entirely on one ending
  (NCED23) and one episode (#87), not broad consistency. Average-based score can't
  tell "consistently great" from "few brilliant moments."

## v3 ideas to build
1. Per-episode analysis: parse episode_source (#08 (BD) -> 8, reject NCOP/NCED/OP/PV/URLs)
   to measure consistency vs. peak craft, and power the episode heatmap feature.
2. Two separate rankings: "Craft Score" (per-moment quality) vs "Sakuga Volume"
   (body of celebrated work). Stop forcing one number to do both jobs.
3. Uncap clip collection (currently max_clips=20) so volume/consistency signal is real.
4. Mob Psycho 100: excluded (insufficient_data) — tag with numeral doesn't resolve via
   post API. Documented data-source limitation.

## Session findings: combined quality + consistency analysis
- Built 3-dimension view: Craft Score (quality) + episode spread (consistency) + coverage % (trust flag).
- Three kinds of "good animation" now distinguished:
  * BROADLY EXCELLENT: high craft + high spread + high coverage (Vinland Saga, AoT, Gurren Lagann)
  * PEAKY BRILLIANT: high craft + low spread + high coverage (Frieren ~2 eps, One Punch Man ~3 eps)
  * CANNOT ASSESS: high craft + low coverage (Chainsaw Man, JJK) — consistency unmeasurable
- KEY FINDING: Chainsaw Man ranks #1 but its clips are mostly promotional/social (PR trailers, OP/ED).
  Its score reflects marketing reach + fandom hype, NOT episode craft. Confirms the popularity confound
  concretely: community scores conflate animation quality with fandom size and promotional buzz.
- Coverage flag (<50% episode data) successfully identifies which rankings NOT to trust.
