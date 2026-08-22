import { cn } from "@/lib/utils";

interface ScoreBadgeProps {
  score: number | null;
}

export default function ScoreBadge({
  score,
}: ScoreBadgeProps) {
  if (score === null) {
    return (
      <span className="text-gray-400 text-sm">
        N/A
      </span>
    );
  }

  let style =
    "bg-gray-100 text-gray-700";

  if (score >= 70) {
    style =
      "bg-green-100 text-green-700";
  } else if (score >= 50) {
    style =
      "bg-yellow-100 text-yellow-700";
  } else if (score >= 30) {
    style =
      "bg-orange-100 text-orange-700";
  } else {
    style =
      "bg-red-100 text-red-700";
  }

  return (
    <span
      className={cn(
        "px-3 py-1 rounded-full text-sm font-semibold",
        style
      )}
    >
      {score.toFixed(1)}%
    </span>
  );
}