import type { Profile } from "@/components/dashboard/UserMenu";
import { createClient } from "./server";

/** Reads the signed-in user's display name and email from the session claims (server only). */
export async function getProfile(): Promise<Profile> {
  const supabase = await createClient();
  const { data } = await supabase.auth.getClaims();
  const claims = data?.claims;
  const email = typeof claims?.email === "string" ? claims.email : "";
  const displayName = claims?.user_metadata?.display_name;
  return { email, name: typeof displayName === "string" && displayName.trim() ? displayName : email };
}
