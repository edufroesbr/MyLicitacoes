"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { obterResumoProjeto } from "@/lib/api";
import type { ResumoProjeto } from "@/lib/types";

export default function ResumoProjetoPage({ params }: { params: Promise<{ id: string }> }) {
  const projetoId = Number(use(params).id);
  const [resumo, setResumo] = useState<ResumoProjeto | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    let cancelado = false;
    setCarregando(true);
    setErro(null);
    obterResumoProjeto(projetoId)
      .then((r) => {
        if (!cancelado) setResumo(r);
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
  }, [projetoId]);

  return (
    <main className="mx-auto max-w-2xl px-6 py-8">
      <Link
        href="/projetos"
        className="inline-flex items-center gap-1.5 text-sm text-primary-ink hover:underline"
      >
        <ArrowLeft aria-hidden className="h-3.5 w-3.5" strokeWidth={2} />
        Voltar a projetos
      </Link>

      {carregando && (
        <div className="mt-5 overflow-hidden rounded-lg border border-border bg-card p-5 shadow-card">
          <div className="h-4 w-1/2 animate-pulse rounded bg-muted" />
          <div className="mt-3 h-4 w-3/4 animate-pulse rounded bg-muted/70" />
        </div>
      )}

      {erro && (
        <div className="mt-5 rounded-lg border border-danger/30 bg-danger/5 p-4 text-sm text-danger">
          Erro ao carregar resumo: {erro}
        </div>
      )}

      {!carregando && !erro && resumo && (
        <div className="anim-rise mt-5 flex flex-col gap-5">
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-lg border border-border bg-card p-4 shadow-card">
              <div className="text-xs text-foreground-muted">Editais ativos</div>
              <div className="tnum text-2xl font-semibold text-foreground">{resumo.editais_ativos}</div>
            </div>
            <div className="rounded-lg border border-border bg-card p-4 shadow-card">
              <div className="text-xs text-foreground-muted">Editais encerrados</div>
              <div className="tnum text-2xl font-semibold text-foreground">{resumo.editais_encerrados}</div>
            </div>
            <div className="rounded-lg border border-border bg-card p-4 shadow-card">
              <div className="text-xs text-foreground-muted">Contratos celebrados</div>
              <div className="tnum text-2xl font-semibold text-foreground">{resumo.contratos_quantidade}</div>
            </div>
            <div className="rounded-lg border border-border bg-card p-4 shadow-card">
              <div className="text-xs text-foreground-muted">Valor médio por contrato</div>
              <div className="tnum text-2xl font-semibold text-foreground">
                {resumo.contratos_valor_medio ?? "—"}
              </div>
            </div>
          </div>

          <section>
            <h2 className="mb-2 text-sm font-semibold text-foreground">Contratos por UF</h2>
            {resumo.por_uf.length === 0 && (
              <p className="text-sm text-foreground-muted">Nenhum contrato celebrado ainda.</p>
            )}
            {resumo.por_uf.length > 0 && (
              <ul className="overflow-hidden rounded-lg border border-border bg-card shadow-card">
                {resumo.por_uf.map((u, i) => (
                  <li
                    key={i}
                    className="flex items-center justify-between gap-2 border-b border-border p-3 last:border-0"
                  >
                    <span className="text-sm text-foreground">{u.uf ?? "sem UF"}</span>
                    <span className="tnum text-sm text-foreground-muted">
                      {u.quantidade} contrato(s) · {u.valor_total}
                    </span>
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
