const LABEL_CLASS: Record<string, string> = {
  "Must-Watch Sakuga":          "badge-brilliant",
  "Great Throughout":           "badge-steady",
  "Worth It for a Few Episodes":"badge-peak",
  "Big Moments, Less Consistent":"badge-solid",
  "Hyped — Hard to Verify":     "badge-viral",
  "Film — Worth Seeing":        "badge-film",
  "Modest Sakuga Presence":     "badge-modest",
};

export function labelClass(label: string): string {
  return LABEL_CLASS[label] ?? "badge-modest";
}

export type Show = {
  title: string;
  peak: number;
  sustained: number | null;
  spread: number;
  coverage: number;
  clips: number;
  measurable: boolean;
  label: string;
  peakStars: number;
  sustainedStars: number;
  phrase: string;
  isFilm: boolean;
};
