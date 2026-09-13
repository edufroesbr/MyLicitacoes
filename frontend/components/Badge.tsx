export function BadgeScore({ score }: { score: number }) {
  const cls =
    score >= 0.67
      ? "bg-primary text-primary-foreground"
      : score >= 0.34
        ? "bg-warning text-white"
        : "bg-muted text-foreground-muted";
  return (
    <span className={`shrink-0 rounded px-2 py-0.5 text-xs font-medium ${cls}`}>
      {Math.round(score * 100)}%
    </span>
  );
}

export function BadgePrazo({ dataFim }: { dataFim: string | null }) {
  if (!dataFim) return null;
  const dias = Math.ceil((new Date(dataFim).getTime() - Date.now()) / 86_400_000);
  const urgente = dias <= 3;
  const texto = dias < 0 ? "encerrado" : dias === 0 ? "hoje" : `${dias}d`;
  const cls = urgente ? "bg-danger text-white" : "bg-muted text-foreground-muted";
  return <span className={`shrink-0 rounded px-2 py-0.5 text-xs font-medium ${cls}`}>{texto}</span>;
}
