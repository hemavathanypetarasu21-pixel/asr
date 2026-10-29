import Link from "next/link";
import { env } from "@/lib/env";

export default function BrandMark({ href }: { href: string }) {
  return (
    <Link href={href} className="flex items-center gap-2 text-sm font-bold text-heading" aria-label={`${env.appName} home`}>
      <span className="flex h-6 w-6 items-center justify-center rounded-md bg-brand text-white" aria-hidden="true">
        <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16M8 8v8m8-10v12M4 10v4m16-6v8" />
        </svg>
      </span>
      <span>{env.appName}</span>
    </Link>
  );
}
