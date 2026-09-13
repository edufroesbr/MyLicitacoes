from pathlib import Path

from app.config import Settings

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_pdf_dir_relativo_e_independente_do_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    s1 = Settings(database_url="postgresql+psycopg://u:p@localhost/db")

    outro_dir = tmp_path / "outro"
    outro_dir.mkdir()
    monkeypatch.chdir(outro_dir)
    s2 = Settings(database_url="postgresql+psycopg://u:p@localhost/db")

    esperado = str((REPO_ROOT / "pdfs").resolve())
    assert s1.pdf_dir == esperado
    assert s2.pdf_dir == esperado
