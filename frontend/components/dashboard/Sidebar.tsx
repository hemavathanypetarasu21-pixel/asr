"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, type ReactNode } from "react";
import UserMenu, { type Profile } from "@/components/dashboard/UserMenu";
import { routes } from "@/lib/routes";

const menuItems = [
  { label: "Chat", href: routes.chat, icon: "M12 15a3 3 0 0 0 3-3V6a3 3 0 1 0-6 0v6a3 3 0 0 0 3 3Zm6-3a6 6 0 0 1-12 0m6 6v3" },
  { label: "Insights", href: routes.insights, icon: "M4 19V9m5 10V5m5 14v-7m5 7V3" },
] as const;

export default function Sidebar({ brand, profile }: { brand: ReactNode; profile: Profile }) {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        aria-label="Open menu"
        className="btn-secondary fixed left-2.5 top-2.5 z-30 px-2 md:hidden"
      >
        <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <path strokeLinecap="round" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
      {isOpen && (
        <div className="fixed inset-0 z-30 bg-black/30 md:hidden" onClick={() => setIsOpen(false)} aria-hidden="true" />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-56 shrink-0 flex-col border-r border-line bg-surface transition-transform md:static md:translate-x-0 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-12 items-center justify-between border-b border-line px-4">
          {brand}
          <button type="button" onClick={() => setIsOpen(false)} aria-label="Close menu" className="btn px-1.5 text-muted md:hidden">
            <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path strokeLinecap="round" d="M6 6l12 12M18 6 6 18" />
            </svg>
          </button>
        </div>

        <nav className="min-h-0 flex-1 overflow-y-auto p-2" aria-label="Dashboard">
          <ul className="space-y-0.5">
            {menuItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    onClick={() => setIsOpen(false)}
                    aria-current={isActive ? "page" : undefined}
                    className={`flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-[13px] font-medium transition-colors ${
                      isActive ? "bg-brand-soft text-brand-ink" : "text-muted hover:bg-subtle hover:text-heading"
                    }`}
                  >
                    <svg className="h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" d={item.icon} />
                    </svg>
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        <div className="border-t border-line p-2">
          <UserMenu profile={profile} onNavigate={() => setIsOpen(false)} />
        </div>
      </aside>
    </>
  );
}
