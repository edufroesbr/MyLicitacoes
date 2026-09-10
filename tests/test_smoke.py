def test_importa_app_e_config():
    from app.config import Settings
    s = Settings(database_url="postgresql+psycopg://u:p@localhost/db", pdf_dir="/tmp/pdfs")
    assert s.pncp_base_url.endswith("/api/consulta")
    assert s.score_piso == 0.34
