"use client";

import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { getSettings } from "./endpoints";
import type { UserSettings } from "./types";
import { applyTheme } from "@/lib/theme";

type SettingsContextValue = {
  settings: UserSettings | null;
  /** Replaces settings with a server response (after a save) and applies its theme. */
  setSettings: (settings: UserSettings) => void;
};

const SettingsContext = createContext<SettingsContextValue | null>(null);

/** Loads the signed-in user's settings once for the whole dashboard. */
export function SettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettingsState] = useState<UserSettings | null>(null);

  const setSettings = useCallback((next: UserSettings) => {
    setSettingsState(next);
    applyTheme(next.theme);
  }, []);

  useEffect(() => {
    getSettings()
      .then(setSettings)
      .catch(() => {
        // Settings are optional for the pages to work; failures surface on the settings page.
      });
  }, [setSettings]);

  return <SettingsContext.Provider value={{ settings, setSettings }}>{children}</SettingsContext.Provider>;
}

export function useSettings() {
  const value = useContext(SettingsContext);
  if (!value) throw new Error("useSettings must be used inside SettingsProvider.");
  return value;
}
