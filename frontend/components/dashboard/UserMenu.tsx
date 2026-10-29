"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import Avatar from "@/components/dashboard/Avatar";
import { routes } from "@/lib/routes";
import { createClient } from "@/lib/supabase/client";

export type Profile = { name: string; email: string };

export default function UserMenu({ profile, onNavigate }: { profile: Profile; onNavigate?: () => void }) {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  // Without a display name the name falls back to the email; avoid showing it twice.
  const hasDisplayName = profile.name !== profile.email;

  useEffect(() => {
    if (!isOpen) return;
    const close = (event: MouseEvent | KeyboardEvent) => {
      if (event instanceof KeyboardEvent ? event.key === "Escape" : !menuRef.current?.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", close);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", close);
    };
  }, [isOpen]);

  async function signOut() {
    await createClient().auth.signOut();
    router.replace(routes.login);
    router.refresh();
  }

  return (
    <div ref={menuRef} className="relative">
      {isOpen && (
        <div role="menu" className="card absolute bottom-full left-0 right-0 mb-2 overflow-hidden py-1 shadow-lg">
          <div className="border-b border-line px-3 py-2">
            <p className="truncate text-xs font-semibold text-heading">{profile.name}</p>
            {hasDisplayName && <p className="truncate text-xs text-muted">{profile.email}</p>}
          </div>
          <Link
            role="menuitem"
            href={routes.settings}
            onClick={() => {
              setIsOpen(false);
              onNavigate?.();
            }}
            className="block px-3 py-2 text-sm text-ink hover:bg-subtle"
          >
            Settings
          </Link>
          <button role="menuitem" type="button" onClick={() => void signOut()} className="block w-full px-3 py-2 text-left text-sm text-danger hover:bg-danger-soft">
            Log out
          </button>
        </div>
      )}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-haspopup="menu"
        aria-expanded={isOpen}
        className="flex w-full items-center gap-2.5 rounded-lg p-1.5 text-left hover:bg-subtle"
      >
        <Avatar name={profile.name} />
        <span className="min-w-0 flex-1">
          <span className="block truncate text-[13px] font-semibold text-heading">{profile.name}</span>
          {hasDisplayName && <span className="block truncate text-xs text-muted">{profile.email}</span>}
        </span>
        <svg className="h-4 w-4 text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" d="m7 15 5-5 5 5" />
        </svg>
      </button>
    </div>
  );
}
