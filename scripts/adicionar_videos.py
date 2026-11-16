"""Adiciona os trailers ao banco existente sem recriar tabelas ou contas.

Uso: python scripts/adicionar_videos.py
"""
import sys
from pathlib import Path

import mysql.connector

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import Config  # noqa: E402
from videos_demo import VIDEOS_DEMO, adicionar_videos  # noqa: E402


def main():
    raiz = Path(__file__).resolve().parent.parent
    for video in VIDEOS_DEMO:
        if not (raiz / video["video_url"].lstrip("/")).is_file():
            raise SystemExit(f"Arquivo de vídeo ausente: {video['video_url']}")

    try:
        with mysql.connector.connect(
            host=Config.DB_HOST, port=Config.DB_PORT, user=Config.DB_USER,
            password=Config.DB_PASSWORD, database=Config.DB_NAME, charset="utf8mb4",
        ) as conn:
            with conn.cursor() as cursor:
                adicionados = adicionar_videos(cursor)
            conn.commit()
    except mysql.connector.Error as erro:
        raise SystemExit(
            f"Não foi possível adicionar os vídeos (MySQL {erro.errno}). "
            "Confira o .env e se o banco foi inicializado."
        ) from None
    print(f"{adicionados} vídeo(s) adicionado(s). Os três trailers estão no catálogo.")


if __name__ == "__main__":
    main()
