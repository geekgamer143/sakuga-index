"use client";

import { useState } from "react";
import type { Show } from "./types";
import { labelClass } from "./types";

type Lens = "peak" | "sustained";

function Stars({ count, score }: { count: number; score: number }) {
  return (
    <span style={{ whiteSpace: "nowrap" }}>
      {[1, 2, 3, 4, 5].map((i) => (
        <span key={i} style={{ color: i <= count ? "#f5c518" : "#3a3a44", fontSize: "1.05em", letterSpacing: 1 }}>★</span>
      ))}
      <span style={{ color: "#6a6a7a", fontSize: "0.75em", marginLeft: 6 }}>{score}</span>
    </span>
  );
}

export default function RankingsTable({ shows }: { shows: Show[] }) {
  const [lens, setLens] = useState<Lens>("peak");

  const sorted = [...shows]
    .filter((s) => (lens === "sustained" ? s.measurable : true))
    .sort((a, b) =>
      lens === "peak" ? b.peak - a.peak : (b.sustained ?? 0) - (a.sustained ?? 0)
    );

  return (
    <div>
      <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
        <button style={lens === "peak" ? activeBtn : btn} onClick={() => setLens("peak")}>
          Peak Craft
        </button>
        <button style={lens === "sustained" ? activeBtn : btn} onClick={() => setLens("sustained")}>
          Sustained Craft
        </button>
      </div>
      <p style={{ color: "#7a7a8a", fontSize: "0.9em", fontStyle: "italic", marginBottom: 24 }}>
        {lens === "peak"
          ? "Peak Craft: the most celebrated individual cuts, viral or not. Rewards standout moments."
          : "Sustained Craft: quality spread across many episodes. Rewards consistency over a full run. Films and data-thin shows are listed separately below."}
      </p>

      <table>
        <thead>
          <tr>
            <th style={{ width: 40 }}>#</th>
            <th>Title</th>
            <th>Rating</th>
            <th>Consistency</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((show, i) => (
            <tr key={show.title}>
              <td style={{ color: "#6a6a7a", fontWeight: "bold" }}>{i + 1}</td>
              <td style={{ fontWeight: 600 }}>
                {show.title}
                <span className={`badge ${labelClass(show.label)}`}>{show.label}</span>
              </td>
              <td>
                <Stars
                  count={lens === "peak" ? show.peakStars : show.sustainedStars}
                  score={lens === "peak" ? show.peak : (show.sustained ?? 0)}
                />
              </td>
              <td style={{ color: "#9a9aa8", fontSize: "0.85em" }}>{show.phrase}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const btn: React.CSSProperties = {
  padding: "10px 18px",
  cursor: "pointer",
  background: "#1a1a22",
  border: "1px solid #3a3a48",
  borderRadius: 8,
  color: "#9a9aa8",
  fontSize: "0.95em",
  fontFamily: "var(--font-heading, sans-serif)",
  transition: "all 0.2s",
};

const activeBtn: React.CSSProperties = {
  ...btn,
  background: "#7dd3a8",
  color: "#0f0f14",
  borderColor: "#7dd3a8",
  fontWeight: "bold",
};
