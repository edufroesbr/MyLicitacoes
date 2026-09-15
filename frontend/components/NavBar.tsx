"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/caixa", rotulo: "Caixa" },
  { href: "/digest", rotulo: "Digest" },
  { href: "/projetos", rotulo: "Projetos" },
];

export default function NavBar() {
  const path = usePathname() ?? "";
  return (
    <header className="sticky top-0 z-10 border-b border-border bg-card/85 backdrop-blur">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-3">
        <Link href="/caixa" className="group flex items-center gap-2">
          <span
            aria-hidden
            className="inline-block h-4 w-4 rounded-sm border border-accent/60 bg-accent/15"
          />
          <span className="font-display text-lg font-semibold tracking-tightest text-foreground">
            MyLicitacoes
          </span>
        </Link>
        <nav className="flex gap-1 text-sm">
          {LINKS.map((l) => {
            const ativo = path === l.href || (l.href !== "/caixa" && path.startsWith(l.href));
            return (
              <Link
                key={l.href}
                href={l.href}
                aria-current={ativo ? "page" : undefined}
                className={`rounded-md px-3 py-1.5 transition-colors ${
                  ativo
                    ? "bg-muted font-medium text-primary-ink"
                    : "text-foreground-muted hover:bg-muted/60 hover:text-foreground"
                }`}
              >
                {l.rotulo}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
