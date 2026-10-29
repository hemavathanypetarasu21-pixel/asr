"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import RecordingItem from "@/components/insights/RecordingItem";
import { getApiErrorMessage } from "@/lib/api/client";
import { getRecordings } from "@/lib/api/endpoints";
import type { Recording } from "@/lib/api/types";
import { useOptions } from "@/lib/api/useOptions";
import { routes } from "@/lib/routes";

const PAGE_SIZE = 20;

export default function InsightsWorkspace() {
  const { options } = useOptions();
  const [recordings, setRecordings] = useState<Recording[]>([]);
  const [total, setTotal] = useState(0);
  const [analysed, setAnalysed] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (skip: number) => {
    setIsLoading(true);
    setError(null);
    try {
      const page = await getRecordings({ skip, limit: PAGE_SIZE });
      setRecordings((current) => (skip === 0 ? page.items : [...current, ...page.items]));
      setTotal(page.total);
      setAnalysed(page.analysed);
    } catch (caught) {
      setError(getApiErrorMessage(caught, "Recordings could not be loaded."));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // Initial fetch on mount.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load(0);
  }, [load]);

  return (
    <div className="mx-auto grid w-full max-w-5xl gap-3 px-4 py-4 sm:px-6">
      <section className="grid gap-3 sm:grid-cols-3" aria-label="Summary">
        {[
          { label: "Recordings", value: total },
          { label: "Analysed", value: analysed },
          { label: "Waiting for analysis", value: total - analysed },
        ].map((stat) => (
          <div key={stat.label} className="card px-3 py-2.5">
            <p className="text-[11px] font-semibold text-muted">{stat.label}</p>
            <p className="text-lg font-bold text-heading">{stat.value}</p>
          </div>
        ))}
      </section>

      <div className="flex items-center justify-between">
        <h2 className="text-[13px] font-semibold text-heading">Recordings</h2>
        <button type="button" className="btn-secondary" onClick={() => void load(0)} disabled={isLoading}>Refresh</button>
      </div>

      {error && <p className="rounded-md bg-danger-soft p-2.5 text-xs text-danger" role="alert">{error}</p>}

      {isLoading && recordings.length === 0 ? (
        <p className="card py-8 text-center text-xs text-muted" role="status">Loading recordings…</p>
      ) : recordings.length === 0 && !error ? (
        <div className="card px-6 py-8 text-center">
          <p className="text-[13px] font-semibold text-heading">No recordings yet</p>
          <p className="mt-0.5 text-xs text-muted">Speak or upload audio in Chat, then analyse it here.</p>
          <Link href={routes.chat} className="btn-primary mt-3">Go to chat</Link>
        </div>
      ) : (
        <ul className="grid gap-2">
          {recordings.map((recording) => (
            <RecordingItem
              key={recording.id}
              recording={recording}
              options={options}
              onChange={(updated) => {
                if (!recording.analysis) setAnalysed((current) => current + 1);
                setRecordings((current) => current.map((item) => (item.id === updated.id ? updated : item)));
              }}
              onDelete={(id) => {
                if (recording.analysis) setAnalysed((current) => current - 1);
                setRecordings((current) => current.filter((item) => item.id !== id));
                setTotal((current) => current - 1);
              }}
            />
          ))}
        </ul>
      )}

      {recordings.length < total && (
        <button type="button" className="btn-secondary justify-self-center" onClick={() => void load(recordings.length)} disabled={isLoading}>
          {isLoading ? "Loading…" : "Load more"}
        </button>
      )}
    </div>
  );
}
