"use client";

import { useEffect, useState } from "react";
import { apagarProjeto, atualizarProjeto, criarProjeto, listarProjetos } from "@/lib/api";
import type { Projeto } from "@/lib/types";
import ProjetoForm, { type DadosProjetoForm } from "@/components/ProjetoForm";

export default function ProjetosPage() {
  const [projetos, setProjetos] = useState<Projeto[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [editando, setEditando] = useState<Projeto | null>(null);
  const [criando, setCriando] = useState(false);
  const [salvando, setSalvando] = useState(false);

  function carregar() {
    setCarregando(true);
    setErro(null);
    listarProjetos()
      .then(setProjetos)
      .catch((e: unknown) => setErro(e instanceof Error ? e.message : String(e)))
      .finally(() => setCarregando(false));
  }

  useEffect(carregar, []);

  async function salvar(dados: DadosProjetoForm) {
    setSalvando(true);
    setErro(null);
    try {
      if (editando) {
        await atualizarProjeto(editando.id, dados);
      } else {
        await criarProjeto(dados);
      }
      setEditando(null);
      setCriando(false);
      carregar();
    } catch (e: unknown) {
      setErro(e instanceof Error ? e.message : String(e));
    } finally {
      setSalvando(false);
    }
  }

  async function apagar(id: number) {
    setErro(null);
    try {
      await apagarProjeto(id);
      carregar();
    } catch (e: unknown) {
      setErro(e instanceof Error ? e.message : String(e));
    }
  }

  const formAberto = criando || editando !== null;

  return (
    <main className="mx-auto max-w-2xl px-6 py-8">
      <header className="mb-5">
        <h1 className="font-display text-3xl font-semibold tracking-tightest text-foreground">
          Projetos de interesse
        </h1>
        <p className="mt-1 text-sm text-foreground-muted">
          Palavras-chave e filtros salvos para vigiar a caixa.
        </p>
      </header>

      {erro && (
        <div className="mb-4 rounded-lg border border-danger/30 bg-danger/5 p-4 text-sm text-danger">
          Erro: {erro}
        </div>
      )}

      {!formAberto && (
        <button
          className="mb-5 rounded-md bg-primary px-4 py-1.5 text-sm font-medium text-primary-foreground shadow-sm transition-colors hover:bg-primary-hover"
          onClick={() => setCriando(true)}
        >
          Novo projeto
        </button>
      )}

      {formAberto && (
        <div className="mb-5">
          <ProjetoForm
            projeto={editando ?? undefined}
            salvando={salvando}
            onSalvar={salvar}
            onCancelar={() => {
              setEditando(null);
              setCriando(false);
            }}
          />
        </div>
      )}

      {carregando && (
        <ul className="overflow-hidden rounded-lg border border-border bg-card shadow-card">
          {[0, 1].map((i) => (
            <li
              key={i}
              className="flex items-center justify-between gap-2 border-b border-border p-4 last:border-0"
            >
              <div className="flex-1">
                <div className="h-4 w-1/3 animate-pulse rounded bg-muted" />
                <div className="mt-2 h-3 w-2/3 animate-pulse rounded bg-muted/70" />
              </div>
            </li>
          ))}
        </ul>
      )}

      {!carregando && projetos.length === 0 && (
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
            <path d="M4 6a2 2 0 0 1 2-2h4l2 2h6a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z" />
          </svg>
          <p className="mt-3 font-display text-lg text-foreground">Nenhum projeto criado</p>
          <p className="mt-1 text-sm text-foreground-muted">
            Crie um projeto para vigiar palavras-chave e filtros na caixa.
          </p>
        </div>
      )}

      {!carregando && projetos.length > 0 && (
        <ul className="overflow-hidden rounded-lg border border-border bg-card shadow-card">
          {projetos.map((p) => (
            <li
              key={p.id}
              className="flex items-center justify-between gap-2 border-b border-border p-4 last:border-0"
            >
              <div className="min-w-0">
                <div className="truncate font-medium text-foreground">
                  {p.nome}
                  {!p.ativo && <span className="ml-2 text-xs text-foreground-muted">(inativo)</span>}
                </div>
                <div className="truncate text-sm text-foreground-muted">
                  {p.palavras_chave.length > 0 ? p.palavras_chave.join(", ") : "sem palavras-chave"}
                </div>
              </div>
              <div className="flex shrink-0 gap-2">
                <button
                  className="rounded-md border border-border bg-card px-3 py-1.5 text-sm transition-colors hover:bg-muted"
                  onClick={() => {
                    setEditando(p);
                    setCriando(false);
                  }}
                >
                  Editar
                </button>
                <button
                  className="rounded-md border border-border bg-card px-3 py-1.5 text-sm text-danger transition-colors hover:bg-danger/5"
                  onClick={() => apagar(p.id)}
                >
                  Apagar
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
