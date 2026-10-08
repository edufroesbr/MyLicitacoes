"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Inbox, Radar, Target } from "lucide-react";

const LINKS = [
  { href: "/caixa", rotulo: "Caixa", Icone: Inbox },
  { href: "/digest", rotulo: "Digest", Icone: Radar },
  { href: "/projetos", rotulo: "Projetos", Icone: Target },
];

export default function NavBar() {
  const path = usePathname() ?? "";
  return (
    <header className="sticky top-0 z-10 border-b border-border bg-card/85 backdrop-blur">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-y-1 px-4 py-3 sm:px-6">
        <Link href="/caixa" className="group flex items-center gap-2">
          <Radar aria-hidden className="h-5 w-5 shrink-0 text-primary" strokeWidth={1.75} />
          <span className="hidden font-display text-lg font-semibold tracking-tightest text-foreground sm:inline">
            MyLicitacoes
          </span>
        </Link>
        <nav className="flex gap-0.5 text-sm sm:gap-1">
          {LINKS.map((l) => {
            const ativo = path === l.href || (l.href !== "/caixa" && path.startsWith(l.href));
            return (
              <Link
                key={l.href}
                href={l.href}
                aria-current={ativo ? "page" : undefined}
                className={`flex items-center gap-1.5 rounded-md px-2 py-1.5 transition-colors sm:px-3 ${
                  ativo
                    ? "bg-muted font-medium text-primary-ink"
                    : "text-foreground-muted hover:bg-muted/60 hover:text-foreground"
                }`}
              >
                <l.Icone aria-hidden className="h-4 w-4" strokeWidth={1.75} />
                {l.rotulo}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
