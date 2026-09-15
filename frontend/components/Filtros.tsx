"use client";

import { useState } from "react";
import type { FiltrosEditais } from "@/lib/api";

interface Props {
  filtros: FiltrosEditais;
  onChange: (f: FiltrosEditais) => void;
}

const campo =
  "rounded-md border border-border bg-card px-3 py-1.5 text-sm text-foreground placeholder:text-foreground-muted/70 transition-colors hover:border-foreground-muted/40";

export default function Filtros({ filtros, onChange }: Props) {
  // Campos de texto sao rascunho local; aplicam no submit (Buscar / Enter).
  // Os selects aplicam na hora, ja incluindo o rascunho de texto atual.
  const [q, setQ] = useState(filtros.q ?? "");
  const [uf, setUf] = useState(filtros.uf ?? "");
  const [modalidade, setModalidade] = useState(filtros.modalidade ?? "");
  const [fonte, setFonte] = useState(filtros.fonte ?? "");

  function aplicar(extra: Partial<FiltrosEditais> = {}) {
    onChange({
      ...filtros,
      q: q || undefined,
      uf: uf || undefined,
      modalidade: modalidade || undefined,
      fonte: fonte || undefined,
      pagina: 1,
      ...extra,
    });
  }

  return (
    <form
      className="mb-5 flex flex-wrap items-center gap-2 rounded-lg border border-border bg-surface/70 p-2.5 shadow-card"
      onSubmit={(e) => {
        e.preventDefault();
        aplicar();
      }}
    >
      <div className="relative min-w-[13rem] flex-1">
        <svg
          aria-hidden
          viewBox="0 0 24 24"
          className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground-muted"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
        >
          <circle cx="11" cy="11" r="7" />
          <path d="m20 20-3.2-3.2" />
        </svg>
        <input
          className={`${campo} w-full pl-8`}
          placeholder="Buscar no objeto do edital..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>
      <input
        className={`${campo} w-16 uppercase`}
        placeholder="UF"
        maxLength={2}
        value={uf}
        onChange={(e) => setUf(e.target.value.toUpperCase())}
      />
      <input
        className={`${campo} w-32`}
        placeholder="Modalidade"
        value={modalidade}
        onChange={(e) => setModalidade(e.target.value)}
      />
      <input
        className={`${campo} w-28`}
        placeholder="Fonte"
        value={fonte}
        onChange={(e) => setFonte(e.target.value)}
      />
      <select
        className={campo}
        value={filtros.status ?? ""}
        onChange={(e) => aplicar({ status: e.target.value || undefined })}
      >
        <option value="">Status (todos)</option>
        <option value="novo">Novo</option>
        <option value="lido">Lido</option>
        <option value="arquivado">Arquivado</option>
        <option value="oportunidade">Oportunidade</option>
      </select>
      <select
        className={campo}
        value={filtros.score_min ?? ""}
        onChange={(e) => aplicar({ score_min: e.target.value ? Number(e.target.value) : undefined })}
      >
        <option value="">Score (todos)</option>
        <option value="0.34">Medio (34%+)</option>
        <option value="0.67">Alto (67%+)</option>
      </select>
      <button
        type="submit"
        className="rounded-md bg-primary px-4 py-1.5 text-sm font-medium text-primary-foreground shadow-sm transition-colors hover:bg-primary-hover"
      >
        Buscar
      </button>
    </form>
  );
}
