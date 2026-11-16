"""Trailers locais e créditos dos projetos abertos do Blender."""

VIDEOS_DEMO = (
    {
        "titulo": "Big Buck Bunny — Trailer",
        "genero": "Animação",
        "ano": 2008,
        "duracao_min": 1,
        "sinopse": "Um coelho tranquilo enfrenta três pequenos valentões da floresta. Trailer da animação Big Buck Bunny, sem diálogos.",
        "cor1": "#355C35",
        "cor2": "#101D20",
        "capa_url": "/static/img/demos/big-buck-bunny.svg",
        "video_url": "/static/videos/big-buck-bunny-trailer.mp4",
        "autoria": "© 2008 Blender Foundation / www.bigbuckbunny.org",
        "fonte": "https://peach.blender.org/about/",
        "licenca": "CC BY 3.0",
        "licenca_url": "https://creativecommons.org/licenses/by/3.0/",
    },
    {
        "titulo": "Sintel — Trailer",
        "genero": "Fantasia",
        "ano": 2010,
        "duracao_min": 1,
        "sinopse": "Uma jovem percorre um mundo de fantasia em busca de um pequeno dragão. Trailer de Sintel, em áudio original.",
        "cor1": "#4B335D",
        "cor2": "#151E30",
        "capa_url": "/static/img/demos/sintel.svg",
        "video_url": "/static/videos/sintel-trailer.mp4",
        "autoria": "© Blender Foundation | durian.blender.org",
        "fonte": "https://durian.blender.org/sharing/",
        "licenca": "CC BY 3.0",
        "licenca_url": "https://creativecommons.org/licenses/by/3.0/",
    },
    {
        "titulo": "Elephants Dream — Teaser",
        "genero": "Ficção científica",
        "ano": 2006,
        "duracao_min": 1,
        "sinopse": "Dois personagens exploram uma máquina misteriosa em um universo surreal. Teaser de Elephants Dream, em áudio original.",
        "cor1": "#77513A",
        "cor2": "#111B24",
        "capa_url": "/static/img/demos/elephants-dream.svg",
        "video_url": "/static/videos/elephants-dream-teaser-h264.mp4",
        "video_url_anterior": "/static/videos/elephants-dream-teaser.mp4",
        "autoria": "© 2006 Blender Foundation / Netherlands Media Art Institute / www.elephantsdream.org",
        "fonte": "https://orange.blender.org/blog/creative-commons-license/",
        "licenca": "CC BY 2.5",
        "licenca_url": "https://creativecommons.org/licenses/by/2.5/",
    },
)

CREDITOS_POR_VIDEO = {video["video_url"]: video for video in VIDEOS_DEMO}


def adicionar_videos(cursor):
    """Acrescenta os trailers sem substituir títulos ou repetir importações."""
    adicionados = 0
    for video in VIDEOS_DEMO:
        if anterior := video.get("video_url_anterior"):
            cursor.execute(
                "UPDATE titulos SET video_url=%s WHERE video_url=%s",
                (video["video_url"], anterior),
            )
        cursor.execute(
            """INSERT INTO titulos
               (titulo, tipo, genero, ano, duracao_min, classificacao, sinopse,
                cor1, cor2, capa_url, banner_url, video_url, destaque)
               SELECT %s, 'filme', %s, %s, %s, 'NR', %s, %s, %s, %s, %s, %s, 0
               WHERE NOT EXISTS (
                   SELECT 1 FROM titulos WHERE video_url=%s OR titulo=%s
               )""",
            (
                video["titulo"], video["genero"], video["ano"], video["duracao_min"],
                video["sinopse"], video["cor1"], video["cor2"], video["capa_url"],
                video["capa_url"], video["video_url"], video["video_url"], video["titulo"],
            ),
        )
        adicionados += cursor.rowcount
    return adicionados
