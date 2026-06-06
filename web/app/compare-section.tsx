"use client";

import { useState } from "react";
import type { Show } from "./types";
import { labelClass } from "./types";

function verdict(a: Show, b: Show): { headline: string; detail: string } {
  if (a.isFilm !== b.isFilm) {
    const film = a.isFilm ? a : b;
    const series = a.isFilm ? b : a;
    return {
      headline: "Different things entirely",
      detail:
        `${film.title} is a film and ${series.title} is a series — not directly comparable. ` +
        `${film.title} delivers a single concentrated work; ${series.title} is judged across its full run (${series.phrase.toLowerCase()}).`,
    };
  }
  if (a.isFilm && b.isFilm) {
    const hi = a.peak >= b.peak ? a : b;
    const lo = a.peak >= b.peak ? b : a;
    return {
      headline: `${hi.title} edges ahead on celebrated craft`,
      detail:
        `Both are films. ${hi.title} has the higher peak-craft rating (${hi.peak} vs ${lo.peak}), ` +
        `meaning its standout cuts drew more acclaim — though both are worth seeing.`,
    };
  }
  const aHype = !a.measurable;
  const bHype = !b.measurable;
  if (aHype && bHype) {
    return {
      headline: "Both are hard to verify",
      detail:
        `${a.title} and ${b.title} both score on buzz, but most of their clips are promo/social — ` +
        `we can't confirm episode-to-episode craft for either. Treat the ratings as hype, not proven consistency.`,
    };
  }
  if (aHype || bHype) {
    const hyped = aHype ? a : b;
    const solid = aHype ? b : a;
    return {
      headline: `${solid.title} is the safer bet for proven craft`,
      detail:
        `${hyped.title} scores higher on peak buzz (${hyped.peak}), but most of its clips are promo/social, ` +
        `so we can't verify consistent animation. ${solid.title} has verifiable quality — ${solid.phrase.toLowerCase()}. ` +
        `Pick ${hyped.title} for hyped moments, ${solid.title} for reliable craft.`,
    };
  }
  const peakWin = a.peak >= b.peak ? a : b;
  const susWin = (a.sustained ?? 0) >= (b.sustained ?? 0) ? a : b;
  if (peakWin.title === susWin.title) {
    const winner = peakWin;
    const other = winner.title === a.title ? b : a;
    return {
      headline: `${winner.title} is the stronger pick overall`,
      detail:
        `${winner.title} leads on both standout moments (peak ${winner.peak} vs ${other.peak}) ` +
        `and consistency (${winner.phrase.toLowerCase()}). ${other.title} is still solid — ` +
        `${other.phrase.toLowerCase()} — but ${winner.title} wins on both dimensions.`,
    };
  }
  return {
    headline: "Depends what you're after",
    detail:
      `${peakWin.title} has the higher standout moments (peak ${peakWin.peak}), while ` +
      `${susWin.title} is more consistent (${susWin.phrase.toLowerCase()}). ` +
      `Pick ${peakWin.title} for the best individual cuts, ${susWin.title} for sustained quality across its run.`,
  };
}

export default function CompareSection({ shows }: { shows: Show[] }) {
  const sorted = [...shows].sort((a, b) => a.title.localeCompare(b.title));
  const [titleA, setTitleA] = useState(sorted[0]?.title ?? "");
  const [titleB, setTitleB] = useState(sorted[1]?.title ?? "");

  const showA = shows.find((s) => s.title === titleA);
  const showB = shows.find((s) => s.title === titleB);
  const result = showA && showB && titleA !== titleB ? verdict(showA, showB) : null;

  return (
    <div style={{ margin: "28px 0", padding: 20, background: "#15151c", borderRadius: 10, border: "1px solid #2a2a36" }}>
      <h2 style={{ fontSize: "1.15em", margin: "0 0 14px" }}>Compare two anime</h2>

      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
        <select value={titleA} onChange={(e) => setTitleA(e.target.value)} style={selectStyle}>
          {sorted.map((s) => <option key={s.title} value={s.title}>{s.title}</option>)}
        </select>
        <span style={{ color: "#7a7a8a" }}>vs</span>
        <select value={titleB} onChange={(e) => setTitleB(e.target.value)} style={selectStyle}>
          {sorted.map((s) => <option key={s.title} value={s.title}>{s.title}</option>)}
        </select>
      </div>

      {titleA === titleB && (
        <p style={{ marginTop: 14, color: "#7a7a8a" }}>Pick two different anime to compare.</p>
      )}

      {result && (
        <div style={{ marginTop: 16, background: "#12121a", border: "1px solid #2a2a36", borderRadius: 10, padding: 18 }}>
          <div style={{ display: "flex", gap: 20, marginBottom: 14, flexWrap: "wrap" }}>
            {[showA!, showB!].map((s) => (
              <div key={s.title} style={{ flex: 1, minWidth: 180 }}>
                <div style={{ fontWeight: 600, marginBottom: 4 }}>{s.title}</div>
                <div style={{ color: "#9a9aa8", fontSize: "0.88em" }}>
                  <span className={`badge ${labelClass(s.label)}`} style={{ marginLeft: 0, marginRight: 6 }}>{s.label}</span>
                  peak {s.peak} · {s.phrase}
                </div>
              </div>
            ))}
          </div>
          <div style={{ fontWeight: 700, color: "#7dd3a8", marginBottom: 10, fontSize: "1.05em", fontFamily: "var(--font-heading, sans-serif)" }}>
            {result.headline}
          </div>
          <div style={{ color: "#c8c8d4", lineHeight: 1.6, fontSize: "0.95em" }}>{result.detail}</div>
        </div>
      )}
    </div>
  );
}

const selectStyle: React.CSSProperties = {
  padding: "10px 12px",
  fontSize: "0.95em",
  background: "#1a1a22",
  border: "1px solid #3a3a48",
  borderRadius: 8,
  color: "#e8e8ea",
  minWidth: 200,
  fontFamily: "var(--font-body, sans-serif)",
};
