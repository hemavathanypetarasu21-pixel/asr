"use client";

import { useEffect, useState } from "react";
import { getApiErrorMessage } from "@/lib/api/client";
import { getDatasetClipAudio } from "@/lib/api/endpoints";
import type { DatasetClip } from "@/lib/api/types";
import { formatDuration } from "@/lib/format";

export default function DatasetClipItem({ clip, languageLabel }: { clip: DatasetClip; languageLabel: string }) {
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [isLoadingAudio, setIsLoadingAudio] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isRomanised = clip.training_text !== clip.transcript;

  useEffect(() => () => {
    if (audioUrl) URL.revokeObjectURL(audioUrl);
  }, [audioUrl]);

  // Audio is fetched only when the user asks to play the clip.
  async function loadAudio() {
    setError(null);
    setIsLoadingAudio(true);
    try {
      setAudioUrl(URL.createObjectURL(await getDatasetClipAudio(clip.id)));
    } catch (caught) {
      setError(getApiErrorMessage(caught, "The audio could not be loaded."));
    } finally {
      setIsLoadingAudio(false);
    }
  }

  return (
    <li className="card grid gap-2 px-3 py-2.5">
      <div className="flex flex-wrap items-center gap-2">
        <span className="min-w-0 flex-1 truncate text-[13px] font-semibold text-heading">{clip.file_name}</span>
        <span className="rounded-full bg-brand-soft px-2 py-0.5 text-[11px] font-semibold text-brand-ink">{languageLabel}</span>
        <span className="rounded-full bg-subtle px-2 py-0.5 text-[11px] font-semibold capitalize text-muted">{clip.split}</span>
        <span className="text-[11px] text-muted">{formatDuration(clip.duration)}</span>
      </div>

      <p className="text-[13px] leading-6 text-ink">{clip.training_text}</p>
      {isRomanised && (
        <p className="text-[11px] leading-4 text-muted" lang="ta">Tamil script: {clip.transcript}</p>
      )}

      {audioUrl ? (
        <audio className="h-10 w-full" controls autoPlay src={audioUrl} />
      ) : (
        <button type="button" className="btn-secondary justify-self-start" onClick={() => void loadAudio()} disabled={isLoadingAudio}>
          {isLoadingAudio ? "Loading audio…" : "Play"}
        </button>
      )}
      {error && <p className="field-error">{error}</p>}

      <p className="text-[11px] text-muted">
        Speaker {clip.speaker_id} ·{" "}
        {clip.source_url ? (
          <a href={clip.source_url} target="_blank" rel="noreferrer" className="font-semibold text-brand hover:underline">{clip.source}</a>
        ) : (
          clip.source
        )}{" "}
        · {clip.licence}
        {clip.is_code_mixed && " · code-mixed (heuristic)"}
      </p>
    </li>
  );
}
