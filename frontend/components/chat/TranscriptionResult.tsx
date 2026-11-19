"use client";

import { useEffect, useState } from "react";
import { getApiErrorMessage } from "@/lib/api/client";
import { saveTranscript } from "@/lib/api/endpoints";
import type { Recording } from "@/lib/api/types";
import { formatDuration } from "@/lib/format";

export type ResultStage = "saving" | "transcribing" | "done" | "error";

export type TranscriptionItem = {
  key: string;
  name: string;
  source: "speak" | "upload";
  language: string;
  stage: ResultStage;
  recording?: Recording;
  error?: string;
};

const STAGE_BADGE: Record<ResultStage, { label: string; className: string }> = {
  saving: { label: "Saving audio…", className: "bg-subtle text-muted" },
  transcribing: { label: "Transcribing…", className: "bg-brand-soft text-brand-ink" },
  done: { label: "Ready", className: "bg-accent-soft text-accent" },
  error: { label: "Failed", className: "bg-danger-soft text-danger" },
};

export default function TranscriptionResult({
  item,
  languageLabel,
  onRetry,
  onClear,
  onRecordingChange,
}: {
  item: TranscriptionItem;
  languageLabel: string;
  onRetry: () => void;
  onClear: () => void;
  onRecordingChange: (recording: Recording) => void;
}) {
  const recording = item.recording;
  const savedText = recording?.corrected_transcript ?? recording?.analysis?.transcript ?? "";
  const [draft, setDraft] = useState(savedText);
  const [isSaving, setIsSaving] = useState(false);
  const [notice, setNotice] = useState<{ tone: "ok" | "error"; text: string } | null>(null);
  const isProcessing = item.stage === "saving" || item.stage === "transcribing";
  const isEdited = draft.trim() !== savedText.trim();
  const badge = STAGE_BADGE[item.stage];

  // Load the transcript into the editor once the model has produced it.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (item.stage === "done") setDraft(savedText);
    // Only when a new result arrives, not after every save.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [item.stage, recording?.analysis?.analysed_at]);

  useEffect(() => {
    if (notice?.tone !== "ok") return;
    const timer = setTimeout(() => setNotice(null), 2500);
    return () => clearTimeout(timer);
  }, [notice]);

  async function copy() {
    try {
      await navigator.clipboard.writeText(draft);
      setNotice({ tone: "ok", text: "Copied to clipboard." });
    } catch {
      setNotice({ tone: "error", text: "Copy failed. Select the text and copy it manually." });
    }
  }

  async function save() {
    if (!recording) return;
    setIsSaving(true);
    setNotice(null);
    try {
      onRecordingChange(await saveTranscript(recording.id, draft));
      setNotice({ tone: "ok", text: "Transcript saved. It also appears in Insights." });
    } catch (caught) {
      setNotice({ tone: "error", text: getApiErrorMessage(caught, "The transcript could not be saved.") });
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <li className="grid gap-2.5 py-3 first:pt-0 last:pb-0">
      <div className="flex flex-wrap items-center gap-2">
        <div className="min-w-0 flex-1">
          <p className="truncate text-[13px] font-semibold text-heading">{recording?.file_name ?? item.name}</p>
          <p className="text-xs text-muted">
            Language: <span className="font-medium text-ink">{languageLabel}</span>
            {recording && <> · {formatDuration(recording.duration)}</>}
            {" · "}{item.source === "speak" ? "Microphone" : "Uploaded file"}
          </p>
        </div>
        <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${badge.className}`}>{badge.label}</span>
      </div>

      {isProcessing && (
        <div className="flex items-center gap-2.5 rounded-md bg-subtle p-3 text-xs text-muted" role="status">
          <span className="h-4 w-4 shrink-0 animate-spin rounded-full border-2 border-brand border-t-transparent" aria-hidden="true" />
          {item.stage === "saving"
            ? "Saving your audio…"
            : "Processing your audio and generating the transcription. This can take a little while for longer clips."}
        </div>
      )}

      {item.stage === "error" && (
        <div className="flex flex-wrap items-start justify-between gap-2 rounded-md bg-danger-soft p-2.5 text-xs text-danger" role="alert">
          <span>{item.error}</span>
          <div className="flex gap-3">
            <button type="button" className="font-semibold underline" onClick={onRetry}>Try again</button>
            <button type="button" className="font-semibold underline" onClick={onClear}>Dismiss</button>
          </div>
        </div>
      )}

      {item.stage === "done" && recording && (
        <>
          <label className="field-label">
            Transcription
            <textarea
              className="input min-h-24 resize-y leading-6"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="No speech was recognised. You can type the transcript here."
              lang={recording.language === "tanglish" ? "ta-Latn" : "ms"}
            />
          </label>
          {recording.analysis?.transcript_native && (
            <p className="text-[11px] leading-4 text-muted" lang="ta">Tamil script: {recording.analysis.transcript_native}</p>
          )}
          <p className="text-[11px] text-muted">
            {isEdited
              ? "You have unsaved changes."
              : recording.corrected_transcript
                ? "Your corrected transcript is saved."
                : "Correct any mistakes in the text, then save."}
          </p>
          <div className="flex flex-wrap gap-2">
            <button type="button" className="btn-primary" onClick={() => void save()} disabled={isSaving || !draft.trim()}>
              {isSaving ? "Saving…" : "Save transcript"}
            </button>
            <button type="button" className="btn-secondary" onClick={() => void copy()} disabled={!draft}>Copy</button>
            <button type="button" className="btn-secondary" onClick={() => setDraft(savedText)} disabled={!isEdited || isSaving}>Undo changes</button>
            <button type="button" className="btn-secondary ml-auto" onClick={onClear} title="Removes it from this panel; the recording stays in Insights">
              Clear
            </button>
          </div>
          {notice && (
            <p className={`text-xs ${notice.tone === "ok" ? "text-accent" : "text-danger"}`} role={notice.tone === "error" ? "alert" : "status"}>
              {notice.text}
            </p>
          )}
        </>
      )}
    </li>
  );
}
