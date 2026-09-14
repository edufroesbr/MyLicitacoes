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
    <main className="mx-auto max-w-2xl p-6">
      <h1 className="mb-4 text-xl font-semibold text-foreground">Projetos de interesse</h1>

      {erro && <p className="mb-4 text-danger">Erro: {erro}</p>}

      {!formAberto && (
        <button
          className="mb-4 rounded bg-primary px-3 py-1 text-sm text-primary-foreground"
          onClick={() => setCriando(true)}
        >
          Novo projeto
        </button>
      )}

      {formAberto && (
        <div className="mb-4">
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

      {carregando && <p className="text-foreground-muted">A carregar...</p>}

      {!carregando && projetos.length === 0 && (
        <p className="text-foreground-muted">Nenhum projeto criado.</p>
      )}

      {!carregando && projetos.length > 0 && (
        <ul className="divide-y divide-border rounded-lg border border-border bg-card">
          {projetos.map((p) => (
            <li key={p.id} className="flex items-center justify-between gap-2 p-4">
              <div>
                <div className="font-medium text-foreground">
                  {p.nome}
                  {!p.ativo && <span className="ml-2 text-xs text-foreground-muted">(inativo)</span>}
                </div>
                <div className="text-sm text-foreground-muted">
                  {p.palavras_chave.length > 0 ? p.palavras_chave.join(", ") : "sem palavras-chave"}
                </div>
              </div>
              <div className="flex shrink-0 gap-2">
                <button
                  className="rounded border border-border px-2 py-1 text-sm"
                  onClick={() => {
                    setEditando(p);
                    setCriando(false);
                  }}
                >
                  Editar
                </button>
                <button
                  className="rounded border border-border px-2 py-1 text-sm text-danger"
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
