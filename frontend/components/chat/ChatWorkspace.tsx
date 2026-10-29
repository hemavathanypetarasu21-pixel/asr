"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { getApiErrorMessage } from "@/lib/api/client";
import { saveSpeech, uploadAudio } from "@/lib/api/endpoints";
import { useSettings } from "@/lib/api/SettingsProvider";
import type { Recording, RecordingSettings } from "@/lib/api/types";
import { useOptions, type AppOptions } from "@/lib/api/useOptions";
import { useRecorder } from "@/lib/audio/useRecorder";
import { env } from "@/lib/env";
import { formatDuration, labelFor } from "@/lib/format";
import { routes } from "@/lib/routes";

const settingsSchema = z.object({
  language: z.string().min(1, "Choose a language."),
  mode: z.string().min(1, "Choose a speaker mode."),
  recognition_model: z.string().min(1, "Choose a dialect recognition model."),
  translation_model: z.string().min(1, "Choose a translation model."),
});

type SavedItem = { key: string; name: string; status: "saving" | "saved" | "error"; recording?: Recording; error?: string };

const fields: { name: keyof RecordingSettings; label: string; pick: (options: AppOptions) => { id: string; label: string }[] }[] = [
  { name: "language", label: "Language", pick: (options) => options.languages },
  { name: "mode", label: "Speaker mode", pick: (options) => options.modes },
  { name: "recognition_model", label: "Dialect recognition model", pick: (options) => options.models.recognition },
  { name: "translation_model", label: "Translation model", pick: (options) => options.models.translation },
];

export default function ChatWorkspace() {
  const { options, error: optionsError, retry: retryOptions } = useOptions();
  const { settings } = useSettings();
  const recorder = useRecorder();
  const [items, setItems] = useState<SavedItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  // Settings are captured when recording starts; the dropdowns are locked while recording.
  const recordingSettingsRef = useRef<RecordingSettings | null>(null);
  const form = useForm<RecordingSettings>({
    resolver: zodResolver(settingsSchema),
    defaultValues: { language: "", mode: "", recognition_model: "", translation_model: "" },
  });
  const { errors } = form.formState;

  // Pre-select the user's saved defaults, falling back to the first option of each dropdown.
  useEffect(() => {
    if (!options) return;
    const defaults = settings?.defaults;
    form.reset(
      Object.fromEntries(
        fields.map((field) => {
          const items = field.pick(options);
          const saved = defaults?.[field.name];
          return [field.name, items.some((item) => item.id === saved) ? saved : (items[0]?.id ?? "")];
        }),
      ) as RecordingSettings,
    );
  }, [options, settings, form]);

  async function validSettings() {
    if (await form.trigger()) return form.getValues();
    setError("Choose every option under Recording settings first.");
    return null;
  }

  async function save(file: File, source: "speak" | "upload", settings: RecordingSettings) {
    const key = crypto.randomUUID();
    setItems((current) => [{ key, name: file.name, status: "saving" }, ...current]);
    try {
      const recording = await (source === "speak" ? saveSpeech : uploadAudio)(file, settings);
      setItems((current) => current.map((item) => (item.key === key ? { ...item, status: "saved", recording } : item)));
    } catch (caught) {
      const message = getApiErrorMessage(caught, "The recording could not be saved.");
      setItems((current) => current.map((item) => (item.key === key ? { ...item, status: "error", error: message } : item)));
    }
  }

  async function toggleSpeak() {
    setError(null);
    if (recorder.isRecording) {
      const file = await recorder.stop();
      const settings = recordingSettingsRef.current;
      recordingSettingsRef.current = null;
      if (settings) await save(file, "speak", settings);
      return;
    }
    const settings = await validSettings();
    if (!settings) return;
    try {
      recordingSettingsRef.current = settings;
      await recorder.start();
    } catch (caught) {
      recordingSettingsRef.current = null;
      setError(caught instanceof Error ? caught.message : "Recording could not start.");
    }
  }

  async function handleUpload(file: File | undefined) {
    if (fileInputRef.current) fileInputRef.current.value = "";
    if (!file) return;
    setError(null);
    if (!file.type.startsWith("audio/")) return setError("Choose an audio file.");
    if (file.size > env.maxAudioUploadBytes) return setError(`Choose a file smaller than ${env.maxAudioUploadMb} MB.`);
    const settings = await validSettings();
    if (settings) await save(file, "upload", settings);
  }

  const ringScale = 1 + recorder.level * 0.6;

  return (
    <div className="mx-auto grid w-full max-w-5xl gap-3 px-4 py-4 sm:px-6 lg:grid-cols-[16rem_1fr]">
      <section className="card h-fit p-4" aria-labelledby="settings-heading">
        <h2 id="settings-heading" className="text-[13px] font-semibold text-heading">Recording settings</h2>
        <p className="mt-0.5 text-xs text-muted">Saved with every recording and used when you analyse it.</p>
        {optionsError && (
          <div className="mt-3 flex items-start justify-between gap-2 rounded-md bg-danger-soft p-2.5 text-xs text-danger" role="alert">
            <span>{optionsError}</span>
            <button type="button" className="shrink-0 font-semibold underline" onClick={retryOptions}>Retry</button>
          </div>
        )}
        <form className="mt-3 grid gap-3" onSubmit={(event) => event.preventDefault()}>
          {fields.map((field) => (
            <label key={field.name} className="field-label">
              {field.label}
              <select
                className="input"
                disabled={!options || recorder.isRecording}
                aria-invalid={Boolean(errors[field.name])}
                {...form.register(field.name)}
              >
                {!options && <option value="">Loading…</option>}
                {options && field.pick(options).map((option) => (
                  <option key={option.id} value={option.id}>{option.label}</option>
                ))}
              </select>
              {errors[field.name] && <span className="field-error">{errors[field.name]?.message}</span>}
            </label>
          ))}
        </form>
      </section>

      <div className="grid content-start gap-3">
        <section className="card flex flex-col items-center px-4 py-7 text-center" aria-labelledby="speak-heading">
          <h2 id="speak-heading" className="text-[15px] font-semibold text-heading">
            {recorder.isRecording ? "Listening…" : "Speak in Manglish or Tanglish"}
          </h2>
          <p className="mt-0.5 text-xs text-muted">
            {recorder.isRecording ? "Tap again to stop and save." : "Tap the microphone to start recording."}
          </p>

          <div className="relative mt-5 flex h-24 w-24 items-center justify-center">
            {recorder.isRecording && (
              <span
                className="absolute inset-0 rounded-full bg-brand/20 transition-transform duration-75"
                style={{ transform: `scale(${ringScale})` }}
                aria-hidden="true"
              />
            )}
            <button
              type="button"
              onClick={() => void toggleSpeak()}
              disabled={!options}
              aria-pressed={recorder.isRecording}
              aria-label={recorder.isRecording ? "Stop and save recording" : "Start speaking"}
              className={`relative flex h-[4.5rem] w-[4.5rem] items-center justify-center rounded-full text-white shadow-lg transition-colors focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-brand disabled:opacity-50 ${
                recorder.isRecording ? "bg-danger" : "bg-brand hover:bg-brand-hover"
              }`}
            >
              {recorder.isRecording ? (
                <span className="h-6 w-6 rounded bg-white" aria-hidden="true" />
              ) : (
                <svg className="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 15a3 3 0 0 0 3-3V6a3 3 0 1 0-6 0v6a3 3 0 0 0 3 3Zm6-3a6 6 0 0 1-12 0m6 6v3" />
                </svg>
              )}
            </button>
          </div>
          <p className="mt-3 font-mono text-xs text-muted" aria-live="polite">
            {recorder.isRecording ? formatDuration(recorder.elapsed) : "0:00"}
          </p>

          <div className="mt-5 flex w-full max-w-xs items-center gap-3 text-xs text-muted">
            <span className="h-px flex-1 bg-line" />or<span className="h-px flex-1 bg-line" />
          </div>
          <button
            type="button"
            className="btn-secondary mt-4"
            disabled={!options || recorder.isRecording}
            onClick={() => fileInputRef.current?.click()}
          >
            Upload audio file
          </button>
          <input ref={fileInputRef} type="file" accept="audio/*" className="hidden" onChange={(event) => void handleUpload(event.target.files?.[0])} />
          <p className="mt-1.5 text-[11px] text-muted">Up to {env.maxAudioUploadMb} MB</p>
          {error && <p className="mt-3 rounded-md bg-danger-soft p-2.5 text-xs text-danger" role="alert">{error}</p>}
        </section>

        <section className="card p-4" aria-labelledby="saved-heading">
          <div className="flex items-center justify-between">
            <h2 id="saved-heading" className="text-[13px] font-semibold text-heading">Saved this session</h2>
            <Link href={routes.insights} className="text-xs font-semibold text-brand hover:underline">Open insights →</Link>
          </div>
          {items.length === 0 ? (
            <p className="mt-2 text-xs text-muted">Recordings you save appear here. Analyse them on the insights page.</p>
          ) : (
            <ul className="mt-3 divide-y divide-line" aria-live="polite">
              {items.map((item) => (
                <li key={item.key} className="flex flex-wrap items-center justify-between gap-2 py-2">
                  <div className="min-w-0">
                    <p className="truncate text-[13px] font-medium text-heading">{item.recording?.file_name ?? item.name}</p>
                    {item.recording && options && (
                      <p className="text-xs text-muted">
                        {labelFor(options.languages, item.recording.language)} · {labelFor(options.modes, item.recording.mode)} · {formatDuration(item.recording.duration)}
                      </p>
                    )}
                    {item.error && <p className="field-error">{item.error}</p>}
                  </div>
                  <span
                    className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${
                      item.status === "saved" ? "bg-accent-soft text-accent" : item.status === "error" ? "bg-danger-soft text-danger" : "bg-subtle text-muted"
                    }`}
                  >
                    {item.status === "saved" ? "Saved" : item.status === "error" ? "Failed" : "Saving…"}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}
