"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { obterEdital, urlArquivo } from "@/lib/api";
import type { EditalDetalhe, StatusCaixa } from "@/lib/types";
import { BadgePrazo, BadgeScore } from "@/components/Badge";
import AcoesStatus from "@/components/AcoesStatus";

export default function DetalheEditalPage({ params }: { params: { id: string } }) {
  const editalId = Number(params.id);
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
    <main className="mx-auto max-w-3xl p-6">
      <Link href="/caixa" className="text-sm text-primary-ink hover:underline">
        &larr; Voltar a caixa
      </Link>

      {carregando && <p className="mt-4 text-foreground-muted">A carregar...</p>}
      {erro && <p className="mt-4 text-danger">Erro ao carregar edital: {erro}</p>}

      {!carregando && !erro && edital && (
        <article className="mt-4 flex flex-col gap-4">
          <header className="flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <BadgeScore score={edital.score_relevancia} />
              <BadgePrazo dataFim={edital.data_fim_propostas} />
              <span className="rounded bg-muted px-2 py-0.5 text-xs font-medium text-foreground-muted">
                {edital.status}
              </span>
            </div>
            <h1 className="text-xl font-semibold text-foreground">{edital.objeto}</h1>
            <p className="text-sm text-foreground-muted">{edital.motivo_relevancia}</p>
          </header>

          <dl className="grid grid-cols-2 gap-x-4 gap-y-2 rounded-lg border border-border bg-card p-4 text-sm">
            <dt className="text-foreground-muted">Orgao</dt>
            <dd>{edital.orgao_nome}</dd>
            <dt className="text-foreground-muted">CNPJ</dt>
            <dd>{edital.orgao_cnpj}</dd>
            <dt className="text-foreground-muted">UF / Municipio</dt>
            <dd>{edital.uf ?? "—"} / {edital.municipio ?? "—"}</dd>
            <dt className="text-foreground-muted">Modalidade</dt>
            <dd>{edital.modalidade ?? "—"}</dd>
            <dt className="text-foreground-muted">Valor estimado</dt>
            <dd>{edital.valor_estimado ?? "—"}</dd>
            <dt className="text-foreground-muted">Publicacao</dt>
            <dd>{edital.data_publicacao ?? "—"}</dd>
            <dt className="text-foreground-muted">Fim das propostas</dt>
            <dd>{edital.data_fim_propostas ?? "—"}</dd>
            <dt className="text-foreground-muted">Fonte</dt>
            <dd>{edital.fonte}</dd>
          </dl>

          <a
            href={edital.url_origem}
            target="_blank"
            rel="noreferrer"
            className="text-sm text-primary-ink hover:underline"
          >
            Ver na fonte original &rarr;
          </a>

          <section>
            <h2 className="mb-2 text-sm font-semibold text-foreground">Arquivos</h2>
            {edital.arquivos.length === 0 && (
              <p className="text-sm text-foreground-muted">Nenhum arquivo capturado.</p>
            )}
            <ul className="flex flex-col gap-1">
              {edital.arquivos.map((arquivo) => (
                <li key={arquivo.id}>
                  <a
                    href={urlArquivo(edital.id, arquivo.id)}
                    target="_blank"
                    rel="noreferrer"
                    className="text-sm text-primary-ink hover:underline"
                  >
                    {arquivo.tipo} (arquivo #{arquivo.id})
                  </a>
                </li>
              ))}
            </ul>
          </section>

          <AcoesStatus editalId={edital.id} statusAtual={edital.status} onMudou={aoMudarStatus} />
        </article>
      )}
    </main>
  );
}
