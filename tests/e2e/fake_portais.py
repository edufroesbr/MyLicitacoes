# tests/e2e/fake_portais.py
import contextlib
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

_EDITAL = {
    "orgaoEntidade": {"cnpj": "00000000000191", "razaoSocial": "Tribunal X"},
    "unidadeOrgao": {"ufSigla": "AM", "municipioNome": "Manaus"},
    "anoCompra": 2026, "sequencialCompra": 42,
    "objetoCompra": "Contratacao de servico de clipping e monitoramento de publicacoes",
    "modalidadeNome": "Pregao", "valorTotalEstimado": 1000.0,
    "dataPublicacaoPncp": "2026-09-01T10:00:00",
}


class _H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if "/v1/contratacoes/publicacao" in self.path:
            body = {"data": [_EDITAL], "totalPaginas": 1, "totalRegistros": 1, "numeroPagina": 1}
        elif "/arquivos" in self.path:
            body = [{"url": "http://x/edital.pdf", "titulo": "Edital.pdf"}]
        else:
            self.send_response(404); self.end_headers(); return
        data = json.dumps(body).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)


@contextlib.contextmanager
def servidor_fake():
    srv = HTTPServer(("127.0.0.1", 0), _H)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        yield f"http://127.0.0.1:{srv.server_address[1]}"
    finally:
        srv.shutdown()
