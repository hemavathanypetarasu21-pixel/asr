import { apiClient } from "./client";
import type {
  ModelOptions,
  Option,
  Recording,
  RecordingDefaults,
  RecordingPage,
  RecordingSettings,
  Theme,
  UserSettings,
} from "./types";

function recordingForm(file: File, settings: RecordingSettings) {
  const form = new FormData();
  form.append("file", file);
  Object.entries(settings).forEach(([key, value]) => form.append(key, value));
  return form;
}

export async function getLanguages() {
  const { data } = await apiClient.get<Option[]>("/languages");
  return data;
}

export async function getModes() {
  const { data } = await apiClient.get<Option[]>("/modes");
  return data;
}

export async function getModels() {
  const { data } = await apiClient.get<ModelOptions>("/models");
  return data;
}

export async function saveSpeech(file: File, settings: RecordingSettings) {
  const { data } = await apiClient.post<Recording>("/speak", recordingForm(file, settings));
  return data;
}

export async function uploadAudio(file: File, settings: RecordingSettings) {
  const { data } = await apiClient.post<Recording>("/upload", recordingForm(file, settings));
  return data;
}

export async function getRecordings(params: { skip: number; limit: number }) {
  const { data } = await apiClient.get<RecordingPage>("/recordings", { params });
  return data;
}

/** Audio is fetched with the auth header, so it is returned as a Blob for an object URL. */
export async function getRecordingAudio(id: string) {
  const { data } = await apiClient.get<Blob>(`/recordings/${encodeURIComponent(id)}/audio`, {
    responseType: "blob",
  });
  return data;
}

export async function deleteRecording(id: string) {
  await apiClient.delete(`/recordings/${encodeURIComponent(id)}`);
}

/** Model ids override the ones saved with the recording (needed when a saved model is retired). */
export async function analyseRecording(
  id: string,
  models: Pick<RecordingSettings, "recognition_model" | "translation_model">,
) {
  const { data } = await apiClient.post<Recording>(`/recordings/${encodeURIComponent(id)}/analyse`, models);
  return data;
}

export async function getSettings() {
  const { data } = await apiClient.get<UserSettings>("/settings");
  return data;
}

export async function updatePreferences(preferences: { theme: Theme; defaults: RecordingDefaults }) {
  const { data } = await apiClient.put<UserSettings>("/settings/preferences", preferences);
  return data;
}

export async function saveGeminiApiKey(apiKey: string) {
  const { data } = await apiClient.put<UserSettings>("/settings/api-keys/gemini", { api_key: apiKey });
  return data;
}

export async function deleteGeminiApiKey() {
  const { data } = await apiClient.delete<UserSettings>("/settings/api-keys/gemini");
  return data;
}
