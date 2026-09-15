const pill =
  "inline-flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium tnum";

export function BadgeScore({ score }: { score: number }) {
  const tier =
    score >= 0.67
      ? { cls: "bg-score-high/12 text-score-high", dot: "bg-score-high" }
      : score >= 0.34
        ? { cls: "bg-score-mid/14 text-score-mid", dot: "bg-score-mid" }
        : { cls: "bg-muted text-foreground-muted", dot: "bg-score-low" };
  return (
    <span className={`${pill} ${tier.cls}`} title="Relevancia tipo-LexFlow">
      <span aria-hidden className={`h-1.5 w-1.5 rounded-full ${tier.dot}`} />
      {Math.round(score * 100)}%
    </span>
  );
}

function diasAte(dataFim: string): number {
  const [y, m, d] = dataFim.split("-").map(Number);
  const alvo = new Date(y, m - 1, d);
  const hoje = new Date();
  const base = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate());
  return Math.round((alvo.getTime() - base.getTime()) / 86_400_000);
}

export function BadgePrazo({ dataFim }: { dataFim: string | null }) {
  if (!dataFim) return null;
  const dias = diasAte(dataFim);
  const texto = dias < 0 ? "encerrado" : dias === 0 ? "hoje" : `${dias}d`;
  const cls =
    dias < 0
      ? "bg-muted text-foreground-muted line-through decoration-1"
      : dias <= 3
        ? "bg-danger/12 text-danger"
        : "bg-muted text-foreground-muted";
  return (
    <span className={`${pill} ${cls}`} title="Prazo para propostas">
      {texto}
    </span>
  );
}
