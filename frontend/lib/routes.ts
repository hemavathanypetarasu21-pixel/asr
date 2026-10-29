export const routes = {
  home: "/",
  login: "/auth/login",
  signup: "/auth/signup",
  chat: "/dashboard",
  insights: "/dashboard/insights",
  settings: "/dashboard/settings",
} as const;

export const protectedPrefix = "/dashboard";
export const authPrefix = "/auth";

/** Only allow same-origin relative paths as post-login redirects. */
export function safeRedirectPath(value: string | null | undefined): string {
  return value && value.startsWith("/") && !value.startsWith("//") ? value : routes.chat;
}
