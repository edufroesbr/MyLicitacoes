"use client";

import type { FiltrosEditais } from "@/lib/api";

interface Props {
  filtros: FiltrosEditais;
  onChange: (f: FiltrosEditais) => void;
}

const campoCls = "rounded border border-border bg-card px-2 py-1 text-sm text-foreground";

export default function Filtros({ filtros, onChange }: Props) {
  function set<K extends keyof FiltrosEditais>(chave: K, valor: FiltrosEditais[K]) {
    onChange({ ...filtros, [chave]: valor, pagina: 1 });
  }

  return (
    <div className="mb-4 flex flex-wrap gap-2">
      <input
        className={campoCls}
        placeholder="Buscar no objeto..."
        value={filtros.q ?? ""}
        onChange={(e) => set("q", e.target.value)}
      />
      <input
        className={`${campoCls} w-16`}
        placeholder="UF"
        maxLength={2}
        value={filtros.uf ?? ""}
        onChange={(e) => set("uf", e.target.value.toUpperCase())}
      />
      <input
        className={campoCls}
        placeholder="Modalidade"
        value={filtros.modalidade ?? ""}
        onChange={(e) => set("modalidade", e.target.value)}
      />
      <input
        className={campoCls}
        placeholder="Fonte"
        value={filtros.fonte ?? ""}
        onChange={(e) => set("fonte", e.target.value)}
      />
      <select
        className={campoCls}
        value={filtros.status ?? ""}
        onChange={(e) => set("status", e.target.value || undefined)}
      >
        <option value="">Status (todos)</option>
        <option value="novo">Novo</option>
        <option value="lido">Lido</option>
        <option value="arquivado">Arquivado</option>
        <option value="oportunidade">Oportunidade</option>
      </select>
      <select
        className={campoCls}
        value={filtros.score_min ?? ""}
        onChange={(e) => set("score_min", e.target.value ? Number(e.target.value) : undefined)}
      >
        <option value="">Score minimo (todos)</option>
        <option value="0.34">Medio (34%+)</option>
        <option value="0.67">Alto (67%+)</option>
      </select>
    </div>
  );
}
