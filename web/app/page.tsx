import data from "@/data/rankings.json";
import RankingsTable from "./rankings-table";
import CompareSection from "./compare-section";
import type { Show } from "./types";

export default function Home() {
  const shows = data.shows as Show[];

  return (
    <main style={{ maxWidth: 1000, margin: "48px auto", padding: "0 24px" }}>
      <h1>Sakuga Index</h1>
      <p style={{ color: "#9a9aa8", marginBottom: 8 }}>
        Ranking anime by animation craft — not story or popularity.
      </p>
      <CompareSection shows={shows} />
      <RankingsTable shows={shows} />
    </main>
  );
}
