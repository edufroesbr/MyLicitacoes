import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "MyLicitacoes",
  description: "Radar de editais",
};

const LINKS_NAV = [
  { href: "/caixa", rotulo: "Caixa" },
  { href: "/digest", rotulo: "Digest" },
  { href: "/projetos", rotulo: "Projetos" },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body>
        <nav className="border-b border-border bg-card px-6 py-3">
          <div className="mx-auto flex max-w-3xl gap-4">
            {LINKS_NAV.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="text-sm font-medium text-foreground-muted hover:text-primary-ink"
              >
                {link.rotulo}
              </Link>
            ))}
          </div>
        </nav>
        {children}
      </body>
    </html>
  );
}
