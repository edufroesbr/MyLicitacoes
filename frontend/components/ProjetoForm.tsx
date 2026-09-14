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

const campoCls = "rounded border border-border bg-background px-2 py-1 text-sm text-foreground";

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
      className="flex flex-col gap-3 rounded-lg border border-border bg-card p-4"
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
            className={campoCls}
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
        <input type="checkbox" checked={ativo} onChange={(e) => setAtivo(e.target.checked)} />
        Ativo
      </label>
      <div className="flex gap-2">
        <button
          type="submit"
          className="rounded bg-primary px-3 py-1 text-sm text-primary-foreground disabled:opacity-50"
          disabled={salvando}
        >
          {salvando ? "A guardar..." : "Guardar"}
        </button>
        <button type="button" className="rounded border border-border px-3 py-1 text-sm" onClick={onCancelar}>
          Cancelar
        </button>
      </div>
    </form>
  );
}
