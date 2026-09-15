"use client";

import { useState, type FormEvent } from "react";
import type { Projeto } from "@/lib/types";

export interface DadosProjetoForm {
  nome: string;
  palavras_chave: string[];
  filtros: Record<string, unknown>;
  ativo: boolean;
}

interface Props {
  projeto?: Projeto;
  salvando?: boolean;
  onSalvar: (dados: DadosProjetoForm) => void;
  onCancelar: () => void;
}

const campoCls =
  "rounded-md border border-border bg-card px-3 py-1.5 text-sm text-foreground transition-colors hover:border-foreground-muted/40";

export default function ProjetoForm({ projeto, salvando, onSalvar, onCancelar }: Props) {
  const [nome, setNome] = useState(projeto?.nome ?? "");
  const [palavrasChaveTexto, setPalavrasChaveTexto] = useState(
    (projeto?.palavras_chave ?? []).join(", ")
  );
  const [uf, setUf] = useState(typeof projeto?.filtros.uf === "string" ? projeto.filtros.uf : "");
  const [modalidade, setModalidade] = useState(
    typeof projeto?.filtros.modalidade === "string" ? projeto.filtros.modalidade : ""
  );
  const [ativo, setAtivo] = useState(projeto?.ativo ?? true);

  function submeter(e: FormEvent) {
    e.preventDefault();
    const filtros: Record<string, unknown> = {};
    if (uf) filtros.uf = uf;
    if (modalidade) filtros.modalidade = modalidade;
    onSalvar({
      nome,
      palavras_chave: palavrasChaveTexto
        .split(",")
        .map((p) => p.trim())
        .filter(Boolean),
      filtros,
      ativo,
    });
  }

  return (
    <form
      onSubmit={submeter}
      className="flex flex-col gap-3 rounded-lg border border-border bg-card p-5 shadow-card"
    >
      <label className="flex flex-col gap-1 text-sm text-foreground-muted">
        Nome
        <input className={campoCls} value={nome} onChange={(e) => setNome(e.target.value)} required />
      </label>
      <label className="flex flex-col gap-1 text-sm text-foreground-muted">
        Palavras-chave (separadas por virgula)
        <input
          className={campoCls}
          value={palavrasChaveTexto}
          onChange={(e) => setPalavrasChaveTexto(e.target.value)}
        />
      </label>
      <div className="flex gap-3">
        <label className="flex flex-1 flex-col gap-1 text-sm text-foreground-muted">
          UF
          <input
            className={`${campoCls} uppercase`}
            maxLength={2}
            value={uf}
            onChange={(e) => setUf(e.target.value.toUpperCase())}
          />
        </label>
        <label className="flex flex-1 flex-col gap-1 text-sm text-foreground-muted">
          Modalidade
          <input className={campoCls} value={modalidade} onChange={(e) => setModalidade(e.target.value)} />
        </label>
      </div>
      <label className="flex items-center gap-2 text-sm text-foreground-muted">
        <input
          type="checkbox"
          className="h-4 w-4 rounded border-border accent-[hsl(var(--primary))]"
          checked={ativo}
          onChange={(e) => setAtivo(e.target.checked)}
        />
        Ativo
      </label>
      <div className="flex gap-2 pt-1">
        <button
          type="submit"
          className="rounded-md bg-primary px-4 py-1.5 text-sm font-medium text-primary-foreground shadow-sm transition-colors hover:bg-primary-hover disabled:opacity-50"
          disabled={salvando}
        >
          {salvando ? "A guardar..." : "Guardar"}
        </button>
        <button
          type="button"
          className="rounded-md border border-border bg-card px-4 py-1.5 text-sm transition-colors hover:bg-muted"
          onClick={onCancelar}
        >
          Cancelar
        </button>
      </div>
    </form>
  );
}
