const AVATAR_COLORS = ["bg-brand", "bg-accent", "bg-[#c2410c]", "bg-[#0369a1]", "bg-[#7e22ce]", "bg-[#be185d]"];

function initials(name: string) {
  const parts = name.trim().split(/[\s@._-]+/).filter(Boolean);
  return ((parts[0]?.[0] ?? "?") + (parts[1]?.[0] ?? "")).toUpperCase();
}

/** Stable colour per user so the same person always gets the same avatar. */
function colorFor(seed: string) {
  let hash = 0;
  for (const char of seed) hash = (hash * 31 + char.charCodeAt(0)) | 0;
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
}

export default function Avatar({ name, size = "md" }: { name: string; size?: "sm" | "md" | "lg" }) {
  const dimensions = { sm: "h-7 w-7 text-[11px]", md: "h-8 w-8 text-xs", lg: "h-12 w-12 text-base" }[size];
  return (
    <span
      className={`inline-flex shrink-0 select-none items-center justify-center rounded-full font-semibold text-white ${dimensions} ${colorFor(name)}`}
      aria-hidden="true"
    >
      {initials(name)}
    </span>
  );
}
