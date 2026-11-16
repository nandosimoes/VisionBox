import secrets
from pathlib import Path
from uuid import uuid4
from functools import wraps

import mysql.connector
from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from videos_demo import CREDITOS_POR_VIDEO
from models import (TIPO_SINGULAR, TIPOS, FavoritoRepo, HistoricoRepo,
                    ProgressoRepo, TituloRepo, UsuarioRepo)

app = Flask(__name__)
app.secret_key = Config.SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024 * 1024  # até 1 GB por vídeo
UPLOAD_DIR = Path(app.root_path) / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.jinja_env.globals["tipo_label"] = lambda t: TIPO_SINGULAR.get(t, t)
app.jinja_env.globals["TIPOS"] = TIPOS


@app.template_filter("duracao")
def duracao(minutos):
    h, m = divmod(int(minutos), 60)
    return f"{h}h {m:02d}min" if h else f"{m} min"


# ---------- utilidades ----------
def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not g.usuario:
            return redirect(url_for("entrar"))
        return view(*args, **kwargs)
    return wrapper


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not g.usuario:
            return redirect(url_for("admin_login"))
        if not g.usuario.get("is_admin"):
            abort(403)
        return view(*args, **kwargs)
    return wrapper


def destino_seguro(padrao):
    alvo = request.form.get("next", "")
    return alvo if alvo.startswith("/") and not alvo.startswith("//") else padrao


@app.before_request
def preparar():
    uid = session.get("uid")
    g.usuario = UsuarioRepo.por_id(uid) if uid else None
    if request.method == "POST":
        enviado = request.form.get("_csrf") or request.headers.get("X-CSRF", "")
        if not secrets.compare_digest(session.get("_csrf", ""), enviado):
            abort(400)


@app.context_processor
def contexto():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return {"csrf_token": session["_csrf"], "usuario": g.get("usuario")}


# ---------- autenticação ----------
@app.route("/entrar", methods=["GET", "POST"])
def entrar():
    if g.usuario:
        return redirect(url_for("inicio"))
    if request.method == "POST":
        u = UsuarioRepo.por_email(request.form.get("email", "").strip().lower())
        if u and check_password_hash(u["senha_hash"], request.form.get("senha", "")):
            session.clear()
            session["uid"] = u["id"]
            return redirect(url_for("inicio"))
        flash("E-mail ou senha incorretos. Confira os dados e tente de novo.", "erro")
    return render_template("auth.html", modo="entrar")


@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    if g.usuario:
        return redirect(url_for("inicio"))
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        if not nome or "@" not in email:
            flash("Informe seu nome e um e-mail válido.", "erro")
        elif len(senha) < 8:
            flash("A senha precisa ter pelo menos 8 caracteres.", "erro")
        elif UsuarioRepo.por_email(email):
            flash("Já existe uma conta com esse e-mail. Entre ou use outro e-mail.", "erro")
        else:
            try:
                uid = UsuarioRepo.criar(nome, email, generate_password_hash(senha))
            except mysql.connector.Error:
                flash("Não foi possível criar a conta agora. Tente novamente.", "erro")
            else:
                session.clear()
                session["uid"] = uid
                return redirect(url_for("inicio"))
    return render_template("auth.html", modo="registrar")


@app.post("/sair")
def sair():
    session.clear()
    return redirect(url_for("entrar"))


# ---------- páginas ----------
@app.route("/")
@login_required
def inicio():
    uid = g.usuario["id"]
    destaques = TituloRepo.destaques()
    continuar = TituloRepo.continuar(uid)
    heroi = destaques[0] if destaques else None
    return render_template(
        "inicio.html",
        heroi=heroi,
        heroi_lista=heroi and FavoritoRepo.existe(uid, heroi["id"]),
        continuar=continuar,
        minha_lista=FavoritoRepo.listar(uid),
        disponiveis=TituloRepo.com_video(),
        secoes=[(chave, nome, TituloRepo.listar(chave)) for chave, nome in TIPOS.items()],
    )


@app.route("/biblioteca")
@login_required
def biblioteca():
    tipo = request.args.get("tipo", "")
    busca = request.args.get("q", "").strip()
    return render_template("biblioteca.html", titulos=TituloRepo.listar(tipo, busca), tipo=tipo, busca=busca)


@app.route("/titulo/<int:titulo_id>")
@login_required
def titulo(titulo_id):
    t = TituloRepo.por_id(titulo_id) or abort(404)
    if not t.get("video_url") or not t.get("visivel", 1):
        abort(404)
    uid = g.usuario["id"]
    prog = ProgressoRepo.obter(uid, titulo_id)
    return render_template(
        "titulo.html", t=t, na_lista=FavoritoRepo.existe(uid, titulo_id),
        prog=prog if prog and prog["segundo_atual"] >= 10 and prog["pct"] < 95 else None,
        parecidos=TituloRepo.parecidos(t),
        creditos=CREDITOS_POR_VIDEO.get(t["video_url"] or Config.DEMO_VIDEO_URL),
    )


@app.post("/titulo/<int:titulo_id>/lista")
@login_required
def lista(titulo_id):
    t = TituloRepo.por_id(titulo_id) or abort(404)
    ativo = FavoritoRepo.alternar(g.usuario["id"], titulo_id)
    flash(f"“{t['titulo']}” {'entrou na' if ativo else 'saiu da'} Minha lista.", "ok")
    return redirect(destino_seguro(url_for("titulo", titulo_id=titulo_id)))


@app.route("/assistir/<int:titulo_id>")
@login_required
def assistir(titulo_id):
    t = TituloRepo.por_id(titulo_id) or abort(404)
    if not t.get("video_url") or not t.get("visivel", 1):
        abort(404)
    uid = g.usuario["id"]
    prog = ProgressoRepo.obter(uid, titulo_id)
    recomecar = request.args.get("recomecar") == "1"
    retomar = 0 if recomecar or not prog or prog["pct"] >= 95 else prog["segundo_atual"]
    HistoricoRepo.registrar(uid, titulo_id)
    return render_template(
        "player.html", t=t, retomar=retomar,
        fonte=t["video_url"], demo=False,
    )


@app.post("/api/progresso/<int:titulo_id>")
@login_required
def salvar_progresso(titulo_id):
    TituloRepo.por_id(titulo_id) or abort(404)
    segundo = max(0, request.form.get("segundo", 0, type=int))
    pct = max(0, min(100, request.form.get("pct", 0, type=int)))
    ProgressoRepo.salvar(g.usuario["id"], titulo_id, segundo, pct)
    return jsonify(ok=True)


@app.route("/perfil")
@login_required
def perfil():
    uid = g.usuario["id"]
    return render_template(
        "perfil.html", lista=FavoritoRepo.listar(uid), recentes=HistoricoRepo.recentes(uid),
        stats=HistoricoRepo.estatisticas(uid),
    )


# ---------- painel administrativo ----------
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if g.usuario and g.usuario.get("is_admin"):
        return redirect(url_for("admin_painel"))
    if g.usuario:
        session.clear()
        return redirect(url_for("admin_login"))
    if request.method == "POST":
        u = UsuarioRepo.por_email(request.form.get("email", "").strip().lower())
        if u and u.get("is_admin") and check_password_hash(u["senha_hash"], request.form.get("senha", "")):
            session.clear()
            session["uid"] = u["id"]
            return redirect(url_for("admin_painel"))
        flash("Credenciais administrativas inválidas.", "erro")
    return render_template("admin_login.html")


@app.route("/admin/painel")
@admin_required
def admin_painel():
    return render_template("admin.html", usuarios=UsuarioRepo.listar(), titulos=TituloRepo.listar_admin())


@app.post("/admin/usuarios")
@admin_required
def admin_criar_usuario():
    nome = request.form.get("nome", "").strip()
    email = request.form.get("email", "").strip().lower()
    senha = request.form.get("senha", "")
    admin = 1 if request.form.get("is_admin") == "1" else 0
    if not nome or "@" not in email or len(senha) < 8:
        flash("Informe nome, e-mail válido e senha com pelo menos 8 caracteres.", "erro")
    elif UsuarioRepo.por_email(email):
        flash("Já existe um usuário com esse e-mail.", "erro")
    else:
        try:
            UsuarioRepo.criar(nome, email, generate_password_hash(senha), admin)
            flash("Usuário criado com sucesso.", "ok")
        except mysql.connector.Error:
            flash("Não foi possível criar o usuário.", "erro")
    return redirect(url_for("admin_painel"))


@app.post("/admin/usuarios/<int:uid>/excluir")
@admin_required
def admin_excluir_usuario(uid):
    if uid == g.usuario["id"]:
        flash("Você não pode excluir sua própria conta administrativa.", "erro")
    else:
        UsuarioRepo.excluir(uid)
        flash("Usuário excluído.", "ok")
    return redirect(url_for("admin_painel"))


@app.post("/admin/usuarios/<int:uid>/permissao")
@admin_required
def admin_permissao_usuario(uid):
    if uid == g.usuario["id"]:
        flash("Não é possível remover sua própria permissão administrativa.", "erro")
    else:
        UsuarioRepo.alterar_admin(uid, request.form.get("is_admin") == "1")
        flash("Permissões atualizadas.", "ok")
    return redirect(url_for("admin_painel"))


@app.post("/admin/filmes")
@admin_required
def admin_criar_titulo():
    dados = {k: request.form.get(k, "").strip() for k in ("titulo", "tipo", "genero", "ano", "duracao_min", "classificacao", "sinopse")}
    if not all(dados.values()) or dados["tipo"] not in TIPOS:
        flash("Preencha todos os campos obrigatórios do filme.", "erro")
        return redirect(url_for("admin_painel"))
    video = request.files.get("video")
    capa = request.files.get("capa")
    if not video or not video.filename:
        flash("Selecione um arquivo de vídeo para publicar o título.", "erro")
        return redirect(url_for("admin_painel"))
    if not video.filename.lower().endswith((".mp4", ".webm", ".ogg", ".mov", ".m4v")):
        flash("Formato de vídeo não suportado. Use MP4, WebM, OGG ou MOV.", "erro")
        return redirect(url_for("admin_painel"))
    video_name = f"{uuid4().hex}{Path(video.filename).suffix.lower()}"
    video.save(UPLOAD_DIR / video_name)
    capa_url = "/static/img/capa-nao-encontrada.svg"
    if capa and capa.filename:
        if capa.filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            capa_name = f"{uuid4().hex}{Path(capa.filename).suffix.lower()}"
            capa.save(UPLOAD_DIR / capa_name)
            capa_url = f"/static/uploads/{capa_name}"
        else:
            flash("Capa ignorada: use JPG, PNG ou WebP. Foi aplicada a imagem padrão.", "erro")
    try:
        TituloRepo.criar(dados, capa_url, f"/static/uploads/{video_name}")
        flash("Título publicado na biblioteca.", "ok")
    except (ValueError, mysql.connector.Error):
        (UPLOAD_DIR / video_name).unlink(missing_ok=True)
        flash("Não foi possível cadastrar o título. Confira os dados informados.", "erro")
    return redirect(url_for("admin_painel"))




@app.post("/admin/filmes/<int:tid>/visibilidade")
@admin_required
def admin_visibilidade_titulo(tid):
    t = TituloRepo.por_id(tid) or abort(404)
    ativo = request.form.get("visivel") == "1"
    if ativo and not t.get("video_url"):
        flash("Adicione um vídeo antes de tornar este título visível na biblioteca.", "erro")
    else:
        TituloRepo.alterar_visibilidade(tid, ativo)
        flash("Título exibido na biblioteca." if ativo else "Título ocultado da biblioteca.", "ok")
    return redirect(url_for("admin_painel"))


@app.post("/admin/filmes/<int:tid>/destaque")
@admin_required
def admin_destaque_titulo(tid):
    t = TituloRepo.por_id(tid) or abort(404)
    ativo = request.form.get("destaque") == "1"
    if ativo and (not t.get("video_url") or not t.get("visivel", 1)):
        flash("O destaque precisa estar visível e ter um vídeo hospedado.", "erro")
    else:
        TituloRepo.definir_destaque(tid, ativo)
        flash("Destaque da página inicial atualizado.", "ok")
    return redirect(url_for("admin_painel"))


@app.post("/admin/filmes/<int:tid>/video")
@admin_required
def admin_adicionar_video(tid):
    t = TituloRepo.por_id(tid) or abort(404)
    video = request.files.get("video")
    if not video or not video.filename:
        flash("Selecione um arquivo de vídeo.", "erro")
    elif not video.filename.lower().endswith((".mp4", ".webm", ".ogg", ".mov", ".m4v")):
        flash("Formato não suportado. Use MP4, WebM, OGG ou MOV.", "erro")
    else:
        video_name = f"{uuid4().hex}{Path(video.filename).suffix.lower()}"
        video.save(UPLOAD_DIR / video_name)
        TituloRepo.adicionar_video(tid, f"/static/uploads/{video_name}")
        flash(f"Vídeo adicionado a ‘{t['titulo']}’. O título agora está visível na biblioteca.", "ok")
    return redirect(url_for("admin_painel"))


@app.post("/admin/filmes/<int:tid>/excluir")
@admin_required
def admin_excluir_titulo(tid):
    TituloRepo.excluir(tid)
    flash("Título removido do catálogo.", "ok")
    return redirect(url_for("admin_painel"))


if __name__ == "__main__":
    app.run(debug=True)
