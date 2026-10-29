"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { useForm, useWatch } from "react-hook-form";
import { z } from "zod";
import Avatar from "@/components/dashboard/Avatar";
import type { Profile } from "@/components/dashboard/UserMenu";
import { getApiErrorMessage } from "@/lib/api/client";
import { deleteGeminiApiKey, saveGeminiApiKey, updatePreferences } from "@/lib/api/endpoints";
import { useSettings } from "@/lib/api/SettingsProvider";
import type { RecordingDefaults, Theme } from "@/lib/api/types";
import { useOptions } from "@/lib/api/useOptions";
import { routes } from "@/lib/routes";
import { createClient } from "@/lib/supabase/client";

const MIN_PASSWORD_LENGTH = 8;
const MAX_NAME_LENGTH = 60;

const themes: { value: Theme; label: string }[] = [
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
  { value: "system", label: "System" },
];

const profileSchema = z.object({
  displayName: z.string().trim().min(1, "Enter a name.").max(MAX_NAME_LENGTH, `Use at most ${MAX_NAME_LENGTH} characters.`),
});
const apiKeySchema = z.object({ apiKey: z.string().trim().min(1, "Paste your Gemini API key.") });
const passwordSchema = z
  .object({
    password: z.string().min(MIN_PASSWORD_LENGTH, `Use at least ${MIN_PASSWORD_LENGTH} characters.`),
    confirmPassword: z.string(),
  })
  .refine((values) => values.password === values.confirmPassword, { path: ["confirmPassword"], message: "Passwords do not match." });

type Notice = { tone: "ok" | "error"; text: string } | null;

function Section({ title, description, children }: { title: string; description: string; children: ReactNode }) {
  return (
    <section className="card grid gap-4 p-4 md:grid-cols-[13rem_1fr]">
      <div>
        <h2 className="text-[13px] font-semibold text-heading">{title}</h2>
        <p className="mt-0.5 text-xs leading-5 text-muted">{description}</p>
      </div>
      <div className="min-w-0">{children}</div>
    </section>
  );
}

function NoticeText({ notice }: { notice: Notice }) {
  if (!notice) return null;
  return (
    <p className={`mt-2 text-xs ${notice.tone === "ok" ? "text-accent" : "text-danger"}`} role={notice.tone === "ok" ? "status" : "alert"}>
      {notice.text}
    </p>
  );
}

export default function SettingsWorkspace({ profile }: { profile: Profile }) {
  const router = useRouter();
  const { settings, setSettings } = useSettings();
  const { options } = useOptions();
  const [notices, setNotices] = useState<Record<string, Notice>>({});
  const notify = (section: string, notice: Notice) => setNotices((current) => ({ ...current, [section]: notice }));

  const profileForm = useForm({ resolver: zodResolver(profileSchema), defaultValues: { displayName: profile.name === profile.email ? "" : profile.name } });
  const displayName = useWatch({ control: profileForm.control, name: "displayName" });
  const apiKeyForm = useForm({ resolver: zodResolver(apiKeySchema), defaultValues: { apiKey: "" } });
  const passwordForm = useForm({ resolver: zodResolver(passwordSchema), defaultValues: { password: "", confirmPassword: "" } });
  const defaultsForm = useForm<RecordingDefaults>({
    defaultValues: { language: null, mode: null, recognition_model: null, translation_model: null },
  });

  useEffect(() => {
    if (settings) defaultsForm.reset(settings.defaults);
  }, [settings, defaultsForm]);

  async function saveProfile({ displayName }: z.infer<typeof profileSchema>) {
    const supabase = createClient();
    const { error } = await supabase.auth.updateUser({ data: { display_name: displayName } });
    if (error) return notify("profile", { tone: "error", text: error.message });
    // Refresh so the new name is in the session token the server layout reads.
    await supabase.auth.refreshSession();
    router.refresh();
    notify("profile", { tone: "ok", text: "Profile updated." });
  }

  async function savePreferences(theme: Theme, defaults: RecordingDefaults, section: string) {
    try {
      setSettings(await updatePreferences({ theme, defaults }));
      notify(section, { tone: "ok", text: "Saved." });
    } catch (caught) {
      notify(section, { tone: "error", text: getApiErrorMessage(caught, "Could not save your preferences.") });
    }
  }

  async function saveApiKey({ apiKey }: z.infer<typeof apiKeySchema>) {
    try {
      setSettings(await saveGeminiApiKey(apiKey));
      apiKeyForm.reset();
      notify("apiKey", { tone: "ok", text: "API key verified and saved." });
    } catch (caught) {
      notify("apiKey", { tone: "error", text: getApiErrorMessage(caught, "Could not save the API key.") });
    }
  }

  async function removeApiKey() {
    try {
      setSettings(await deleteGeminiApiKey());
      notify("apiKey", { tone: "ok", text: "API key removed." });
    } catch (caught) {
      notify("apiKey", { tone: "error", text: getApiErrorMessage(caught, "Could not remove the API key.") });
    }
  }

  async function changePassword({ password }: z.infer<typeof passwordSchema>) {
    const { error } = await createClient().auth.updateUser({ password });
    if (error) return notify("password", { tone: "error", text: error.message });
    passwordForm.reset();
    notify("password", { tone: "ok", text: "Password updated." });
  }

  async function signOutEverywhere() {
    await createClient().auth.signOut({ scope: "global" });
    router.replace(routes.login);
    router.refresh();
  }

  const keyStatus = settings?.gemini_api_key;
  const defaultFields: { name: keyof RecordingDefaults; label: string; items: { id: string; label: string }[] }[] = [
    { name: "language", label: "Language", items: options?.languages ?? [] },
    { name: "mode", label: "Speaker mode", items: options?.modes ?? [] },
    { name: "recognition_model", label: "Dialect recognition model", items: options?.models.recognition ?? [] },
    { name: "translation_model", label: "Translation model", items: options?.models.translation ?? [] },
  ];

  return (
    <div className="mx-auto grid w-full max-w-4xl gap-3 px-4 py-5 sm:px-6">
      <Section title="Profile" description="Your name is shown in the sidebar.">
        <form className="grid gap-3" onSubmit={profileForm.handleSubmit(saveProfile)} noValidate>
          <div className="flex items-center gap-3">
            <Avatar name={displayName || profile.email} size="lg" />
            <div className="min-w-0 text-xs text-muted">
              <p className="truncate font-medium text-heading">{profile.email}</p>
              <p>Avatar uses your initials.</p>
            </div>
          </div>
          <label className="field-label max-w-sm">
            Display name
            <input className="input" autoComplete="name" {...profileForm.register("displayName")} />
            {profileForm.formState.errors.displayName && <span className="field-error">{profileForm.formState.errors.displayName.message}</span>}
          </label>
          <button type="submit" className="btn-primary justify-self-start" disabled={profileForm.formState.isSubmitting}>Save profile</button>
        </form>
        <NoticeText notice={notices.profile ?? null} />
      </Section>

      <Section title="Appearance" description="Light, dark, or follow your device.">
        <div className="flex flex-wrap gap-1.5" role="group" aria-label="Theme">
          {themes.map((theme) => (
            <button
              key={theme.value}
              type="button"
              className="choice"
              aria-pressed={settings?.theme === theme.value}
              disabled={!settings}
              onClick={() => settings && void savePreferences(theme.value, settings.defaults, "theme")}
            >
              {theme.label}
            </button>
          ))}
        </div>
        <NoticeText notice={notices.theme ?? null} />
      </Section>

      <Section title="Recording defaults" description="Pre-selected in Chat for every new recording.">
        <form
          className="grid gap-3 sm:grid-cols-2"
          onSubmit={defaultsForm.handleSubmit((defaults) => settings && savePreferences(settings.theme, defaults, "defaults"))}
        >
          {defaultFields.map((field) => (
            <label key={field.name} className="field-label">
              {field.label}
              <select
                className="input"
                disabled={!options || !settings}
                {...defaultsForm.register(field.name, { setValueAs: (value: string) => value || null })}
              >
                <option value="">First option</option>
                {field.items.map((item) => (
                  <option key={item.id} value={item.id}>{item.label}</option>
                ))}
              </select>
            </label>
          ))}
          <button type="submit" className="btn-primary justify-self-start sm:col-span-2" disabled={!settings || defaultsForm.formState.isSubmitting}>
            Save defaults
          </button>
        </form>
        <NoticeText notice={notices.defaults ?? null} />
      </Section>

      <Section title="API keys" description="Used to translate recordings. Stored encrypted and never shown again.">
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="font-semibold text-heading">Gemini</span>
          {!keyStatus ? (
            <span className="text-muted">Loading…</span>
          ) : keyStatus.source === "user" ? (
            <span className="rounded-full bg-accent-soft px-2 py-0.5 font-semibold text-accent">Saved · ending {keyStatus.hint}</span>
          ) : keyStatus.source === "server" ? (
            <span className="rounded-full bg-subtle px-2 py-0.5 font-semibold text-muted">Using the server key</span>
          ) : (
            <span className="rounded-full bg-danger-soft px-2 py-0.5 font-semibold text-danger">Not set: translation is disabled</span>
          )}
        </div>
        <form className="mt-3 flex flex-wrap items-start gap-2" onSubmit={apiKeyForm.handleSubmit(saveApiKey)} noValidate>
          <label className="grid min-w-0 flex-1 basis-60 gap-1">
            <span className="sr-only">Gemini API key</span>
            <input className="input font-mono" type="password" autoComplete="off" placeholder="Paste a Gemini API key" {...apiKeyForm.register("apiKey")} />
            {apiKeyForm.formState.errors.apiKey && <span className="field-error">{apiKeyForm.formState.errors.apiKey.message}</span>}
          </label>
          <button type="submit" className="btn-primary" disabled={apiKeyForm.formState.isSubmitting}>
            {apiKeyForm.formState.isSubmitting ? "Verifying…" : keyStatus?.source === "user" ? "Replace key" : "Save key"}
          </button>
          {keyStatus?.source === "user" && (
            <button type="button" className="btn-danger" onClick={() => void removeApiKey()}>Remove</button>
          )}
        </form>
        <p className="mt-2 text-xs text-muted">
          Get a key at <span className="font-mono">aistudio.google.com/apikey</span>. It is checked with Gemini before saving.
        </p>
        <NoticeText notice={notices.apiKey ?? null} />
      </Section>

      <Section title="Security" description="Change your password or sign out of every device.">
        <form className="grid max-w-md gap-3 sm:grid-cols-2" onSubmit={passwordForm.handleSubmit(changePassword)} noValidate>
          <label className="field-label">
            New password
            <input className="input" type="password" autoComplete="new-password" {...passwordForm.register("password")} />
            {passwordForm.formState.errors.password && <span className="field-error">{passwordForm.formState.errors.password.message}</span>}
          </label>
          <label className="field-label">
            Confirm password
            <input className="input" type="password" autoComplete="new-password" {...passwordForm.register("confirmPassword")} />
            {passwordForm.formState.errors.confirmPassword && <span className="field-error">{passwordForm.formState.errors.confirmPassword.message}</span>}
          </label>
          <button type="submit" className="btn-primary justify-self-start" disabled={passwordForm.formState.isSubmitting}>Update password</button>
        </form>
        <NoticeText notice={notices.password ?? null} />
        <div className="mt-4 border-t border-line pt-3">
          <button type="button" className="btn-secondary text-danger" onClick={() => void signOutEverywhere()}>Sign out of all devices</button>
        </div>
      </Section>
    </div>
  );
}
