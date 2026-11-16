"""Cria o banco, as tabelas e carrega os dados iniciais.

Uso:  python scripts/init_db.py          (cria o que faltar)
      python scripts/init_db.py --reset  (apaga tudo e recria)
"""
import sys
from pathlib import Path

import mysql.connector

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import Config  # noqa: E402
from videos_demo import adicionar_videos  # noqa: E402

DB_DIR = Path(__file__).resolve().parent.parent / "db"


def executar_arquivo(cursor, caminho: Path) -> None:
    linhas = [l for l in caminho.read_text(encoding="utf-8").splitlines() if not l.strip().startswith("--")]
    for comando in "\n".join(linhas).split(";"):
        if comando.strip():
            cursor.execute(comando)


def main() -> None:
    conn = mysql.connector.connect(
        host=Config.DB_HOST, port=Config.DB_PORT,
        user=Config.DB_USER, password=Config.DB_PASSWORD,
    )
    cur = conn.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {Config.DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    cur.execute(f"USE {Config.DB_NAME}")
    # Recria as tabelas se pediu --reset ou se o banco é da versão antiga (com projetores)
    cur.execute("SHOW TABLES LIKE 'projetores'")
    banco_antigo = cur.fetchone() is not None
    if "--reset" in sys.argv or banco_antigo:
        executar_arquivo(cur, DB_DIR / "reset.sql")
        print("Tabelas antigas removidas e recriadas.")
    executar_arquivo(cur, DB_DIR / "schema.sql")
    cur.execute("SHOW COLUMNS FROM usuarios LIKE 'is_admin'")
    if cur.fetchone() is None:
        cur.execute("ALTER TABLE usuarios ADD COLUMN is_admin TINYINT(1) NOT NULL DEFAULT 0 AFTER senha_hash")
        print("Permissões administrativas adicionadas à tabela de usuários.")
    cur.execute("SHOW COLUMNS FROM titulos LIKE 'visivel'")
    if cur.fetchone() is None:
        cur.execute("ALTER TABLE titulos ADD COLUMN visivel TINYINT(1) NOT NULL DEFAULT 1 AFTER destaque")
        print("Controle de visibilidade adicionado ao catálogo.")
    cur.execute(f"USE {Config.DB_NAME}")
    cur.execute("SELECT COUNT(*) FROM titulos")
    if cur.fetchone()[0] == 0:
        executar_arquivo(cur, DB_DIR / "seed.sql")
        print("Dados iniciais carregados.")
    else:
        print("Dados iniciais já existiam, nada foi alterado.")
    adicionados = adicionar_videos(cur)
    print(f"{adicionados} trailer(s) adicionado(s) ao catálogo.")
    conn.commit()
    cur.close()
    conn.close()
    print("Banco pronto.")


if __name__ == "__main__":
    main()
