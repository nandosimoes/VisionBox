"""Cria ou atualiza a conta administradora usando as credenciais de admin.env.

1. Copie admin.env.example para admin.env na raiz do projeto.
2. Edite ADMIN_NAME, ADMIN_EMAIL e ADMIN_PASSWORD.
3. Execute: python scripts/configurar_admin.py
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import dotenv_values
from werkzeug.security import generate_password_hash
import mysql.connector
from config import Config

arquivo = ROOT / "admin.env"
if not arquivo.exists():
    raise SystemExit(
        "Arquivo admin.env nao encontrado. Copie admin.env.example para admin.env "
        "e preencha os dados do administrador."
    )

credenciais = dotenv_values(arquivo)
nome = (credenciais.get("ADMIN_NAME") or "").strip()
email = (credenciais.get("ADMIN_EMAIL") or "").strip().lower()
senha = credenciais.get("ADMIN_PASSWORD") or ""

if not nome or "@" not in email or len(senha) < 8:
    raise SystemExit(
        "Preencha ADMIN_NAME, ADMIN_EMAIL e ADMIN_PASSWORD no admin.env. "
        "A senha precisa ter pelo menos 8 caracteres."
    )
if senha == "troque-esta-senha-por-uma-forte":
    raise SystemExit("Troque a senha de exemplo por uma senha forte no admin.env.")

conn = mysql.connector.connect(
    host=Config.DB_HOST,
    port=Config.DB_PORT,
    user=Config.DB_USER,
    password=Config.DB_PASSWORD,
    database=Config.DB_NAME,
)
try:
    cur = conn.cursor()
    senha_hash = generate_password_hash(senha)
    cur.execute("SELECT id FROM usuarios WHERE email=%s", (email,))
    existente = cur.fetchone()
    if existente:
        cur.execute(
            "UPDATE usuarios SET nome=%s, senha_hash=%s, is_admin=1 WHERE id=%s",
            (nome, senha_hash, existente[0]),
        )
        mensagem = "Conta existente atualizada e promovida a administradora."
    else:
        cur.execute(
            "INSERT INTO usuarios (nome, email, senha_hash, is_admin) VALUES (%s, %s, %s, 1)",
            (nome, email, senha_hash),
        )
        mensagem = "Conta administradora criada com sucesso."
    conn.commit()
    print(mensagem)
    print(f"E-mail de acesso: {email}")
    print("Acesse /admin para entrar no painel.")
finally:
    conn.close()
