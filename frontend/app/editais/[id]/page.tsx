"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { obterEdital, urlArquivo } from "@/lib/api";
import type { EditalDetalhe, StatusCaixa } from "@/lib/types";
import { BadgePrazo, BadgeScore } from "@/components/Badge";
import AcoesStatus from "@/components/AcoesStatus";

export default function DetalheEditalPage({ params }: { params: Promise<{ id: string }> }) {
  const editalId = Number(use(params).id);
  const [edital, setEdital] = useState<EditalDetalhe | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    let cancelado = false;
    setCarregando(true);
    setErro(null);
    obterEdital(editalId)
      .then((e) => {
        if (!cancelado) setEdital(e);
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
  }, [editalId]);

  function aoMudarStatus(novo: StatusCaixa) {
    setEdital((atual) => (atual ? { ...atual, status: novo } : atual));
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-8">
      <Link
        href="/caixa"
        className="inline-flex items-center gap-1.5 text-sm text-primary-ink hover:underline"
      >
        <svg
          aria-hidden
          viewBox="0 0 24 24"
          className="h-3.5 w-3.5"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M19 12H5M12 19l-7-7 7-7" />
        </svg>
        Voltar a caixa
      </Link>

      {carregando && (
        <div className="mt-5 overflow-hidden rounded-lg border border-border bg-card p-5 shadow-card">
          <div className="h-3 w-24 animate-pulse rounded bg-muted" />
          <div className="mt-3 h-6 w-3/4 animate-pulse rounded bg-muted" />
          <div className="mt-2 h-4 w-1/2 animate-pulse rounded bg-muted/70" />
        </div>
      )}

      {erro && (
        <div className="mt-5 rounded-lg border border-danger/30 bg-danger/5 p-4 text-sm text-danger">
          Erro ao carregar edital: {erro}
        </div>
      )}

      {!carregando && !erro && edital && (
        <article className="anim-rise mt-5 flex flex-col gap-5">
          <header className="flex flex-col gap-2">
            <div className="flex flex-wrap items-center gap-1.5">
              <BadgeScore score={edital.score_relevancia} />
              <BadgePrazo dataFim={edital.data_fim_propostas} />
              <span
                data-testid="status-atual"
                className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-foreground-muted"
              >
                {edital.status}
              </span>
            </div>
            <h1 className="font-display text-3xl font-semibold tracking-tightest text-foreground">
              {edital.objeto}
            </h1>
            <p className="text-sm text-foreground-muted">{edital.motivo_relevancia}</p>
          </header>

          <dl className="grid grid-cols-2 gap-x-6 gap-y-3 rounded-lg border border-border bg-card p-5 text-sm shadow-card">
            <dt className="text-foreground-muted">Orgao</dt>
            <dd className="text-foreground">{edital.orgao_nome}</dd>
            <dt className="text-foreground-muted">CNPJ</dt>
            <dd className="tnum text-foreground">{edital.orgao_cnpj}</dd>
            <dt className="text-foreground-muted">UF / Municipio</dt>
            <dd className="text-foreground">
              {edital.uf ?? "—"} / {edital.municipio ?? "—"}
            </dd>
            <dt className="text-foreground-muted">Modalidade</dt>
            <dd className="text-foreground">{edital.modalidade ?? "—"}</dd>
            <dt className="text-foreground-muted">Valor estimado</dt>
            <dd className="tnum text-foreground">{edital.valor_estimado ?? "—"}</dd>
            <dt className="text-foreground-muted">Publicacao</dt>
            <dd className="tnum text-foreground">{edital.data_publicacao ?? "—"}</dd>
            <dt className="text-foreground-muted">Fim das propostas</dt>
            <dd className="tnum text-foreground">{edital.data_fim_propostas ?? "—"}</dd>
            <dt className="text-foreground-muted">Fonte</dt>
            <dd className="text-foreground">{edital.fonte}</dd>
          </dl>

          <a
            href={edital.url_origem}
            target="_blank"
            rel="noreferrer"
            className="inline-flex w-fit items-center gap-1.5 text-sm text-primary-ink hover:underline"
          >
            Ver na fonte original
            <svg
              aria-hidden
              viewBox="0 0 24 24"
              className="h-3.5 w-3.5"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </a>

          <section>
            <h2 className="mb-2 text-sm font-semibold text-foreground">Arquivos</h2>
            {edital.arquivos.length === 0 && (
              <p className="text-sm text-foreground-muted">Nenhum arquivo capturado.</p>
            )}
            {edital.arquivos.length > 0 && (
              <ul className="overflow-hidden rounded-lg border border-border bg-card shadow-card">
                {edital.arquivos.map((arquivo) => (
                  <li key={arquivo.id} className="border-b border-border last:border-0">
                    <a
                      href={urlArquivo(edital.id, arquivo.id)}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center gap-2 p-3 text-sm text-primary-ink transition-colors hover:bg-muted/50"
                    >
                      <svg
                        aria-hidden
                        viewBox="0 0 24 24"
                        className="h-4 w-4 shrink-0 text-foreground-muted"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <path d="M14 3v5h5M6 3h8l5 5v13H6z" />
                      </svg>
                      {arquivo.tipo} (arquivo #{arquivo.id})
                    </a>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <AcoesStatus editalId={edital.id} statusAtual={edital.status} onMudou={aoMudarStatus} />
        </article>
      )}
    </main>
  );
}
