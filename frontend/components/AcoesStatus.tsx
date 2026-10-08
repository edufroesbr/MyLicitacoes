"use client";

import { useState } from "react";
import { Archive, CheckCheck, Loader2, Star } from "lucide-react";
import { mudarStatus } from "@/lib/api";
import type { StatusCaixa } from "@/lib/types";

interface Props {
  editalId: number;
  statusAtual: StatusCaixa;
  onMudou: (novo: StatusCaixa) => void;
}

const ACOES: { status: StatusCaixa; rotulo: string; Icone: typeof CheckCheck }[] = [
  { status: "lido", rotulo: "Marcar como lido", Icone: CheckCheck },
  { status: "arquivado", rotulo: "Arquivar", Icone: Archive },
  { status: "oportunidade", rotulo: "Marcar como oportunidade", Icone: Star },
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
            className="flex items-center gap-1.5 rounded-md border border-border bg-card px-3 py-1.5 text-sm font-medium text-foreground transition-colors hover:bg-muted disabled:opacity-40"
            disabled={statusAtual === a.status || processando !== null}
            onClick={() => acionar(a.status)}
          >
            {processando === a.status ? (
              <Loader2 aria-hidden className="h-4 w-4 animate-spin" strokeWidth={2} />
            ) : (
              <a.Icone aria-hidden className="h-4 w-4" strokeWidth={2} />
            )}
            {processando === a.status ? "A processar..." : a.rotulo}
          </button>
        ))}
      </div>
      {erro && <p className="text-sm text-danger">Erro ao mudar status: {erro}</p>}
    </div>
  );
}
