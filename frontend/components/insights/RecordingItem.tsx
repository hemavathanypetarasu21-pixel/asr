"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import MetricTile from "@/components/insights/MetricTile";
import { getApiErrorMessage } from "@/lib/api/client";
import { analyseRecording, deleteRecording, getRecordingAudio } from "@/lib/api/endpoints";
import type { Recording } from "@/lib/api/types";
import type { AppOptions } from "@/lib/api/useOptions";
import { formatDateTime, formatDuration, formatPercent, labelFor } from "@/lib/format";
import { routes } from "@/lib/routes";

const WHISPER_TRANSLATION_PREFIX = "whisper-";

export default function RecordingItem({
  recording,
  options,
  onChange,
  onDelete,
}: {
  recording: Recording;
  options: AppOptions | null;
  onChange: (recording: Recording) => void;
  onDelete: (id: string) => void;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [isAnalysing, setIsAnalysing] = useState(false);
  // null = use the recording's model if it is still offered, otherwise the first option.
  const [recognitionChoice, setRecognitionChoice] = useState<string | null>(null);
  const [translationChoice, setTranslationChoice] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const analysis = recording.analysis;
  const optionLists = {
    languages: options?.languages ?? [],
    modes: options?.modes ?? [],
    recognition: options?.models.recognition ?? [],
    translation: options?.models.translation ?? [],
  };
  const label = (key: keyof typeof optionLists, id: string | null | undefined) => labelFor(optionLists[key], id);
  const pick = (key: "recognition" | "translation", saved: string) =>
    optionLists[key].some((option) => option.id === saved) ? saved : (optionLists[key][0]?.id ?? saved);
  // Whisper fallback translations are stored as "whisper-<recognition model id>".
  const translationModelLabel = (id: string) =>
    id.startsWith(WHISPER_TRANSLATION_PREFIX)
      ? `${label("recognition", id.slice(WHISPER_TRANSLATION_PREFIX.length))} (translation)`
      : label("translation", id);
  const recognitionModel = recognitionChoice ?? pick("recognition", recording.recognition_model);
  const translationModel = translationChoice ?? pick("translation", recording.translation_model);

  // Audio is only fetched the first time the item is opened.
  useEffect(() => {
    if (!isOpen || audioUrl) return;
    let isCurrent = true;
    let createdUrl: string | null = null;
    getRecordingAudio(recording.id)
      .then((blob) => {
        if (!isCurrent) return;
        createdUrl = URL.createObjectURL(blob);
        setAudioUrl(createdUrl);
      })
      .catch((caught) => {
        if (isCurrent) setError(getApiErrorMessage(caught, "The audio could not be loaded."));
      });
    return () => {
      isCurrent = false;
    };
  }, [isOpen, audioUrl, recording.id]);

  useEffect(() => () => {
    if (audioUrl) URL.revokeObjectURL(audioUrl);
  }, [audioUrl]);

  async function analyse() {
    setError(null);
    setIsAnalysing(true);
    try {
      onChange(await analyseRecording(recording.id, { recognition_model: recognitionModel, translation_model: translationModel }));
    } catch (caught) {
      setError(getApiErrorMessage(caught, "Analysis failed. Please try again."));
    } finally {
      setIsAnalysing(false);
    }
  }

  async function remove() {
    setError(null);
    try {
      await deleteRecording(recording.id);
      onDelete(recording.id);
    } catch (caught) {
      setError(getApiErrorMessage(caught, "The recording could not be deleted."));
      setConfirmDelete(false);
    }
  }

  const matches = analysis?.detected_dialect ? analysis.detected_dialect === recording.language : null;
  const panelId = `recording-${recording.id}`;

  return (
    <li className="card overflow-hidden">
      <div className="flex items-center hover:bg-subtle">
        <h3 className="min-w-0 flex-1">
          <button
            type="button"
            onClick={() => setIsOpen(!isOpen)}
            aria-expanded={isOpen}
            aria-controls={panelId}
            className="flex w-full flex-wrap items-center gap-2.5 py-2.5 pl-3 pr-1 text-left"
          >
            <span className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${recording.source === "speak" ? "bg-brand-soft text-brand-ink" : "bg-accent-soft text-accent"}`} aria-hidden="true">
              <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d={recording.source === "speak" ? "M12 15a3 3 0 0 0 3-3V6a3 3 0 1 0-6 0v6a3 3 0 0 0 3 3Zm6-3a6 6 0 0 1-12 0m6 6v3" : "M12 16V4m0 0 4 4m-4-4L8 8M5 14v4a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-4"}
                />
              </svg>
            </span>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-[13px] font-semibold text-heading">{recording.file_name}</span>
              <span className="block text-[11px] text-muted">
                {formatDateTime(recording.created_at)} · {formatDuration(recording.duration)} · {label("languages", recording.language)} · {label("modes", recording.mode)}
              </span>
            </span>
            <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${analysis ? "bg-accent-soft text-accent" : "bg-subtle text-muted"}`}>
              {analysis ? "Analysed" : "Not analysed"}
            </span>
            <svg className={`h-4 w-4 text-muted transition-transform ${isOpen ? "rotate-180" : ""}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="m6 9 6 6 6-6" />
            </svg>
          </button>
        </h3>
        <div className="flex shrink-0 items-center gap-1 pr-2">
          {confirmDelete ? (
            <>
              <span className="text-[11px] text-danger">Remove?</span>
              <button type="button" className="btn min-h-7 bg-danger px-2 text-xs text-white hover:opacity-90" onClick={() => void remove()}>
                Yes
              </button>
              <button type="button" className="btn-secondary min-h-7 px-2 text-xs" onClick={() => setConfirmDelete(false)}>
                No
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={() => setConfirmDelete(true)}
              disabled={isAnalysing}
              aria-label={`Remove ${recording.file_name}`}
              title="Remove recording"
              className="rounded-md p-1.5 text-muted transition-colors hover:bg-danger-soft hover:text-danger disabled:opacity-40"
            >
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 7h16M10 11v6m4-6v6M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12M9 7V4h6v3" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {error && <p className="mx-3 mb-2 rounded-md bg-danger-soft p-2.5 text-xs text-danger" role="alert">{error}</p>}

      {isOpen && (
        <div id={panelId} className="grid gap-3 border-t border-line p-3">
          {audioUrl ? (
            <audio className="h-10 w-full" controls src={audioUrl} />
          ) : (
            <p className="text-xs text-muted" role="status">Loading audio…</p>
          )}

          {analysis ? (
            <>
              <div className="grid gap-2 sm:grid-cols-3">
                <MetricTile
                  label="Detected dialect"
                  value={analysis.detected_dialect ? label("languages", analysis.detected_dialect) : "Unclear"}
                  hint={matches === null ? undefined : matches ? "Matches the declared language" : `Declared: ${label("languages", recording.language)}`}
                  tone={matches === false ? "warn" : "default"}
                />
                <MetricTile label="Confidence" value={analysis.confidence == null ? "—" : formatPercent(analysis.confidence)} />
                <MetricTile label="Speaker mode" value={label("modes", recording.mode)} />
              </div>
              <div className="grid gap-2 md:grid-cols-2">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-muted">Transcript</p>
                  <p className="mt-1 rounded-md bg-subtle p-2.5 text-[13px] leading-6 text-ink">{analysis.transcript || "No speech recognised."}</p>
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-muted">English translation</p>
                  <p className="mt-1 rounded-md bg-brand-soft p-2.5 text-[13px] leading-6 text-ink">{analysis.translation || "—"}</p>
                  {analysis.translation_error && (
                    <p className="mt-1 text-[11px] leading-4 text-muted">
                      {analysis.translation_error}{" "}
                      <Link href={routes.settings} className="font-semibold text-brand hover:underline">Settings</Link>
                    </p>
                  )}
                </div>
              </div>
              <p className="text-xs text-muted">
                {label("recognition", analysis.recognition_model)} · {translationModelLabel(analysis.translation_model)} · analysed {formatDateTime(analysis.analysed_at)}
              </p>
            </>
          ) : (
            <p className="text-xs text-muted">
              Analyse to transcribe and detect the dialect, then translate to English with the models below.
            </p>
          )}


          <div className="flex flex-wrap items-center gap-2">
            <label className="flex items-center gap-1.5 text-xs text-muted">
              Recognition
              <select
                className="input w-auto"
                value={recognitionModel}
                disabled={isAnalysing || !options}
                onChange={(event) => setRecognitionChoice(event.target.value)}
              >
                {optionLists.recognition.map((option) => (
                  <option key={option.id} value={option.id}>{option.label}</option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-1.5 text-xs text-muted">
              Translation
              <select
                className="input w-auto"
                value={translationModel}
                disabled={isAnalysing || !options}
                onChange={(event) => setTranslationChoice(event.target.value)}
              >
                {optionLists.translation.map((option) => (
                  <option key={option.id} value={option.id}>{option.label}</option>
                ))}
              </select>
            </label>
            <button type="button" className="btn-primary" onClick={() => void analyse()} disabled={isAnalysing || !options}>
              {isAnalysing ? "Analysing…" : analysis ? "Analyse again" : "Analyse"}
            </button>
          </div>
        </div>
      )}
    </li>
  );
}
