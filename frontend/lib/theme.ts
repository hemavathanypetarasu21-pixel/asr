import type { Theme } from "@/lib/api/types";

/** localStorage copy of the saved theme, read before first paint to avoid a flash. */
export const THEME_STORAGE_KEY = "asr-theme";

export function applyTheme(theme: Theme) {
  document.documentElement.dataset.theme = theme;
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // Storage can be unavailable (private mode); the theme still applies for this page.
  }
}

/** Inline script for <head>: applies the cached theme before React hydrates. */
export const themeBootScript = `try{var t=localStorage.getItem("${THEME_STORAGE_KEY}");if(t==="light"||t==="dark"||t==="system")document.documentElement.dataset.theme=t}catch(e){}`;
