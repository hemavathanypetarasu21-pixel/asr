import BrandMark from "@/components/BrandMark";
import Sidebar from "@/components/dashboard/Sidebar";
import { SettingsProvider } from "@/lib/api/SettingsProvider";
import { routes } from "@/lib/routes";
import { getProfile } from "@/lib/supabase/profile";

export default async function DashboardLayout({ children }: LayoutProps<"/dashboard">) {
  return (
    <SettingsProvider>
      <div className="flex h-screen overflow-hidden bg-canvas">
        <Sidebar brand={<BrandMark href={routes.chat} />} profile={await getProfile()} />
        <div className="min-h-0 min-w-0 flex-1 overflow-y-auto">{children}</div>
      </div>
    </SettingsProvider>
  );
}
