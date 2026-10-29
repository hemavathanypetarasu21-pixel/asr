import type { ReactNode } from "react";

export default function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <>
      <header className="sticky top-0 z-20 flex h-12 items-center justify-between gap-4 border-b border-line bg-surface/90 pl-14 pr-4 backdrop-blur md:px-6">
        <h1 className="truncate text-sm font-semibold text-heading">{title}</h1>
        {actions}
      </header>
      <div className="mx-auto w-full max-w-5xl px-4 pt-5 sm:px-6">
        <p className="eyebrow">{eyebrow}</p>
        {description && <p className="mt-1 max-w-2xl text-xs leading-5 text-muted">{description}</p>}
      </div>
    </>
  );
}
