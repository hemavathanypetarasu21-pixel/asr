export type Option = { id: string; label: string };

export type ModelOptions = {
  recognition: Option[];
  translation: Option[];
};

export type RecordingSource = "speak" | "upload";

/** Choices made on the chat page and stored with every recording. */
export type RecordingSettings = {
  language: string;
  mode: string;
  recognition_model: string;
  translation_model: string;
};

export type RecordingAnalysis = {
  transcript: string;
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
};

export type RecordingPage = {
  items: Recording[];
  total: number;
  analysed: number;
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
