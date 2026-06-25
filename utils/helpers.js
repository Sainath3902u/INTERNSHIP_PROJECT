export function getScoreColor(score) {
  if (score <= 0.15) {
    return {
      text: "text-emerald-600 dark:text-emerald-400",
      bg: "bg-emerald-50 dark:bg-emerald-950/30",
      border: "border-emerald-200 dark:border-emerald-800",
      label: "Excellent Match"
    };
  } else if (score <= 0.30) {
    return {
      text: "text-amber-600 dark:text-amber-400",
      bg: "bg-amber-50 dark:bg-amber-950/30",
      border: "border-amber-200 dark:border-amber-800",
      label: "Acceptable Deviation"
    };
  } else {
    return {
      text: "text-rose-600 dark:text-rose-400",
      bg: "bg-rose-50 dark:bg-rose-950/30",
      border: "border-rose-200 dark:border-rose-800",
      label: "Significant Divergence"
    };
  }
}

export function formatScore(score) {
  if (typeof score !== "number") return "0.00";
  return score.toFixed(2);
}

export function convertToConfidence(score) {
  if (typeof score !== "number") return "0%";
  const confidence = Math.max(0, (1 - score) * 100);
  return `${confidence.toFixed(0)}%`;
}