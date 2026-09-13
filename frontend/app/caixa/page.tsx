"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listarEditais, type FiltrosEditais } from "@/lib/api";
import type { EditalResumo, Pagina } from "@/lib/types";
import { BadgePrazo, BadgeScore } from "@/components/Badge";
import Filtros from "@/components/Filtros";

const TAMANHO_PAGINA = 20;

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

  return (
    <main className="mx-auto max-w-4xl p-6">
      <h1 className="mb-4 text-xl font-semibold text-foreground">Caixa</h1>
      <Filtros filtros={filtros} onChange={setFiltros} />

      {carregando && <p className="text-foreground-muted">A carregar...</p>}
      {erro && <p className="text-danger">Erro ao carregar editais: {erro}</p>}
      {!carregando && !erro && pagina?.itens.length === 0 && (
        <p className="text-foreground-muted">Nenhum edital encontrado.</p>
      )}

      {!carregando && !erro && pagina && pagina.itens.length > 0 && (
        <ul className="divide-y divide-border rounded-lg border border-border bg-card">
          {pagina.itens.map((edital) => (
            <li key={edital.id}>
              <Link
                href={`/editais/${edital.id}`}
                className={`flex flex-col gap-1 p-4 hover:bg-muted ${
                  edital.status === "novo" ? "font-semibold text-foreground" : "text-foreground-muted"
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="truncate">{edital.objeto}</span>
                  <div className="flex shrink-0 gap-1">
                    <BadgeScore score={edital.score_relevancia} />
                    <BadgePrazo dataFim={edital.data_fim_propostas} />
                  </div>
                </div>
                <div className="text-sm">
                  {edital.orgao_nome} · {edital.uf ?? "—"} · {edital.modalidade ?? "—"} ·{" "}
                  {edital.valor_estimado ?? "—"} · {edital.data_publicacao ?? "—"}
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}

      {pagina && pagina.total > pagina.tamanho && (
        <div className="mt-4 flex items-center gap-3 text-sm text-foreground-muted">
          <button
            className="rounded border border-border px-2 py-1 disabled:opacity-50"
            disabled={paginaAtual <= 1}
            onClick={() => setFiltros((f) => ({ ...f, pagina: paginaAtual - 1 }))}
          >
            Anterior
          </button>
          <span>
            Pagina {paginaAtual} de {totalPaginas}
          </span>
          <button
            className="rounded border border-border px-2 py-1 disabled:opacity-50"
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
