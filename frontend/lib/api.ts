import { API_URL } from "./config";
import type {
  Digest,
  EditalDetalhe,
  EditalResumo,
  Pagina,
  Projeto,
  StatusCaixa,
} from "./types";

async function j<T>(r: Response): Promise<T> {
  if (!r.ok) throw new Error(`API ${r.status}`);
  return r.json() as Promise<T>;
}

export interface FiltrosEditais {
  uf?: string;
  modalidade?: string;
  fonte?: string;
  status?: string;
  score_min?: number;
  q?: string;
  projeto_id?: number;
  pagina?: number;
  tamanho?: number;
}

export async function listarEditais(f: FiltrosEditais = {}): Promise<Pagina<EditalResumo>> {
  const qs = new URLSearchParams();
  Object.entries(f).forEach(([k, v]) => {
    if (v !== undefined && v !== "") qs.set(k, String(v));
  });
  return j(await fetch(`${API_URL}/editais?${qs}`, { cache: "no-store" }));
}

export async function obterEdital(id: number): Promise<EditalDetalhe> {
  return j(await fetch(`${API_URL}/editais/${id}`, { cache: "no-store" }));
}

export async function mudarStatus(id: number, status: StatusCaixa): Promise<EditalDetalhe> {
  return j(
    await fetch(`${API_URL}/editais/${id}`, {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ status }),
    })
  );
}

export function urlArquivo(editalId: number, arquivoId: number): string {
  return `${API_URL}/editais/${editalId}/arquivo/${arquivoId}`;
}

export async function digestHoje(): Promise<Digest> {
  return j(await fetch(`${API_URL}/digest/hoje`, { cache: "no-store" }));
}

export async function listarProjetos(): Promise<Projeto[]> {
  return j(await fetch(`${API_URL}/projetos-interesse`, { cache: "no-store" }));
}

export async function criarProjeto(p: Partial<Projeto>): Promise<Projeto> {
  return j(
    await fetch(`${API_URL}/projetos-interesse`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(p),
    })
  );
}

export async function atualizarProjeto(id: number, p: Partial<Projeto>): Promise<Projeto> {
  return j(
    await fetch(`${API_URL}/projetos-interesse/${id}`, {
      method: "PUT",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(p),
    })
  );
}

export async function apagarProjeto(id: number): Promise<void> {
  const r = await fetch(`${API_URL}/projetos-interesse/${id}`, { method: "DELETE" });
  if (!r.ok) throw new Error(`API ${r.status}`);
}
