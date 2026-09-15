"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { digestHoje } from "@/lib/api";
import type { Digest } from "@/lib/types";
import { BadgePrazo, BadgeScore } from "@/components/Badge";

function CartaoContador({ rotulo, valor }: { rotulo: string; valor: number }) {
  return (
    <div className="rounded-lg border border-border bg-card p-4 text-center shadow-card">
      <div className="tnum font-display text-2xl font-semibold text-foreground">{valor}</div>
      <div className="mt-1 text-sm text-foreground-muted">{rotulo}</div>
    </div>
  );
}

export default function DigestPage() {
  const [digest, setDigest] = useState<Digest | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    let cancelado = false;
    digestHoje()
      .then((d) => {
        if (!cancelado) setDigest(d);
      })
      .catch((e: unknown) => {
        if (!cancelado) setErro(e instanceof Error ? e.message : String(e));
      })
      .finally(() => {
        if (!cancelado) setCarregando(false);
      });
    return () => {
      cancelado = true;
    };
  }, []);

  return (
    <main className="mx-auto max-w-3xl px-6 py-8">
      <header className="mb-5">
        <h1 className="font-display text-3xl font-semibold tracking-tightest text-foreground">
          Digest do dia
        </h1>
        <p className="mt-1 text-sm text-foreground-muted">
          {digest && !carregando ? digest.data_ref : "Resumo diario de capturas"}
        </p>
      </header>

      {carregando && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="rounded-lg border border-border bg-card p-4 shadow-card">
              <div className="mx-auto h-7 w-10 animate-pulse rounded bg-muted" />
              <div className="mx-auto mt-2 h-3 w-16 animate-pulse rounded bg-muted/70" />
            </div>
          ))}
        </div>
      )}

      {erro && (
        <div className="rounded-lg border border-danger/30 bg-danger/5 p-4 text-sm text-danger">
          Erro ao carregar digest: {erro}
        </div>
      )}

      {!carregando && !erro && digest && (
        <div className="anim-rise flex flex-col gap-5">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <CartaoContador rotulo="Novos" valor={digest.resumo.novos ?? 0} />
            <CartaoContador rotulo="Relevantes" valor={digest.resumo.relevantes ?? 0} />
            <CartaoContador rotulo="Downloads" valor={digest.resumo.downloads ?? 0} />
            <CartaoContador
              rotulo="Fontes com falha"
              valor={digest.resumo.fontes_com_falha?.length ?? 0}
            />
          </div>

          {digest.resumo.fontes_com_falha && digest.resumo.fontes_com_falha.length > 0 && (
            <div className="rounded-lg border border-danger/30 bg-danger/5 p-3 text-sm text-danger">
              Fontes com falha: {digest.resumo.fontes_com_falha.join(", ")}
            </div>
          )}

          <section>
            <h2 className="mb-2 text-sm font-semibold text-foreground">Destaques</h2>
            {digest.destaques.length === 0 && (
              <p className="text-sm text-foreground-muted">Sem destaques hoje.</p>
            )}
            {digest.destaques.length > 0 && (
              <ul className="overflow-hidden rounded-lg border border-border bg-card shadow-card">
                {digest.destaques.map((edital) => (
                  <li key={edital.id} className="border-b border-border last:border-0">
                    <Link
                      href={`/editais/${edital.id}`}
                      className="flex items-center justify-between gap-2 p-4 transition-colors hover:bg-muted/50"
                    >
                      <span className="truncate text-foreground">{edital.objeto}</span>
                      <div className="flex shrink-0 items-center gap-1.5">
                        <BadgeScore score={edital.score_relevancia} />
                        <BadgePrazo dataFim={edital.data_fim_propostas} />
                      </div>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      )}
    </main>
  );
}
