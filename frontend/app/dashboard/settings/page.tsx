import PageHeader from "@/components/dashboard/PageHeader";
import SettingsWorkspace from "@/components/settings/SettingsWorkspace";
import { getProfile } from "@/lib/supabase/profile";

export default async function SettingsPage() {
  return (
    <>
      <PageHeader title="Settings" eyebrow="Account" description="Profile, appearance, recording defaults, API keys and security." />
      <SettingsWorkspace profile={await getProfile()} />
    </>
  );
}
