"use client";

import { useCallback, useEffect, useState } from "react";
import DatasetClipItem from "@/components/dataset/DatasetClipItem";
import { getApiErrorMessage } from "@/lib/api/client";
import { getDatasetClips } from "@/lib/api/endpoints";
import type { DatasetClip, DatasetPage, DatasetSplit } from "@/lib/api/types";
import { useOptions } from "@/lib/api/useOptions";
import { labelFor } from "@/lib/format";

const PAGE_SIZE = 20;
const SPLITS: { id: DatasetSplit; label: string }[] = [
  { id: "train", label: "Train" },
  { id: "validation", label: "Validation" },
  { id: "test", label: "Test" },
];

export default function DatasetWorkspace() {
  const { options } = useOptions();
  const [language, setLanguage] = useState("");
  const [split, setSplit] = useState<DatasetSplit | "">("");
  const [clips, setClips] = useState<DatasetClip[]>([]);
  const [total, setTotal] = useState(0);
  const [summary, setSummary] = useState<DatasetPage["summary"]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const languages = options?.languages ?? [];

  const load = useCallback(async (skip: number) => {
    setIsLoading(true);
    setError(null);
    try {
      const page = await getDatasetClips({ language: language || undefined, split: split || undefined, skip, limit: PAGE_SIZE });
      setClips((current) => (skip === 0 ? page.items : [...current, ...page.items]));
      setTotal(page.total);
      setSummary(page.summary);
    } catch (caught) {
      setError(getApiErrorMessage(caught, "The dataset could not be loaded."));
    } finally {
      setIsLoading(false);
    }
  }, [language, split]);

  useEffect(() => {
    // Reload from the first page whenever a filter changes.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load(0);
  }, [load]);

  const totalClips = summary.reduce((sum, group) => sum + group.clips, 0);
  const totalHours = summary.reduce((sum, group) => sum + group.hours, 0);
  const languageTotals = Array.from(new Set(summary.map((group) => group.language))).map((id) => ({
    id,
    clips: summary.filter((group) => group.language === id).reduce((sum, group) => sum + group.clips, 0),
  }));

  return (
    <div className="mx-auto grid w-full max-w-5xl gap-3 px-4 py-4 sm:px-6">
      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4" aria-label="Summary">
        {[
          { label: "Clips", value: totalClips.toLocaleString() },
          { label: "Hours of audio", value: totalHours.toFixed(2) },
          ...languageTotals.map((item) => ({ label: labelFor(languages, item.id), value: item.clips.toLocaleString() })),
        ].map((stat) => (
          <div key={stat.label} className="card px-3 py-2.5">
            <p className="text-[11px] font-semibold text-muted">{stat.label}</p>
            <p className="text-lg font-bold text-heading">{stat.value}</p>
          </div>
        ))}
      </section>

      <div className="flex flex-wrap items-end gap-3">
        <label className="field-label">
          Language
          <select className="input w-auto" value={language} onChange={(event) => setLanguage(event.target.value)}>
            <option value="">All languages</option>
            {languages.map((option) => (
              <option key={option.id} value={option.id}>{option.label}</option>
            ))}
          </select>
        </label>
        <label className="field-label">
          Split
          <select className="input w-auto" value={split} onChange={(event) => setSplit(event.target.value as DatasetSplit | "")}>
            <option value="">All splits</option>
            {SPLITS.map((option) => (
              <option key={option.id} value={option.id}>{option.label}</option>
            ))}
          </select>
        </label>
        <p className="ml-auto text-xs text-muted" aria-live="polite">{isLoading ? "Loading…" : `${total.toLocaleString()} matching clips`}</p>
      </div>

      {error && <p className="rounded-md bg-danger-soft p-2.5 text-xs text-danger" role="alert">{error}</p>}

      {!isLoading && clips.length === 0 && !error ? (
        <div className="card px-6 py-8 text-center">
          <p className="text-[13px] font-semibold text-heading">No dataset clips</p>
          <p className="mt-0.5 text-xs text-muted">
            {totalClips === 0 ? "Import clips with training/scripts/upload_to_mongodb.py." : "No clips match these filters."}
          </p>
        </div>
      ) : (
        <ul className="grid gap-2">
          {clips.map((clip) => (
            <DatasetClipItem key={clip.id} clip={clip} languageLabel={labelFor(languages, clip.language)} />
          ))}
        </ul>
      )}

      {clips.length < total && (
        <button type="button" className="btn-secondary justify-self-center" onClick={() => void load(clips.length)} disabled={isLoading}>
          {isLoading ? "Loading…" : "Load more"}
        </button>
      )}
    </div>
  );
}
