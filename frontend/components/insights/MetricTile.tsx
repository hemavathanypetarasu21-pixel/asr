export default function MetricTile({
  label,
  value,
  hint,
  tone = "default",
}: {
  label: string;
  value: string;
  hint?: string;
  tone?: "default" | "warn";
}) {
  return (
    <div className={`rounded-md border p-3 ${tone === "warn" ? "border-danger/40 bg-danger-soft" : "border-line bg-subtle"}`}>
      <p className="text-[11px] font-semibold uppercase tracking-wide text-muted">{label}</p>
      <p className="mt-0.5 text-sm font-semibold text-heading">{value}</p>
      {hint && <p className={`mt-0.5 text-xs ${tone === "warn" ? "text-danger" : "text-muted"}`}>{hint}</p>}
    </div>
  );
}
