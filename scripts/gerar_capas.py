"""Gera capas (600x900) e banners (1600x700) originais para os títulos do seed.

Uso (opcional, as imagens já vêm prontas no projeto):
    pip install pillow numpy
    python scripts/gerar_capas.py
"""
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

RAIZ = Path(__file__).resolve().parent.parent / "static" / "img"
FORMATOS = {"capas": (600, 900, 0.5), "banners": (1600, 700, 0.74)}  # largura, altura, foco x


def rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)


class Caneta:
    """Envolve o ImageDraw: formas sem 'outline' são preenchidas por padrão."""

    def __init__(self, d):
        self._d = d

    def __getattr__(self, nome):
        f = getattr(self._d, nome)

        def chamar(*a, **k):
            if nome != "line" and "fill" not in k and "outline" not in k:
                k["fill"] = 255
            return f(*a, **k)
        return chamar


class Tela:
    def __init__(self, w, h, foco, c1, c2, seed):
        self.w, self.h, self.cx = w, h, w * foco
        self.u = h  # unidade de escala
        self.rng = random.Random(seed)
        t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
        self.px = rgb(c1) * (1 - t) + rgb(c2) * t
        self.px = np.repeat(self.px, w, axis=1)

    def forma(self, fn, cor, alpha=1.0, blur=0):
        m = Image.new("L", (self.w, self.h), 0)
        fn(Caneta(ImageDraw.Draw(m)))
        if blur:
            m = m.filter(ImageFilter.GaussianBlur(blur))
        a = (np.asarray(m, dtype=np.float32) / 255.0 * alpha)[:, :, None]
        self.px = self.px * (1 - a) + rgb(cor) * a

    def brilho(self, x, y, r, cor, forca=1.0):
        yy, xx = np.mgrid[0:self.h, 0:self.w].astype(np.float32)
        d = np.sqrt((xx - x) ** 2 + (yy - y) ** 2) / r
        a = (np.clip(1 - d, 0, 1) ** 2 * forca)[:, :, None]
        self.px = self.px * (1 - a) + rgb(cor) * a

    def finalizar(self):
        yy, xx = np.mgrid[0:self.h, 0:self.w].astype(np.float32)
        d = np.sqrt(((xx - self.w / 2) / self.w) ** 2 + ((yy - self.h / 2) / self.h) ** 2)
        self.px *= (1 - np.clip(d - 0.25, 0, 1) * 1.1)[:, :, None]
        self.px += np.random.default_rng(1).normal(0, 3.5, self.px.shape).astype(np.float32)
        return Image.fromarray(np.clip(self.px, 0, 255).astype(np.uint8))


# ---------- motivos ----------
def sessao(t):  # projetor numa sala escura
    u, cx = t.u, t.cx
    fonte = (cx, 0.14 * u)
    t.forma(lambda d: d.polygon([fonte, (cx - 0.55 * u, 0.9 * u), (cx + 0.55 * u, 0.9 * u)]), "#FF2D3F", .45, 18)
    t.brilho(*fonte, 0.18 * u, "#FFFFFF", .9)
    t.forma(lambda d: d.rectangle([cx - .3 * u, .55 * u, cx + .3 * u, .8 * u]), "#FFD9DC", .35, 6)
    for fila, (y, esc) in enumerate(((0.8, .07), (0.9, .09), (1.02, .12))):
        for i in range(-9, 10):
            x = cx + i * esc * u * 1.25 + (fila % 2) * esc * u * .6
            t.forma(lambda d, x=x, y=y, e=esc: (d.ellipse([x - e * u * .45, y * u - e * u * 1.1, x + e * u * .45, y * u - e * u * .2]),
                                              d.rounded_rectangle([x - e * u * .8, y * u - e * u * .3, x + e * u * .8, y * u + e * u * 1.4], 14, fill=255)),
                    "#050003", 1)


def feixe(t):  # feixe no céu sobre uma cidade
    u, cx = t.u, t.cx
    t.forma(lambda d: d.polygon([(cx - .03 * u, 0), (cx + .03 * u, 0), (cx + .22 * u, .75 * u), (cx - .22 * u, .75 * u)]), "#FF6A7A", .55, 14)
    t.brilho(cx, .75 * u, .5 * u, "#FF2D3F", .8)
    x = -20
    while x < t.w + 20:
        w, h = t.rng.randint(int(.05 * u), int(.11 * u)), t.rng.randint(int(.08 * u), int(.28 * u))
        t.forma(lambda d, x=x, w=w, h=h: d.rectangle([x, .86 * u - h, x + w, u]), "#050003", 1)
        for _ in range(3):
            wx, wy = x + t.rng.randint(4, max(5, w - 8)), .86 * u - t.rng.randint(8, max(9, h - 8))
            t.forma(lambda d, wx=wx, wy=wy: d.rectangle([wx, wy, wx + 5, wy + 7]), "#FFC857", .9)
        x += w + t.rng.randint(0, 8)


def casa(t):  # casa à noite
    u, cx = t.u, t.cx
    t.brilho(cx + .3 * u, .2 * u, .22 * u, "#FFE9C7", .9)
    t.forma(lambda d: d.ellipse([cx + .26 * u, .16 * u, cx + .34 * u, .24 * u]), "#FFF6E0", 1, 1)
    t.forma(lambda d: (d.rectangle([cx - .28 * u, .52 * u, cx + .28 * u, .86 * u]), d.polygon([(cx - .34 * u, .52 * u), (cx, .32 * u), (cx + .34 * u, .52 * u)])), "#07040a", 1)
    for wx, wy in ((-.18, .6), (.08, .6), (-.05, .72)):
        t.brilho(cx + wx * u + .05 * u, wy * u + .05 * u, .22 * u, "#FFB347", .6)
        t.forma(lambda d, wx=wx, wy=wy: d.rectangle([cx + wx * u, wy * u, cx + wx * u + .1 * u, wy * u + .1 * u]), "#FFC857", 1)
    t.forma(lambda d: d.rectangle([0, .86 * u, t.w, u]), "#040206", 1)


def terraco(t):  # terraço com telão e luzinhas
    u, cx = t.u, t.cx
    t.forma(lambda d: d.rectangle([cx - .3 * u, .3 * u, cx + .3 * u, .6 * u]), "#FFF3E6", .9, 3)
    t.brilho(cx, .45 * u, .6 * u, "#FF8A3D", .45)
    for i in range(24):
        x = i / 23 * t.w
        y = .14 * u + math.sin(i / 23 * math.pi) * .08 * u
        t.brilho(x, y, .035 * u, "#FFD27A", 1)
    t.forma(lambda d: d.rectangle([0, .82 * u, t.w, u]), "#0a0305", 1)
    for dx in (-.28, -.1, .12, .3):
        x = cx + dx * u
        t.forma(lambda d, x=x: (d.ellipse([x - .03 * u, .72 * u, x + .03 * u, .78 * u]), d.rounded_rectangle([x - .05 * u, .77 * u, x + .05 * u, .9 * u], 12, fill=255)), "#0a0305", 1)


def pixels(t):  # mosaico de pixels e um robô
    u, cx = t.u, t.cx
    s = int(.045 * u)
    for gx in range(0, t.w, s):
        for gy in range(0, int(.7 * u), s):
            if t.rng.random() < .45 * (1 - gy / (.75 * u)):
                cor = t.rng.choice(["#FF2D3F", "#FF6A7A", "#7A0A14", "#FFB347"])
                t.forma(lambda d, gx=gx, gy=gy: d.rectangle([gx + 2, gy + 2, gx + s - 2, gy + s - 2]), cor, .85)
    t.brilho(cx, .72 * u, .3 * u, "#FF2D3F", .7)
    t.forma(lambda d: d.ellipse([cx - .2 * u, .6 * u, cx + .2 * u, .84 * u]), "#1a1a1d", 1, 1)
    t.forma(lambda d: d.ellipse([cx - .09 * u, .69 * u, cx + .09 * u, .75 * u]), "#FF2D3F", 1, 1)


def quadro(t):  # tira de filme inclinada
    u = t.u
    comp, alt = int(t.w * 1.5), int(.36 * u)
    tira = Tela(comp, alt, .5, "#0b0b0d", "#0b0b0d", 3)
    n = 5
    for i in range(n):
        x0 = i * comp / n + 30
        f = Tela(int(comp / n - 60), int(alt * .62), .5, ["#FF2D3F", "#7A0A14", "#FFB347", "#B3121F", "#D61F8C"][i], "#140004", i)
        f.brilho(f.w * .5, f.h * .6, f.w * .5, "#FFE9C7", .5)
        tira.px[int(alt * .19):int(alt * .19) + f.h, int(x0):int(x0) + f.w] = f.px
    for i in range(0, comp, 34):
        for y in (int(alt * .06), int(alt * .86)):
            tira.px[y:y + 10, i:i + 16] = 220
    img = Image.fromarray(np.clip(tira.px, 0, 255).astype(np.uint8)).convert("RGBA").rotate(-12, expand=True, resample=Image.BICUBIC)
    base = Image.fromarray(np.clip(t.px, 0, 255).astype(np.uint8)).convert("RGBA")
    base.alpha_composite(img, (int(t.cx - img.width / 2), int(.5 * u - img.height / 2)))
    t.px = np.asarray(base.convert("RGB"), dtype=np.float32)
    t.brilho(t.cx, .5 * u, .5 * u, "#FF2D3F", .25)


def corredor(t):  # perspectiva até uma luz no fundo
    u, cx = t.u, t.cx
    vx, vy = cx, .46 * u
    t.forma(lambda d: d.polygon([(0, 0), (vx - .05 * u, vy - .04 * u), (vx - .05 * u, vy + .06 * u), (0, t.h)]), "#12030a", 1)
    t.forma(lambda d: d.polygon([(t.w, 0), (vx + .05 * u, vy - .04 * u), (vx + .05 * u, vy + .06 * u), (t.w, t.h)]), "#12030a", 1)
    t.forma(lambda d: d.polygon([(0, t.h), (vx - .05 * u, vy + .06 * u), (vx + .05 * u, vy + .06 * u), (t.w, t.h)]), "#1c0508", 1)
    for k in range(1, 6):
        p = k / 6
        x = vx - (.45 - .4 * p) * t.w * (1 - p * .5)
        t.forma(lambda d, p=p: d.rectangle([vx - (.34 - .3 * p) * u * 1.5 - .2 * u * (1 - p), vy - .1 * u * (1 - p), vx - (.34 - .3 * p) * u * 1.5 - .1 * u * (1 - p), vy + .08 * u * (1 - p) + .12 * u]), "#050003", .8)
    t.brilho(vx, vy + .02 * u, .55 * u, "#FF2D3F", .95)
    t.brilho(vx, vy + .02 * u, .12 * u, "#FFFFFF", 1)


def tempo(t):  # anéis de relógio
    u, cx = t.u, t.cx
    cy = .46 * u
    for i, r in enumerate((.42, .32, .22)):
        t.forma(lambda d, r=r: d.ellipse([cx - r * u, cy - r * u, cx + r * u, cy + r * u], outline=255, width=max(2, int(.006 * u))), "#FF6A7A", .7 - i * .15)
    for k in range(60):
        a = k / 60 * 2 * math.pi
        r1, r2 = .42 * u, (.45 if k % 5 == 0 else .435) * u
        t.forma(lambda d, a=a, r1=r1, r2=r2: d.line([cx + r1 * math.cos(a), cy + r1 * math.sin(a), cx + r2 * math.cos(a), cy + r2 * math.sin(a)], fill=255, width=3), "#FFE9C7", .8)
    for a, r in ((-1.2, .3), (.5, .2)):
        t.forma(lambda d, a=a, r=r: d.line([cx, cy, cx + r * u * math.cos(a), cy + r * u * math.sin(a)], fill=255, width=int(.012 * u)), "#FFFFFF", .95)
    t.brilho(cx, cy, .5 * u, "#FF2D3F", .45)


def conectado(t):  # rede de dispositivos
    u, cx = t.u, t.cx
    pts = [(cx, .46 * u)] + [(cx + math.cos(a) * r * u, .46 * u + math.sin(a) * r * u)
                             for r in (.22, .38) for a in [t.rng.uniform(0, 6.28) + k * 6.28 / 7 for k in range(7)]]
    for i, p in enumerate(pts):
        for q in pts[:i]:
            if math.dist(p, q) < .3 * u:
                t.forma(lambda d, p=p, q=q: d.line([*p, *q], fill=255, width=2), "#FF6A7A", .6)
    for p in pts:
        t.brilho(*p, .05 * u, "#FF2D3F", 1)
    t.brilho(cx, .46 * u, .3 * u, "#FFFFFF", .5)


def escuro(t):  # lua e sombra
    u, cx = t.u, t.cx
    t.brilho(cx, .42 * u, .55 * u, "#FF2D3F", .35)
    t.forma(lambda d: d.ellipse([cx - .25 * u, .17 * u, cx + .25 * u, .67 * u]), "#FFE9E9", 1, 1)
    t.forma(lambda d: d.ellipse([cx - .12 * u, .13 * u, cx + .36 * u, .65 * u]), "#12030a", 1, 1)
    t.forma(lambda d: d.rectangle([0, .8 * u, t.w, u]), "#040206", 1)


def oceano(t):  # raios de luz e bolhas
    u, cx = t.u, t.cx
    for k in range(5):
        x = cx + (k - 2) * .14 * u
        t.forma(lambda d, x=x: d.polygon([(x - .02 * u, 0), (x + .02 * u, 0), (x + .22 * u, u), (x - .12 * u, u)]), "#7FC8FF", .16, 12)
    for _ in range(40):
        x, y, r = t.rng.uniform(0, t.w), t.rng.uniform(.1 * u, u), t.rng.uniform(.006, .02) * u
        t.forma(lambda d, x=x, y=y, r=r: d.ellipse([x - r, y - r, x + r, y + r], outline=255, width=2), "#BFE4FF", .5)
    t.brilho(cx, .5 * u, .22 * u, "#7FC8FF", .8)
    t.forma(lambda d: d.ellipse([cx - .12 * u, .4 * u, cx + .12 * u, .56 * u]), "#CFEBFF", .85, 6)
    for i in range(7):
        x = cx - .1 * u + i * .033 * u
        t.forma(lambda d, x=x: d.line([x, .5 * u, x + 8 * math.sin(x), .74 * u], fill=255, width=3), "#CFEBFF", .5, 2)
    t.forma(lambda d: d.polygon([(0, u), (0, .9 * u), (t.w * .3, .93 * u), (t.w * .6, .88 * u), (t.w, .92 * u), (t.w, u)]), "#020a14", 1)


def show(t):  # palco com holofotes e plateia
    u, cx = t.u, t.cx
    for i, cor in enumerate(("#FF2D3F", "#FFFFFF", "#FF6AC8")):
        x = cx + (i - 1) * .3 * u
        t.forma(lambda d, x=x: d.polygon([(x, 0), (cx - .55 * u + (x - cx), .78 * u), (cx + .55 * u + (x - cx), .78 * u)]), cor, .22, 16)
    t.brilho(cx, .72 * u, .4 * u, "#FF2D3F", .7)
    t.forma(lambda d: d.rectangle([0, .78 * u, t.w, u]), "#2a0a14", 1)
    for i in range(-12, 13):
        x = cx + i * .07 * u + t.rng.uniform(-8, 8)
        y = .86 * u + t.rng.uniform(0, .08) * u
        t.forma(lambda d, x=x, y=y: (d.ellipse([x - .03 * u, y - .06 * u, x + .03 * u, y]), d.rounded_rectangle([x - .05 * u, y - .01 * u, x + .05 * u, y + .2 * u], 14, fill=255)), "#000000", 1)


def standup(t):  # holofote sobre um microfone
    u, cx = t.u, t.cx
    t.forma(lambda d: d.polygon([(cx, 0), (cx - .38 * u, .86 * u), (cx + .38 * u, .86 * u)]), "#FFE0B0", .3, 14)
    t.brilho(cx, .86 * u, .38 * u, "#FF8A3D", .7)
    t.forma(lambda d: (d.line([cx, .4 * u, cx, .84 * u], fill=255, width=6), d.ellipse([cx - .03 * u, .34 * u, cx + .03 * u, .42 * u], fill=255),
                       d.line([cx - .1 * u, .85 * u, cx + .1 * u, .85 * u], fill=255, width=6)), "#050305", 1)
    t.forma(lambda d: d.rectangle([0, .86 * u, t.w, u]), "#0a0305", 1)


MOTIVOS = dict(sessao=sessao, feixe=feixe, casa=casa, terraco=terraco, pixels=pixels, quadro=quadro,
               corredor=corredor, tempo=tempo, conectado=conectado, escuro=escuro, oceano=oceano, show=show, standup=standup)

# slug: (cor topo, cor base, motivo)
TITULOS = {
    "ultima-sessao": ("#4A0A18", "#050003", "sessao"),
    "feixe-de-luz": ("#1b0a2e", "#7A0A14", "feixe"),
    "casa-aberta": ("#101a3a", "#07040a", "casa"),
    "sala-7": ("#7A1A2A", "#FF8A3D", "terraco"),
    "pixels-de-domingo": ("#12060c", "#4A0A18", "pixels"),
    "quadro-a-quadro": ("#2a0509", "#050003", "quadro"),
    "corredor-escuro": ("#050003", "#2a0509", "corredor"),
    "linha-do-tempo": ("#16091f", "#3b0a12", "tempo"),
    "mundo-conectado": ("#0b0b12", "#3b0a12", "conectado"),
    "a-arte-do-escuro": ("#1a0a14", "#050003", "escuro"),
    "oceano-profundo": ("#0b3a6a", "#020a14", "oceano"),
    "noite-de-estreia": ("#2a0518", "#050003", "show"),
    "stand-up-no-terraco": ("#2a0f08", "#050305", "standup"),
}


def main():
    for pasta, (w, h, foco) in FORMATOS.items():
        (RAIZ / pasta).mkdir(parents=True, exist_ok=True)
        for i, (slug, (c1, c2, motivo)) in enumerate(TITULOS.items()):
            t = Tela(w, h, foco, c1, c2, i + 7)
            MOTIVOS[motivo](t)
            t.finalizar().save(RAIZ / pasta / f"{slug}.jpg", quality=86)
            print(pasta, slug)


if __name__ == "__main__":
    main()
