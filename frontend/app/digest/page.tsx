"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { digestHoje } from "@/lib/api";
import type { Digest } from "@/lib/types";
import { BadgePrazo, BadgeScore } from "@/components/Badge";

function CartaoContador({ rotulo, valor }: { rotulo: string; valor: number }) {
  return (
    <div className="rounded-lg border border-border bg-card p-4 text-center">
      <div className="text-2xl font-semibold text-foreground">{valor}</div>
      <div className="text-sm text-foreground-muted">{rotulo}</div>
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
    <main className="mx-auto max-w-3xl p-6">
      <h1 className="mb-1 text-xl font-semibold text-foreground">Digest do dia</h1>

      {carregando && <p className="text-foreground-muted">A carregar...</p>}
      {erro && <p className="text-danger">Erro ao carregar digest: {erro}</p>}

      {!carregando && !erro && digest && (
        <div className="flex flex-col gap-4">
          <p className="text-sm text-foreground-muted">{digest.data_ref}</p>

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
            <p className="text-sm text-danger">
              Fontes com falha: {digest.resumo.fontes_com_falha.join(", ")}
            </p>
          )}

          <section>
            <h2 className="mb-2 text-sm font-semibold text-foreground">Destaques</h2>
            {digest.destaques.length === 0 && (
              <p className="text-sm text-foreground-muted">Sem destaques hoje.</p>
            )}
            <ul className="divide-y divide-border rounded-lg border border-border bg-card">
              {digest.destaques.map((edital) => (
                <li key={edital.id}>
                  <Link
                    href={`/editais/${edital.id}`}
                    className="flex items-center justify-between gap-2 p-4 hover:bg-muted"
                  >
                    <span className="truncate">{edital.objeto}</span>
                    <div className="flex shrink-0 gap-1">
                      <BadgeScore score={edital.score_relevancia} />
                      <BadgePrazo dataFim={edital.data_fim_propostas} />
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        </div>
      )}
    </main>
  );
}
