# app/adapters/notificacao/render.py
from app.domain.digest import Digest


def render_texto(d: Digest) -> str:
    linhas = [f"Radar de Editais — {d.data_ref.isoformat()}",
              f"Novos: {d.total_novos} | Relevantes: {d.total_relevantes} | Downloads: {d.total_downloads}"]
    if d.fontes_com_falha:
        linhas.append(f"Fontes com falha: {', '.join(d.fontes_com_falha)}")
    for p in d.projetos:
        linhas.append(f"Projeto {p.nome}: {p.novos} novos, {p.prazo_a_fechar} com prazo a fechar")
    for e in d.destaques:
        linhas.append(f"- {e.objeto[:90]} ({e.orgao_nome})")
    return "\n".join(linhas)


def render_html(d: Digest) -> str:
    itens = "".join(f"<li>{e.objeto[:120]} — <b>{e.orgao_nome}</b> ({e.uf or ''})</li>" for e in d.destaques)
    projetos = "".join(f"<li>{p.nome}: {p.novos} novos, {p.prazo_a_fechar} a fechar</li>" for p in d.projetos)
    falha = f"<p>Fontes com falha: {', '.join(d.fontes_com_falha)}</p>" if d.fontes_com_falha else ""
    return (f"<h2>Radar de Editais — {d.data_ref.isoformat()}</h2>"
            f"<p>Novos: {d.total_novos} | Relevantes: {d.total_relevantes} | Downloads: {d.total_downloads}</p>"
            f"{falha}<h3>Projetos</h3><ul>{projetos}</ul><h3>Destaques</h3><ul>{itens}</ul>")
