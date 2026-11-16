"""Repositórios: cada classe cuida das consultas de uma tabela."""
from database import Database as DB

TIPOS = {
    "filme": "Filmes",
    "serie": "Séries",
    "documentario": "Documentários",
    "show_ao_vivo": "Shows ao vivo",
}
TIPO_SINGULAR = {"filme": "Filme", "serie": "Série", "documentario": "Documentário", "show_ao_vivo": "Show ao vivo"}


class UsuarioRepo:
    @staticmethod
    def por_id(uid):
        return DB.consultar("SELECT id, nome, email, is_admin FROM usuarios WHERE id=%s", (uid,), um=True)

    @staticmethod
    def por_email(email):
        return DB.consultar("SELECT * FROM usuarios WHERE email=%s", (email,), um=True)

    @staticmethod
    def criar(nome, email, senha_hash, is_admin=0):
        return DB.executar(
            "INSERT INTO usuarios (nome, email, senha_hash, is_admin) VALUES (%s,%s,%s,%s)",
            (nome, email, senha_hash, is_admin),
        )

    @staticmethod
    def listar():
        return DB.consultar("SELECT id, nome, email, is_admin, criado_em FROM usuarios ORDER BY criado_em DESC")

    @staticmethod
    def excluir(uid):
        DB.executar("DELETE FROM usuarios WHERE id=%s", (uid,))

    @staticmethod
    def alterar_admin(uid, ativo):
        DB.executar("UPDATE usuarios SET is_admin=%s WHERE id=%s", (1 if ativo else 0, uid))


class TituloRepo:
    @staticmethod
    def por_id(tid):
        return DB.consultar("SELECT * FROM titulos WHERE id=%s", (tid,), um=True)

    @staticmethod
    def destaques():
        return DB.consultar("SELECT * FROM titulos WHERE visivel=1 AND video_url IS NOT NULL AND video_url<>'' ORDER BY destaque DESC, id DESC LIMIT 1")

    @staticmethod
    def com_video():
        return DB.consultar(
            "SELECT * FROM titulos WHERE visivel=1 AND video_url IS NOT NULL AND video_url<>'' ORDER BY id DESC"
        )

    @staticmethod
    def listar(tipo=None, busca=None):
        sql, params = "SELECT * FROM titulos WHERE visivel=1 AND video_url IS NOT NULL AND video_url<>''", []
        if tipo in TIPOS:
            sql += " AND tipo=%s"
            params.append(tipo)
        if busca:
            sql += " AND (titulo LIKE %s OR genero LIKE %s OR sinopse LIKE %s)"
            params += [f"%{busca}%"] * 3
        return DB.consultar(sql + " ORDER BY titulo", tuple(params))

    @staticmethod
    def listar_admin():
        return DB.consultar("SELECT * FROM titulos ORDER BY criado_em DESC")

    @staticmethod
    def criar(dados, capa_url, video_url):
        ano = int(dados["ano"])
        duracao = int(dados["duracao_min"])
        if not (1888 <= ano <= 2100) or not (1 <= duracao <= 2000):
            raise ValueError("Ano ou duração inválidos")
        return DB.executar(
            """INSERT INTO titulos (titulo,tipo,genero,ano,duracao_min,classificacao,sinopse,capa_url,banner_url,video_url)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (dados["titulo"], dados["tipo"], dados["genero"], ano, duracao,
             dados["classificacao"][:3], dados["sinopse"], capa_url, capa_url, video_url),
        )

    @staticmethod
    def alterar_visibilidade(tid, ativo):
        DB.executar("UPDATE titulos SET visivel=%s WHERE id=%s", (1 if ativo else 0, tid))

    @staticmethod
    def definir_destaque(tid, ativo):
        # Há apenas um destaque ativo por vez; ao remover, limpa o destaque atual.
        DB.executar("UPDATE titulos SET destaque=0")
        if ativo:
            DB.executar("UPDATE titulos SET destaque=1 WHERE id=%s", (tid,))

    @staticmethod
    def adicionar_video(tid, video_url):
        DB.executar("UPDATE titulos SET video_url=%s, visivel=1 WHERE id=%s", (video_url, tid))

    @staticmethod
    def excluir(tid):
        DB.executar("DELETE FROM titulos WHERE id=%s", (tid,))

    @staticmethod
    def parecidos(titulo, limite=8):
        return DB.consultar(
            """SELECT * FROM titulos WHERE id<>%s AND visivel=1 AND video_url IS NOT NULL AND video_url<>''
               ORDER BY (tipo=%s) DESC, (genero=%s) DESC, ano DESC LIMIT %s""",
            (titulo["id"], titulo["tipo"], titulo["genero"], limite),
        )

    @staticmethod
    def continuar(uid, limite=10):
        return DB.consultar(
            """SELECT t.*, p.segundo_atual, p.pct
               FROM progresso p JOIN titulos t ON t.id = p.titulo_id
               WHERE p.usuario_id=%s AND p.segundo_atual >= 10 AND p.pct < 95
                 AND t.visivel=1 AND t.video_url IS NOT NULL AND t.video_url<>'' 
               ORDER BY p.atualizado_em DESC LIMIT %s""",
            (uid, limite),
        )


class FavoritoRepo:
    @staticmethod
    def existe(uid, tid):
        return DB.consultar(
            "SELECT 1 AS ok FROM favoritos WHERE usuario_id=%s AND titulo_id=%s", (uid, tid), um=True
        ) is not None

    @staticmethod
    def alternar(uid, tid):
        if FavoritoRepo.existe(uid, tid):
            DB.executar("DELETE FROM favoritos WHERE usuario_id=%s AND titulo_id=%s", (uid, tid))
            return False
        DB.executar("INSERT INTO favoritos (usuario_id, titulo_id) VALUES (%s,%s)", (uid, tid))
        return True

    @staticmethod
    def listar(uid):
        return DB.consultar(
            """SELECT t.* FROM favoritos f JOIN titulos t ON t.id=f.titulo_id
               WHERE f.usuario_id=%s AND t.visivel=1 AND t.video_url IS NOT NULL AND t.video_url<>'' ORDER BY f.criado_em DESC""",
            (uid,),
        )


class ProgressoRepo:
    @staticmethod
    def obter(uid, tid):
        return DB.consultar(
            "SELECT segundo_atual, pct FROM progresso WHERE usuario_id=%s AND titulo_id=%s", (uid, tid), um=True
        )

    @staticmethod
    def salvar(uid, tid, segundo, pct):
        DB.executar(
            """INSERT INTO progresso (usuario_id, titulo_id, segundo_atual, pct) VALUES (%s,%s,%s,%s)
               ON DUPLICATE KEY UPDATE segundo_atual=%s, pct=%s""",
            (uid, tid, segundo, pct, segundo, pct),
        )


class HistoricoRepo:
    @staticmethod
    def registrar(uid, tid):
        DB.executar("INSERT INTO visualizacoes (usuario_id, titulo_id) VALUES (%s,%s)", (uid, tid))

    @staticmethod
    def recentes(uid, limite=8):
        return DB.consultar(
            """SELECT v.iniciada_em, t.id AS titulo_id, t.titulo, t.tipo
               FROM visualizacoes v JOIN titulos t ON t.id=v.titulo_id
               WHERE v.usuario_id=%s AND t.visivel=1 AND t.video_url IS NOT NULL AND t.video_url<>'' ORDER BY v.iniciada_em DESC LIMIT %s""",
            (uid, limite),
        )

    @staticmethod
    def estatisticas(uid):
        return DB.consultar(
            """SELECT
                 (SELECT COUNT(*) FROM visualizacoes WHERE usuario_id=%s) AS sessoes,
                 (SELECT COUNT(DISTINCT titulo_id) FROM visualizacoes WHERE usuario_id=%s) AS titulos,
                 (SELECT COALESCE(SUM(segundo_atual),0) DIV 60 FROM progresso WHERE usuario_id=%s) AS minutos""",
            (uid, uid, uid), um=True,
        )
