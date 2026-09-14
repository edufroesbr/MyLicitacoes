export type StatusCaixa = "novo" | "lido" | "arquivado" | "oportunidade";

export interface EditalResumo {
  id: number;
  fonte: string;
  objeto: string;
  orgao_nome: string;
  uf: string | null;
  modalidade: string | null;
  valor_estimado: string | null;
  data_publicacao: string | null;
  data_fim_propostas: string | null;
  score_relevancia: number;
  status: StatusCaixa;
}

export interface ArquivoResumo {
  id: number;
  tipo: string;
}

export interface EditalDetalhe extends EditalResumo {
  orgao_cnpj: string;
  municipio: string | null;
  motivo_relevancia: string;
  url_origem: string;
  arquivos: ArquivoResumo[];
}

export interface Pagina<T> {
  itens: T[];
  total: number;
  pagina: number;
  tamanho: number;
}

export interface Projeto {
  id: number;
  nome: string;
  palavras_chave: string[];
  filtros: Record<string, unknown>;
  ativo: boolean;
  criado_em: string;
}

export interface ResumoDigest {
  novos?: number;
  relevantes?: number;
  downloads?: number;
  fontes_com_falha?: string[];
}

export interface Digest {
  data_ref: string;
  resumo: ResumoDigest;
  destaques: EditalResumo[];
}
