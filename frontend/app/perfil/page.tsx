"use client";

import { useEffect, useState, type FormEvent } from "react";
import { Loader2 } from "lucide-react";
import { atualizarPerfil, obterPerfil } from "@/lib/api";
import type { Perfil } from "@/lib/types";

const campoCls =
  "rounded-md border border-border bg-card px-3 py-1.5 text-sm text-foreground transition-colors hover:border-foreground-muted/40";

export default function PerfilPage() {
  const [carregando, setCarregando] = useState(true);
  const [carregado, setCarregado] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [sucesso, setSucesso] = useState(false);

  const [nome, setNome] = useState("");
  const [emailDigest, setEmailDigest] = useState("");
  const [telegramChatId, setTelegramChatId] = useState("");
  const [receberEmail, setReceberEmail] = useState(false);
  const [receberTelegram, setReceberTelegram] = useState(false);

  function popular(p: Perfil) {
    setNome(p.nome);
    setEmailDigest(p.email_digest ?? "");
    setTelegramChatId(p.telegram_chat_id ?? "");
    setReceberEmail(p.receber_email);
    setReceberTelegram(p.receber_telegram);
  }

  useEffect(() => {
    setCarregando(true);
    setErro(null);
    obterPerfil()
      .then((p) => {
        popular(p);
        setCarregado(true);
      })
      .catch((e: unknown) => setErro(e instanceof Error ? e.message : String(e)))
      .finally(() => setCarregando(false));
  }, []);

  async function submeter(e: FormEvent) {
    e.preventDefault();
    setSalvando(true);
    setErro(null);
    setSucesso(false);
    try {
      const atualizado = await atualizarPerfil({
        nome,
        email_digest: emailDigest || null,
        telegram_chat_id: telegramChatId || null,
        receber_email: receberEmail,
        receber_telegram: receberTelegram,
      });
      popular(atualizado);
      setSucesso(true);
    } catch (e: unknown) {
      setErro(e instanceof Error ? e.message : String(e));
    } finally {
      setSalvando(false);
    }
  }

  return (
    <main className="mx-auto max-w-2xl px-6 py-8">
      <header className="mb-5">
        <h1 className="font-display text-3xl font-semibold tracking-tightest text-foreground">
          Configurações
        </h1>
        <p className="mt-1 text-sm text-foreground-muted">
          Preferências de envio do digest diário.
        </p>
      </header>

      {erro && (
        <div className="mb-4 rounded-lg border border-danger/30 bg-danger/5 p-4 text-sm text-danger">
          Erro: {erro}
        </div>
      )}

      {sucesso && !erro && (
        <div className="mb-4 rounded-lg border border-primary/30 bg-primary/5 p-4 text-sm text-primary-ink">
          Preferências guardadas com sucesso.
        </div>
      )}

      {carregando && (
        <div className="rounded-lg border border-border bg-card p-5 shadow-card">
          <div className="h-4 w-1/3 animate-pulse rounded bg-muted" />
          <div className="mt-3 h-4 w-2/3 animate-pulse rounded bg-muted/70" />
        </div>
      )}

      {!carregando && carregado && (
        <form
          onSubmit={submeter}
          className="flex flex-col gap-3 rounded-lg border border-border bg-card p-5 shadow-card"
        >
          <label className="flex flex-col gap-1 text-sm text-foreground-muted">
            Nome
            <input className={campoCls} value={nome} onChange={(e) => setNome(e.target.value)} />
          </label>
          <label className="flex flex-col gap-1 text-sm text-foreground-muted">
            E-mail do digest
            <input
              type="email"
              className={campoCls}
              value={emailDigest}
              onChange={(e) => setEmailDigest(e.target.value)}
            />
          </label>
          <label className="flex flex-col gap-1 text-sm text-foreground-muted">
            Chat ID do Telegram
            <input
              className={campoCls}
              value={telegramChatId}
              onChange={(e) => setTelegramChatId(e.target.value)}
            />
          </label>
          <label className="flex items-center gap-2 text-sm text-foreground-muted">
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-border accent-[hsl(var(--primary))]"
              checked={receberEmail}
              onChange={(e) => setReceberEmail(e.target.checked)}
            />
            Receber digest por e-mail
          </label>
          <label className="flex items-center gap-2 text-sm text-foreground-muted">
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-border accent-[hsl(var(--primary))]"
              checked={receberTelegram}
              onChange={(e) => setReceberTelegram(e.target.checked)}
            />
            Receber digest por Telegram
          </label>
          <div className="flex gap-2 pt-1">
            <button
              type="submit"
              className="flex items-center gap-1.5 rounded-md bg-primary px-4 py-1.5 text-sm font-medium text-primary-foreground shadow-sm transition-colors hover:bg-primary-hover disabled:opacity-50"
              disabled={salvando}
            >
              {salvando && <Loader2 aria-hidden className="h-4 w-4 animate-spin" strokeWidth={2} />}
              {salvando ? "A guardar..." : "Guardar"}
            </button>
          </div>
        </form>
      )}
    </main>
  );
}
