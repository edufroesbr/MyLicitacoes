"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listarEditais, type FiltrosEditais } from "@/lib/api";
import type { EditalResumo, Pagina } from "@/lib/types";
import { BadgePrazo, BadgeScore } from "@/components/Badge";
import Filtros from "@/components/Filtros";

const TAMANHO_PAGINA = 20;

function temFiltro(f: FiltrosEditais): boolean {
  return Boolean(f.q || f.uf || f.modalidade || f.fonte || f.status || f.score_min);
}

export default function CaixaPage() {
  const [filtros, setFiltros] = useState<FiltrosEditais>({ pagina: 1, tamanho: TAMANHO_PAGINA });
  const [pagina, setPagina] = useState<Pagina<EditalResumo> | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    let cancelado = false;
    setCarregando(true);
    setErro(null);
    listarEditais(filtros)
      .then((p) => {
        if (!cancelado) setPagina(p);
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
  }, [filtros]);

  const paginaAtual = filtros.pagina ?? 1;
  const totalPaginas = pagina ? Math.max(1, Math.ceil(pagina.total / pagina.tamanho)) : 1;
  const vazio = !carregando && !erro && pagina?.itens.length === 0;

  return (
    <main className="mx-auto max-w-5xl px-6 py-8">
      <header className="mb-5">
        <h1 className="font-display text-3xl font-semibold tracking-tightest text-foreground">
          Caixa
        </h1>
        <p className="mt-1 text-sm text-foreground-muted">
          {pagina && !carregando ? (
            <>
              <span className="tnum font-medium text-foreground">{pagina.total}</span>{" "}
              {pagina.total === 1 ? "edital" : "editais"} no radar
            </>
          ) : (
            "Radar de editais tipo-LexFlow"
          )}
        </p>
      </header>

      <Filtros filtros={filtros} onChange={setFiltros} />

      {carregando && (
        <ul className="overflow-hidden rounded-lg border border-border bg-card shadow-card">
          {[0, 1, 2].map((i) => (
            <li key={i} className="flex items-center gap-3 border-b border-border p-4 last:border-0">
              <div className="h-2 w-2 shrink-0 rounded-full bg-muted" />
              <div className="flex-1">
                <div className="h-4 w-2/3 animate-pulse rounded bg-muted" />
                <div className="mt-2 h-3 w-1/3 animate-pulse rounded bg-muted/70" />
              </div>
              <div className="h-5 w-12 animate-pulse rounded-full bg-muted" />
            </li>
          ))}
        </ul>
      )}

      {erro && (
        <div className="rounded-lg border border-danger/30 bg-danger/5 p-4 text-sm text-danger">
          Nao foi possivel carregar os editais: {erro}
        </div>
      )}

      {vazio && (
        <div className="rounded-lg border border-dashed border-border bg-card/50 px-6 py-16 text-center">
          <svg
            aria-hidden
            viewBox="0 0 24 24"
            className="mx-auto h-8 w-8 text-foreground-muted/60"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M4 5h16v14H4z" />
            <path d="M4 9h16M9 5v14" />
          </svg>
          <p className="mt-3 font-display text-lg text-foreground">
            {temFiltro(filtros) ? "Nada corresponde a estes filtros" : "A caixa esta vazia"}
          </p>
          <p className="mt-1 text-sm text-foreground-muted">
            {temFiltro(filtros)
              ? "Ajuste os filtros ou limpe a busca."
              : "A proxima captura diaria preenche a caixa com editais do PNCP e Compras.gov."}
          </p>
        </div>
      )}

      {!carregando && !erro && pagina && pagina.itens.length > 0 && (
        <ul className="anim-rise overflow-hidden rounded-lg border border-border bg-card shadow-card">
          {pagina.itens.map((edital) => {
            const novo = edital.status === "novo";
            return (
              <li key={edital.id} className="border-b border-border last:border-0">
                <Link
                  href={`/editais/${edital.id}`}
                  className="flex items-start gap-3 p-4 transition-colors hover:bg-muted/50"
                >
                  <span
                    aria-hidden
                    className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${
                      novo ? "bg-primary" : "bg-transparent"
                    }`}
                  />
                  <div className="min-w-0 flex-1">
                    <p
                      className={`truncate ${
                        novo ? "font-semibold text-foreground" : "font-medium text-foreground/90"
                      }`}
                    >
                      {edital.objeto}
                    </p>
                    <p className="mt-1 truncate text-sm text-foreground-muted">
                      {edital.orgao_nome}
                      <span className="text-foreground-muted/50"> · </span>
                      {edital.uf ?? "—"}
                      <span className="text-foreground-muted/50"> · </span>
                      {edital.modalidade ?? "—"}
                      {edital.valor_estimado && (
                        <>
                          <span className="text-foreground-muted/50"> · </span>
                          <span className="tnum">R$ {edital.valor_estimado}</span>
                        </>
                      )}
                      {edital.data_publicacao && (
                        <>
                          <span className="text-foreground-muted/50"> · </span>
                          <span className="tnum">{edital.data_publicacao}</span>
                        </>
                      )}
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-1.5">
                    <BadgePrazo dataFim={edital.data_fim_propostas} />
                    <BadgeScore score={edital.score_relevancia} />
                  </div>
                </Link>
              </li>
            );
          })}
        </ul>
      )}

      {pagina && pagina.total > pagina.tamanho && (
        <div className="mt-5 flex items-center justify-between text-sm text-foreground-muted">
          <button
            className="rounded-md border border-border bg-card px-3 py-1.5 transition-colors hover:bg-muted disabled:opacity-40"
            disabled={paginaAtual <= 1}
            onClick={() => setFiltros((f) => ({ ...f, pagina: paginaAtual - 1 }))}
          >
            Anterior
          </button>
          <span className="tnum">
            Pagina {paginaAtual} de {totalPaginas}
          </span>
          <button
            className="rounded-md border border-border bg-card px-3 py-1.5 transition-colors hover:bg-muted disabled:opacity-40"
            disabled={paginaAtual >= totalPaginas}
            onClick={() => setFiltros((f) => ({ ...f, pagina: paginaAtual + 1 }))}
          >
            Proxima
          </button>
        </div>
      )}
    </main>
  );
}
