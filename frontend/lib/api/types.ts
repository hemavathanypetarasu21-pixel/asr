export type Option = { id: string; label: string };

export type ModelOptions = {
  recognition: Option[];
  translation: Option[];
};

export type RecordingSource = "speak" | "upload";

/** Choices made on the chat page and stored with every recording. */
export type RecordingSettings = {
  language: string;
  recognition_model: string;
  translation_model: string;
};

export type RecordingAnalysis = {
  transcript: string;
  /** Original Tamil-script output when `transcript` was romanised. */
  transcript_native: string | null;
  detected_dialect: string | null;
  confidence: number | null;
  translation: string | null;
  /** Why translation was skipped (e.g. no API key); transcript and dialect are still valid. */
  translation_error: string | null;
  recognition_model: string;
  translation_model: string;
  analysed_at: string;
};

export type Recording = RecordingSettings & {
  id: string;
  source: RecordingSource;
  file_name: string;
  duration: number | null;
  created_at: string;
  analysis: RecordingAnalysis | null;
  /** The user's corrected transcript; the model's output stays in `analysis.transcript`. */
  corrected_transcript: string | null;
  corrected_at: string | null;
};

export type RecordingPage = {
  items: Recording[];
  total: number;
  analysed: number;
};

export type DatasetSplit = "train" | "validation" | "test";

/** A clip from an imported speech dataset (read-only, shared by all users). */
export type DatasetClip = {
  id: string;
  file_name: string;
  duration: number;
  language: string;
  /** Original transcript as published; Tamil is in Tamil script. */
  transcript: string;
  /** Romanised Tamil (Tanglish style); same as `transcript` for Malay-English. */
  training_text: string;
  is_code_mixed: boolean | null;
  speaker_id: string;
  split: DatasetSplit;
  source: string;
  source_url: string | null;
  licence: string;
};

export type DatasetPage = {
  items: DatasetClip[];
  /** Clips matching the filters. */
  total: number;
  /** Whole dataset, by language and split. */
  summary: { language: string; split: DatasetSplit; clips: number; hours: number }[];
};

export type Theme = "light" | "dark" | "system";

export type RecordingDefaults = {
  [Key in keyof RecordingSettings]: string | null;
};

export type ApiKeyStatus = {
  configured: boolean;
  source: "user" | "server" | null;
  hint: string | null;
};

export type UserSettings = {
  theme: Theme;
  defaults: RecordingDefaults;
  gemini_api_key: ApiKeyStatus;
};
