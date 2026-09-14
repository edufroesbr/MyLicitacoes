"use client";

import { useState } from "react";
import { mudarStatus } from "@/lib/api";
import type { StatusCaixa } from "@/lib/types";

interface Props {
  editalId: number;
  statusAtual: StatusCaixa;
  onMudou: (novo: StatusCaixa) => void;
}

const ACOES: { status: StatusCaixa; rotulo: string }[] = [
  { status: "lido", rotulo: "Marcar como lido" },
  { status: "arquivado", rotulo: "Arquivar" },
  { status: "oportunidade", rotulo: "Marcar como oportunidade" },
];

export default function AcoesStatus({ editalId, statusAtual, onMudou }: Props) {
  const [processando, setProcessando] = useState<StatusCaixa | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  async function acionar(novo: StatusCaixa) {
    setProcessando(novo);
    setErro(null);
    try {
      await mudarStatus(editalId, novo);
      onMudou(novo);
    } catch (e: unknown) {
      setErro(e instanceof Error ? e.message : String(e));
    } finally {
      setProcessando(null);
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap gap-2">
        {ACOES.map((a) => (
          <button
            key={a.status}
            className="rounded border border-border px-3 py-1 text-sm disabled:opacity-50"
            disabled={statusAtual === a.status || processando !== null}
            onClick={() => acionar(a.status)}
          >
            {processando === a.status ? "A processar..." : a.rotulo}
          </button>
        ))}
      </div>
      {erro && <p className="text-sm text-danger">Erro ao mudar status: {erro}</p>}
    </div>
  );
}
