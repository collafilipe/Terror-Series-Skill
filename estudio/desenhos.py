"""
Desenhos vetoriais feitos por codigo: bonequinho articulado animado + objetos.
Tudo e desenhado em 2x e reduzido (bordas suaves).
"""

import math
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

FONT = None  # definido por quem importa (caminho da fonte .ttf)
OUT = (22, 22, 28)          # contorno
SKIN = (246, 205, 166)
SS = 2                       # supersampling


def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def _font(size):
    return ImageFont.truetype(FONT, max(8, int(size)))


# ============================================================ BONEQUINHO
TIPOS = {
    #  tipo        cor da roupa  acessorios
    "rei":        ("#6a2c91", ["coroa", "barba", "capa"]),
    "rainha":     ("#c2185b", ["cabelo_longo", "coroa", "capa"]),
    "soldado":    ("#4b5d2a", ["capacete"]),
    "romano":     ("#b3261e", ["capacete_romano"]),
    "cavaleiro":  ("#8a8f99", ["elmo"]),
    "viking":     ("#7a4b2a", ["capacete_viking", "barba"]),
    "pirata":     ("#2b2b2b", ["bandana", "tapa_olho", "barba"]),
    "marinheiro": ("#1d3f72", ["chapeu_tricornio"]),
    "explorador": ("#9c6b30", ["chapeu_explorador"]),
    "papa":       ("#efe6d0", ["mitra"]),
    "farao":      ("#e0b33a", ["nemes"]),
    "cientista":  ("#f4f4f4", ["oculos", "cabelo_maluco"]),
    "policial":   ("#1f3a68", ["quepe"]),
    "ladrao":     ("#262626", ["mascara", "gorro"]),
    "trabalhador": ("#f08a24", ["capacete_obra"]),
    "homem":      ("#3a7bd5", ["cabelo_curto"]),
    "mulher":     ("#e0457b", ["cabelo_longo"]),
    "crianca":    ("#2bb673", ["cabelo_curto"]),
    "velho":      ("#7d8597", ["careca", "barba_branca"]),
    "velha":      ("#9c6ade", ["cabelo_coque"]),
    "presidente": ("#22252e", ["cabelo_curto", "gravata"]),
}

ACOES = ["parado", "andar", "correr", "acenar", "apontar", "pular", "susto", "comemorar",
         "triste", "cair", "pensar", "lutar", "empurrar", "falar"]
EMOCOES = ["neutro", "feliz", "triste", "bravo", "assustado", "surpreso"]

# comprimentos (1x)
COXA, CANELA, TRONCO, BRACO, ANTEBRACO, CABECA = 92, 92, 150, 82, 76, 52
LARG_MEMBRO, LARG_TRONCO, CONTORNO = 22, 40, 6


def pose(acao, t):
    """Angulos em graus (0 = para baixo, positivo = para frente)."""
    p = dict(tl=5, kl=0, tr=-5, kr=0, af=12, ef=10, ab=-10, eb=10, tilt=0, dy=0, rot=0, shake=0)
    s = math.sin
    if acao == "andar":
        f = 2 * math.pi * 1.7 * t
        p.update(tl=28 * s(f), tr=-28 * s(f), kl=8 + 30 * max(0, -s(f + 1.2)), kr=8 + 30 * max(0, s(f + 1.2)),
                 af=-26 * s(f), ab=26 * s(f), ef=22, eb=22, dy=-7 * abs(math.cos(f)))
    elif acao == "correr":
        f = 2 * math.pi * 2.7 * t
        p.update(tl=48 * s(f), tr=-48 * s(f), kl=20 + 60 * max(0, -s(f + 1.0)), kr=20 + 60 * max(0, s(f + 1.0)),
                 af=-55 * s(f), ab=55 * s(f), ef=85, eb=85, tilt=14, dy=-16 * abs(math.cos(f)))
    elif acao == "acenar":
        p.update(af=150 + 22 * s(2 * math.pi * 2.2 * t), ef=25, ab=-8, dy=2 * s(t * 3))
    elif acao == "apontar":
        p.update(af=88, ef=0, ab=-6, tilt=-3, dy=2 * s(t * 3))
    elif acao == "pular":
        c = (t * 1.1) % 1.0
        no_ar = 0.25 < c < 0.85
        h = math.sin(math.pi * (c - 0.25) / 0.6) if no_ar else 0
        agach = 0 if no_ar else (1 - abs((c if c <= 0.25 else c - 1) / 0.25)) if c <= 0.25 or c >= 0.85 else 0
        p.update(dy=-230 * h + 30 * agach, tl=10 + 25 * agach, kl=50 * agach + 10 * h, tr=-5 + 25 * agach,
                 kr=50 * agach + 25 * h, af=150 * h + 20, ab=140 * h - 10, ef=10, eb=10)
    elif acao == "susto":
        p.update(af=155 + 8 * s(t * 30), ab=150 + 8 * s(t * 33), ef=15, eb=15, tl=18, tr=-18, tilt=-8,
                 shake=6 * s(t * 45))
    elif acao == "comemorar":
        f = 2 * math.pi * 1.6 * t
        p.update(af=160 + 15 * s(f), ab=160 - 15 * s(f), ef=10, eb=10, dy=-70 * abs(s(f / 2)),
                 kl=15 * abs(s(f / 2)), kr=15 * abs(s(f / 2)))
    elif acao == "triste":
        p.update(af=4, ab=-4, ef=5, eb=5, tilt=14, dy=6 + 3 * s(t * 1.5))
    elif acao == "cair":
        k = min(1.0, t / 0.55)
        k = 1 - (1 - k) ** 3
        p.update(rot=-88 * k, af=120 * (1 - k) + 20, ab=150 * (1 - k), tl=10, tr=-20)
    elif acao == "pensar":
        p.update(af=35, ef=135, ab=25, eb=95, tilt=-4, dy=2 * s(t * 2))
    elif acao == "lutar":
        f = (t * 2.2) % 1.0
        soco = math.sin(math.pi * min(1, f / 0.35)) if f < 0.35 else 0
        p.update(af=70 + 20 * soco, ef=95 * (1 - soco), ab=60, eb=110, tl=22, tr=-22, kl=15, kr=10,
                 tilt=6 + 6 * soco)
    elif acao == "empurrar":
        f = 2 * math.pi * 1.0 * t
        p.update(af=85, ef=10, ab=80, eb=15, tilt=22, tl=20 * s(f) - 5, tr=-20 * s(f) - 15,
                 kl=15 + 15 * max(0, s(f)), kr=15 + 15 * max(0, -s(f)))
    elif acao == "falar":
        p.update(af=45 + 25 * s(2 * math.pi * 1.3 * t), ef=60, ab=-6, dy=2 * s(t * 3))
    else:  # parado (respirando)
        p.update(af=10 + 3 * s(t * 2), ab=-10 - 3 * s(t * 2), dy=2 * s(t * 2))
    return p


def _vec(ang, d):
    a = math.radians(ang)
    return (d * math.sin(a), d * math.cos(a))


def desenhar_boneco(tipo="homem", acao="parado", t=0.0, olhar=1, emocao=None, cor=None, escala=1.0):
    """Devolve (imagem RGBA 1x, (ancora_x, ancora_y)) com a ancora nos pes."""
    cor_roupa, acess = TIPOS.get(tipo, TIPOS["homem"])
    cor_roupa = hexc(cor or cor_roupa)
    if emocao not in EMOCOES:
        emocao = {"susto": "assustado", "triste": "triste", "comemorar": "feliz", "lutar": "bravo",
                  "cair": "assustado", "pensar": "neutro"}.get(acao, "neutro")
    if tipo == "crianca":
        escala *= 0.72
    k = escala * SS
    Wc, Hc = int(1200 * k), int(900 * k)
    ax, ay = Wc / 2, Hc - 60 * k
    im = Image.new("RGBA", (Wc, Hc), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    p = pose(acao, t)
    dirx = 1 if olhar >= 0 else -1
    rot = math.radians(p["rot"] * dirx)

    def R(pt):
        x, y = pt[0] - ax, pt[1] - ay
        c, s = math.cos(rot), math.sin(rot)
        return (ax + x * c - y * s + p["shake"] * k, ay + x * s + y * c)

    def V(ang, L):
        vx, vy = _vec(ang, L * k)
        return (vx * dirx, vy)

    def add(a, b):
        return (a[0] + b[0], a[1] + b[1])

    hip = (ax, ay - (COXA + CANELA) * k + p["dy"] * k)
    tilt = p["tilt"]
    tv = _vec(180 - tilt, TRONCO * k)
    neck = (hip[0] + tv[0] * dirx, hip[1] + tv[1])
    sh = (hip[0] + _vec(180 - tilt, (TRONCO - 14) * k)[0] * dirx, hip[1] + _vec(180 - tilt, (TRONCO - 14) * k)[1])
    hv = _vec(180 - tilt, (CABECA + 8) * k)
    head = (neck[0] + hv[0] * dirx, neck[1] + hv[1])

    def perna(ang, joelho):
        knee = add(hip, V(ang, COXA))
        foot = add(knee, V(ang - joelho, CANELA))
        toe = (foot[0] + 26 * k * dirx, foot[1])
        return [hip, knee, foot, toe]

    def braco(ang, cotovelo):
        el = add(sh, V(ang, BRACO))
        hand = add(el, V(ang + cotovelo, ANTEBRACO))
        return [sh, el, hand]

    def membro(pts, cor, larg=LARG_MEMBRO):
        pts = [R(q) for q in pts]
        w, o = larg * k, CONTORNO * k
        d.line(pts, fill=OUT, width=int(w + 2 * o), joint="curve")
        for q in (pts[0], pts[-1]):
            d.ellipse([q[0] - (w / 2 + o), q[1] - (w / 2 + o), q[0] + w / 2 + o, q[1] + w / 2 + o], fill=OUT)
        d.line(pts, fill=cor, width=int(w), joint="curve")
        for q in (pts[0], pts[-1]):
            d.ellipse([q[0] - w / 2, q[1] - w / 2, q[0] + w / 2, q[1] + w / 2], fill=cor)

    calca = shade(cor_roupa, 0.55) if tipo not in ("papa", "cientista") else (60, 60, 70)
    tras = shade(cor_roupa, 0.78)
    # capa atras de tudo
    if "capa" in acess:
        a, b = R((sh[0] - 30 * k * dirx, sh[1])), R((sh[0] + 10 * k * dirx, sh[1]))
        c1 = R((hip[0] - 95 * k * dirx, hip[1] + 120 * k))
        c2 = R((hip[0] - 10 * k * dirx, hip[1] + 120 * k))
        d.polygon([a, b, c2, c1], fill=(170, 25, 40), outline=OUT, width=int(5 * k))
    if "cabelo_longo" in acess:
        hc = R(head)
        r = CABECA * k
        d.rounded_rectangle([hc[0] - r * 1.08, hc[1] - r * 0.6, hc[0] + r * 1.08, hc[1] + r * 1.55],
                            radius=r * 0.6, fill=(70, 40, 25), outline=OUT, width=int(5 * k))
    # membros de tras
    membro(perna(p["tr"], p["kr"]), shade(calca, 0.8))
    membro(braco(p["ab"], p["eb"]), tras)
    # tronco
    membro([hip, sh], cor_roupa, LARG_TRONCO)
    if "gravata" in acess:
        a = R((sh[0] + 6 * k * dirx, sh[1] + 10 * k))
        b = R((sh[0] + 6 * k * dirx, sh[1] + 75 * k))
        d.line([a, b], fill=(200, 30, 40), width=int(12 * k))
    # perna e braco da frente
    membro(perna(p["tl"], p["kl"]), calca)
    # cabeca
    hc = R(head)
    r = CABECA * k
    o = CONTORNO * k
    d.ellipse([hc[0] - r - o, hc[1] - r - o, hc[0] + r + o, hc[1] + r + o], fill=OUT)
    d.ellipse([hc[0] - r, hc[1] - r, hc[0] + r, hc[1] + r], fill=SKIN)
    _cabelo_e_chapeu(d, hc, r, k, acess, dirx, antes_rosto=True)
    _rosto(d, hc, r, k, dirx, emocao, acess, t)
    _cabelo_e_chapeu(d, hc, r, k, acess, dirx, antes_rosto=False)
    membro(braco(p["af"], p["ef"]), cor_roupa)
    small = im.reduce(SS)
    return small, (ax / SS, ay / SS)


def _rosto(d, hc, r, k, dirx, emo, acess, t):
    ex = hc[0] + 10 * k * dirx
    ey = hc[1] - 4 * k
    piscar = (t % 3.3) < 0.12
    for off in (-17, 17):
        cx = ex + off * k
        if emo in ("assustado", "surpreso"):
            d.ellipse([cx - 11 * k, ey - 12 * k, cx + 11 * k, ey + 12 * k], fill=(255, 255, 255), outline=OUT, width=int(3 * k))
            d.ellipse([cx - 4 * k + 3 * k * dirx, ey - 4 * k, cx + 4 * k + 3 * k * dirx, ey + 4 * k], fill=OUT)
        elif piscar:
            d.line([cx - 7 * k, ey, cx + 7 * k, ey], fill=OUT, width=int(4 * k))
        else:
            d.ellipse([cx - 6 * k, ey - 7 * k, cx + 6 * k, ey + 7 * k], fill=OUT)
        if emo == "bravo":
            inc = 6 if off < 0 else -6
            d.line([cx - 11 * k, ey - 16 * k - inc * k, cx + 11 * k, ey - 16 * k + inc * k], fill=OUT, width=int(5 * k))
        if emo == "triste":
            inc = -5 if off < 0 else 5
            d.line([cx - 10 * k, ey - 15 * k - inc * k, cx + 10 * k, ey - 15 * k + inc * k], fill=OUT, width=int(4 * k))
    if "mascara" in acess:
        d.rounded_rectangle([hc[0] - r, ey - 14 * k, hc[0] + r, ey + 12 * k], radius=8 * k, fill=OUT)
        for off in (-17, 17):
            cx = ex + off * k
            d.ellipse([cx - 6 * k, ey - 6 * k, cx + 6 * k, ey + 6 * k], fill=(255, 255, 255))
    if "tapa_olho" in acess:
        cx = ex + 17 * k * dirx
        d.ellipse([cx - 11 * k, ey - 11 * k, cx + 11 * k, ey + 11 * k], fill=OUT)
        d.line([hc[0] - r, ey - 22 * k, hc[0] + r, ey + 6 * k], fill=OUT, width=int(4 * k))
    if "oculos" in acess:
        for off in (-17, 17):
            cx = ex + off * k
            d.ellipse([cx - 14 * k, ey - 14 * k, cx + 14 * k, ey + 14 * k], outline=OUT, width=int(4 * k))
        d.line([ex - 3 * k, ey, ex + 3 * k, ey], fill=OUT, width=int(4 * k))
    if "barba" in acess or "barba_branca" in acess:
        cb = (235, 235, 235) if "barba_branca" in acess else (95, 55, 30)
        d.chord([hc[0] - r * 0.95, hc[1] - r * 0.35, hc[0] + r * 0.95, hc[1] + r * 1.25], 0, 180,
                fill=cb, outline=OUT, width=int(4 * k))
    mx, my = ex, hc[1] + 24 * k
    if emo == "feliz":
        d.arc([mx - 17 * k, my - 14 * k, mx + 17 * k, my + 10 * k], 10, 170, fill=OUT, width=int(5 * k))
    elif emo == "triste":
        d.arc([mx - 14 * k, my - 2 * k, mx + 14 * k, my + 18 * k], 200, 340, fill=OUT, width=int(5 * k))
    elif emo in ("assustado", "surpreso"):
        d.ellipse([mx - 9 * k, my - 9 * k, mx + 9 * k, my + 11 * k], fill=(120, 20, 30), outline=OUT, width=int(4 * k))
    elif emo == "bravo":
        d.line([mx - 13 * k, my + 4 * k, mx + 13 * k, my + 1 * k], fill=OUT, width=int(5 * k))
    else:
        d.line([mx - 10 * k, my, mx + 10 * k, my], fill=OUT, width=int(5 * k))


def _cabelo_e_chapeu(d, hc, r, k, acess, dirx, antes_rosto):
    x, y = hc
    w5 = int(5 * k)
    if antes_rosto:
        if "cabelo_curto" in acess or "cabelo_longo" in acess:
            d.chord([x - r, y - r, x + r, y + r * 0.35], 180, 360, fill=(70, 40, 25), outline=OUT, width=w5)
        if "cabelo_maluco" in acess:
            for i in range(-3, 4):
                a = math.radians(-90 + i * 28)
                d.ellipse([x + math.cos(a) * r - 18 * k, y + math.sin(a) * r - 18 * k,
                           x + math.cos(a) * r + 18 * k, y + math.sin(a) * r + 18 * k], fill=(235, 235, 235), outline=OUT, width=int(3 * k))
        if "cabelo_coque" in acess:
            d.chord([x - r, y - r, x + r, y + r * 0.3], 180, 360, fill=(190, 190, 195), outline=OUT, width=w5)
            d.ellipse([x - 22 * k, y - r - 30 * k, x + 22 * k, y - r + 10 * k], fill=(190, 190, 195), outline=OUT, width=w5)
        return
    if "coroa" in acess:
        b = y - r * 0.7
        pts = [(x - r * 0.8, b), (x - r * 0.8, b - 46 * k), (x - r * 0.4, b - 22 * k), (x, b - 56 * k),
               (x + r * 0.4, b - 22 * k), (x + r * 0.8, b - 46 * k), (x + r * 0.8, b)]
        d.polygon(pts, fill=(255, 196, 0), outline=OUT, width=w5)
        d.ellipse([x - 7 * k, b - 20 * k, x + 7 * k, b - 6 * k], fill=(220, 30, 60))
    if "capacete" in acess:
        d.chord([x - r * 1.1, y - r * 1.15, x + r * 1.1, y + r * 0.5], 180, 360, fill=(85, 100, 50), outline=OUT, width=w5)
        d.line([x - r * 1.2, y - r * 0.32, x + r * 1.2, y - r * 0.32], fill=OUT, width=int(9 * k))
    if "capacete_romano" in acess:
        d.chord([x - r * 1.08, y - r * 1.12, x + r * 1.08, y + r * 0.45], 180, 360, fill=(200, 160, 60), outline=OUT, width=w5)
        d.chord([x - r * 0.9, y - r * 1.55, x + r * 0.9, y - r * 0.5], 180, 360, fill=(200, 25, 30), outline=OUT, width=w5)
        d.chord([x - r * 1.08, y - r * 1.12, x + r * 1.08, y + r * 0.45], 180, 360, fill=(200, 160, 60), outline=OUT, width=w5)
    if "elmo" in acess:
        d.rounded_rectangle([x - r * 1.05, y - r * 1.1, x + r * 1.05, y + r * 0.95], radius=r * 0.5,
                            fill=(160, 166, 176), outline=OUT, width=w5)
        d.rectangle([x - r * 0.75, y - 8 * k, x + r * 0.75, y + 4 * k], fill=OUT)
    if "capacete_viking" in acess:
        for sgn in (-1, 1):
            d.polygon([(x + sgn * r * 0.75, y - r * 0.55), (x + sgn * r * 1.55, y - r * 1.5),
                       (x + sgn * r * 1.0, y - r * 0.4)], fill=(245, 240, 220), outline=OUT, width=w5)
        d.chord([x - r * 1.05, y - r * 1.1, x + r * 1.05, y + r * 0.4], 180, 360, fill=(150, 150, 160), outline=OUT, width=w5)
    if "bandana" in acess:
        d.chord([x - r * 1.03, y - r * 1.05, x + r * 1.03, y + r * 0.2], 180, 360, fill=(200, 30, 40), outline=OUT, width=w5)
        d.ellipse([x - r * 1.3 * dirx - 12 * k, y - r * 0.5, x - r * 1.3 * dirx + 12 * k, y - r * 0.2], fill=(200, 30, 40))
    if "chapeu_tricornio" in acess:
        d.polygon([(x - r * 1.45, y - r * 0.55), (x, y - r * 1.55), (x + r * 1.45, y - r * 0.55),
                   (x, y - r * 0.75)], fill=(35, 35, 45), outline=OUT, width=w5)
    if "chapeu_explorador" in acess:
        d.ellipse([x - r * 1.5, y - r * 0.85, x + r * 1.5, y - r * 0.4], fill=(150, 110, 60), outline=OUT, width=w5)
        d.chord([x - r * 0.85, y - r * 1.45, x + r * 0.85, y - r * 0.3], 180, 360, fill=(170, 125, 70), outline=OUT, width=w5)
    if "mitra" in acess:
        d.polygon([(x - r * 0.75, y - r * 0.6), (x - r * 0.6, y - r * 1.9), (x, y - r * 2.4),
                   (x + r * 0.6, y - r * 1.9), (x + r * 0.75, y - r * 0.6)], fill=(250, 248, 240), outline=OUT, width=w5)
        d.line([x, y - r * 0.6, x, y - r * 2.3], fill=(230, 180, 40), width=int(10 * k))
    if "nemes" in acess:
        d.polygon([(x - r * 1.25, y + r * 0.9), (x - r * 1.05, y - r * 0.9), (x, y - r * 1.15),
                   (x + r * 1.05, y - r * 0.9), (x + r * 1.25, y + r * 0.9), (x + r * 0.8, y - r * 0.3),
                   (x - r * 0.8, y - r * 0.3)], fill=(230, 185, 50), outline=OUT, width=w5)
        for i in range(3):
            yy = y - r * 0.75 + i * 18 * k
            d.line([x - r * 0.9, yy, x + r * 0.9, yy], fill=(30, 60, 150), width=int(7 * k))
    if "quepe" in acess:
        d.chord([x - r * 1.0, y - r * 1.2, x + r * 1.0, y + r * 0.1], 180, 360, fill=(30, 55, 100), outline=OUT, width=w5)
        d.polygon([(x, y - r * 0.55), (x + r * 1.35 * dirx, y - r * 0.4), (x + r * 1.2 * dirx, y - r * 0.25),
                   (x, y - r * 0.35)], fill=OUT)
    if "gorro" in acess:
        d.chord([x - r * 1.03, y - r * 1.1, x + r * 1.03, y + r * 0.15], 180, 360, fill=(40, 40, 45), outline=OUT, width=w5)
    if "capacete_obra" in acess:
        d.chord([x - r * 1.1, y - r * 1.15, x + r * 1.1, y + r * 0.45], 180, 360, fill=(255, 205, 0), outline=OUT, width=w5)
        d.line([x - r * 1.25, y - r * 0.35, x + r * 1.25, y - r * 0.35], fill=OUT, width=int(8 * k))
    if "careca" in acess:
        d.arc([x - r * 0.5, y - r * 0.85, x + r * 0.2, y - r * 0.45], 200, 330, fill=(255, 235, 210), width=int(5 * k))


# ============================================================ OBJETOS
BANDEIRAS = ["brasil", "portugal", "espanha", "eua", "franca", "italia", "alemanha", "japao", "inglaterra",
             "russia", "china", "argentina", "mexico", "holanda", "roma", "pirata", "branca", "vermelha"]

OBJETOS = ["navio", "caravela", "castelo", "casa", "predio", "igreja", "piramide", "arvore", "palmeira",
           "montanha", "vulcao", "ilha", "sol", "lua", "globo", "moeda", "saco_dinheiro", "barra_ouro",
           "bau_tesouro", "coroa", "trono", "espada", "escudo", "canhao", "bomba", "explosao", "fogo",
           "bandeira", "mapa", "documento", "livro", "placa", "seta", "interrogacao", "exclamacao",
           "relogio", "ampulheta", "coracao", "caveira", "foguete", "aviao", "carro", "trem", "nuvem",
           "raio", "gota", "diamante", "chave", "cadeado", "lampada", "microfone", "jornal", "grafico_sobe",
           "grafico_desce", "tenda", "muro", "porta", "estrela", "planeta", "bola_cristal"]


class _P:
    """Canvas 1000x1000 logico, desenhado em alta resolucao."""

    def __init__(self, tam):
        self.s = tam * SS / 1000
        self.im = Image.new("RGBA", (int(1000 * self.s) + 2, int(1000 * self.s) + 2), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)
        self.lw = max(2, int(14 * self.s))

    def _p(self, pts):
        return [(x * self.s, y * self.s) for x, y in pts]

    def poly(self, pts, cor, contorno=True):
        self.d.polygon(self._p(pts), fill=cor, outline=OUT if contorno else None, width=self.lw if contorno else 0)

    def ell(self, x0, y0, x1, y1, cor, contorno=True):
        self.d.ellipse(self._p([(x0, y0), (x1, y1)]), fill=cor, outline=OUT if contorno else None, width=self.lw if contorno else 0)

    def rect(self, x0, y0, x1, y1, cor, contorno=True, raio=0):
        b = self._p([(x0, y0), (x1, y1)])
        if raio:
            self.d.rounded_rectangle(b, radius=raio * self.s, fill=cor, outline=OUT if contorno else None,
                                     width=self.lw if contorno else 0)
        else:
            self.d.rectangle(b, fill=cor, outline=OUT if contorno else None, width=self.lw if contorno else 0)

    def line(self, pts, cor=OUT, w=14):
        self.d.line(self._p(pts), fill=cor, width=max(1, int(w * self.s)), joint="curve")

    def texto(self, x, y, txt, size, cor=(30, 30, 30), contorno=0):
        f = _font(size * self.s)
        self.d.text((x * self.s, y * self.s), txt, font=f, fill=cor, anchor="mm",
                    stroke_width=int(contorno * self.s), stroke_fill=OUT)

    def fim(self):
        im = self.im.reduce(SS)
        bb = im.getbbox()
        return im.crop(bb) if bb else im


def _bandeira_pano(P, x0, y0, x1, y1, pais):
    w, h = x1 - x0, y1 - y0
    c = {"verde": (0, 156, 59), "amarelo": (255, 223, 0), "azul": (0, 39, 118), "vermelho": (206, 17, 38),
         "branco": (250, 250, 250), "preto": (20, 20, 20)}
    if pais == "brasil":
        P.rect(x0, y0, x1, y1, c["verde"])
        P.poly([(x0 + w * .08, y0 + h / 2), (x0 + w / 2, y0 + h * .1), (x1 - w * .08, y0 + h / 2), (x0 + w / 2, y1 - h * .1)], c["amarelo"], False)
        P.ell(x0 + w / 2 - h * .25, y0 + h * .25, x0 + w / 2 + h * .25, y0 + h * .75, c["azul"], False)
    elif pais == "portugal":
        P.rect(x0, y0, x1, y1, c["vermelho"])
        P.rect(x0, y0, x0 + w * .4, y1, (0, 102, 0), False)
        P.ell(x0 + w * .4 - h * .2, y0 + h * .3, x0 + w * .4 + h * .2, y0 + h * .7, c["amarelo"], False)
    elif pais == "espanha":
        P.rect(x0, y0, x1, y1, (198, 11, 30))
        P.rect(x0, y0 + h * .25, x1, y0 + h * .75, (255, 196, 0), False)
    elif pais == "eua":
        P.rect(x0, y0, x1, y1, c["branco"])
        for i in range(7):
            yy = y0 + i * h / 6.5
            P.rect(x0, yy, x1, yy + h / 13, (178, 34, 52), False)
        P.rect(x0, y0, x0 + w * .42, y0 + h * .54, (60, 59, 110), False)
    elif pais in ("franca", "italia"):
        cores = [(0, 85, 164), c["branco"], (239, 65, 53)] if pais == "franca" else [(0, 146, 70), c["branco"], (206, 43, 55)]
        for i, cc in enumerate(cores):
            P.rect(x0 + i * w / 3, y0, x0 + (i + 1) * w / 3, y1, cc, False)
        P.rect(x0, y0, x1, y1, None)
    elif pais in ("alemanha", "russia", "holanda"):
        cores = {"alemanha": [c["preto"], (221, 0, 0), (255, 206, 0)], "russia": [c["branco"], (0, 57, 166), (213, 43, 30)],
                 "holanda": [(174, 28, 40), c["branco"], (33, 70, 139)]}[pais]
        for i, cc in enumerate(cores):
            P.rect(x0, y0 + i * h / 3, x1, y0 + (i + 1) * h / 3, cc, False)
        P.rect(x0, y0, x1, y1, None)
    elif pais == "japao":
        P.rect(x0, y0, x1, y1, c["branco"])
        P.ell(x0 + w / 2 - h * .3, y0 + h * .2, x0 + w / 2 + h * .3, y0 + h * .8, (188, 0, 45), False)
    elif pais == "inglaterra":
        P.rect(x0, y0, x1, y1, c["branco"])
        P.rect(x0 + w * .42, y0, x0 + w * .58, y1, (206, 17, 36), False)
        P.rect(x0, y0 + h * .38, x1, y0 + h * .62, (206, 17, 36), False)
    elif pais == "china":
        P.rect(x0, y0, x1, y1, (222, 41, 16))
        cx, cy, rr = x0 + w * .2, y0 + h * .3, h * .2
        P.poly([(cx + (rr if i % 2 == 0 else rr * .4) * math.cos(math.radians(-90 + i * 36)),
                 cy + (rr if i % 2 == 0 else rr * .4) * math.sin(math.radians(-90 + i * 36))) for i in range(10)],
               (255, 222, 0), False)
    elif pais in ("argentina", "mexico"):
        if pais == "argentina":
            for i, cc in enumerate([(116, 172, 223), c["branco"], (116, 172, 223)]):
                P.rect(x0, y0 + i * h / 3, x1, y0 + (i + 1) * h / 3, cc, False)
            P.ell(x0 + w / 2 - h * .1, y0 + h * .4, x0 + w / 2 + h * .1, y0 + h * .6, (246, 180, 14), False)
        else:
            for i, cc in enumerate([(0, 104, 71), c["branco"], (206, 17, 38)]):
                P.rect(x0 + i * w / 3, y0, x0 + (i + 1) * w / 3, y1, cc, False)
        P.rect(x0, y0, x1, y1, None)
    elif pais == "roma":
        P.rect(x0, y0, x1, y1, (150, 20, 30))
        P.texto(x0 + w / 2, y0 + h / 2, "SPQR", h * .35, (240, 190, 60))
    elif pais == "pirata":
        P.rect(x0, y0, x1, y1, c["preto"])
        cx, cy = x0 + w / 2, y0 + h * .45
        P.line([(cx - h * .3, cy + h * .05), (cx + h * .3, cy + h * .4)], c["branco"], 18)
        P.line([(cx + h * .3, cy + h * .05), (cx - h * .3, cy + h * .4)], c["branco"], 18)
        P.ell(cx - h * .2, cy - h * .25, cx + h * .2, cy + h * .15, c["branco"], False)
        P.ell(cx - h * .12, cy - h * .12, cx - h * .03, cy - h * .02, c["preto"], False)
        P.ell(cx + h * .03, cy - h * .12, cx + h * .12, cy - h * .02, c["preto"], False)
    elif pais == "branca":
        P.rect(x0, y0, x1, y1, c["branco"])
    else:
        P.rect(x0, y0, x1, y1, c["vermelho"])


@lru_cache(maxsize=256)
def desenhar_objeto(tipo, tam=380, texto="", pais=""):
    P = _P(tam)
    if tipo in ("navio", "caravela"):
        P.line([(500, 120), (500, 640)], OUT, 22)
        P.poly([(515, 160), (820, 560), (515, 560)], (250, 246, 232))
        P.poly([(485, 200), (215, 560), (485, 560)], (250, 246, 232))
        if tipo == "caravela":
            P.line([(500, 300), (500, 520)], (200, 30, 40), 30)
            P.line([(420, 410), (580, 410)], (200, 30, 40), 30)
        P.poly([(500, 120), (600, 150), (500, 180)], (210, 40, 40))
        P.poly([(80, 600), (920, 600), (790, 820), (210, 820)], (140, 85, 40))
        P.line([(150, 680), (850, 680)], (100, 60, 25), 16)
        for x in (300, 420, 580, 700):
            P.ell(x - 22, 700, x + 22, 744, (60, 40, 20), False)
    elif tipo == "castelo":
        P.rect(250, 380, 750, 860, (150, 158, 170))
        for x0 in (130, 690):
            P.rect(x0, 260, x0 + 180, 860, (165, 172, 184))
            P.poly([(x0 - 15, 260), (x0 + 90, 110), (x0 + 195, 260)], (190, 40, 50))
        for x in range(260, 740, 90):
            P.rect(x, 330, x + 50, 390, (150, 158, 170))
        P.poly([(420, 860), (420, 700), (500, 630), (580, 700), (580, 860)], (90, 60, 35))
        P.line([(500, 110), (500, 260)], OUT, 12)
        P.poly([(505, 110), (620, 145), (505, 180)], (240, 200, 40))
    elif tipo == "casa":
        P.rect(220, 470, 780, 860, (240, 200, 120))
        P.poly([(160, 490), (500, 190), (840, 490)], (200, 50, 45))
        P.rect(440, 650, 560, 860, (120, 75, 40))
        P.rect(270, 560, 380, 660, (160, 210, 240))
        P.rect(620, 560, 730, 660, (160, 210, 240))
    elif tipo == "predio":
        P.rect(280, 100, 720, 900, (70, 110, 150))
        for y in range(170, 820, 110):
            for x in (330, 450, 570):
                P.rect(x, y, x + 90, y + 70, (255, 220, 120), False)
    elif tipo == "igreja":
        P.rect(250, 470, 750, 880, (240, 235, 220))
        P.poly([(200, 490), (500, 260), (800, 490)], (150, 60, 50))
        P.rect(440, 160, 560, 300, (240, 235, 220))
        P.line([(500, 40), (500, 170)], OUT, 22)
        P.line([(455, 85), (545, 85)], OUT, 22)
        P.poly([(440, 880), (440, 700), (500, 640), (560, 700), (560, 880)], (110, 70, 40))
    elif tipo == "piramide":
        P.poly([(80, 860), (500, 180), (920, 860)], (225, 180, 100))
        for i in range(1, 6):
            y = 180 + i * 113
            half = (y - 180) * 420 / 680
            P.line([(500 - half, y), (500 + half, y)], (180, 135, 70), 10)
    elif tipo in ("arvore", "palmeira"):
        if tipo == "arvore":
            P.rect(450, 550, 550, 900, (120, 75, 40))
            for x0, y0, r in [(320, 330, 170), (510, 250, 190), (660, 360, 160), (480, 450, 170)]:
                P.ell(x0 - r, y0 - r, x0 + r, y0 + r, (60, 160, 70))
        else:
            P.poly([(470, 900), (520, 300), (560, 300), (540, 900)], (150, 105, 55))
            for ang in range(-160, 0, 32):
                a = math.radians(ang)
                P.poly([(530, 300), (530 + 330 * math.cos(a), 300 + 330 * math.sin(a) + 150),
                        (530 + 300 * math.cos(a + 0.25), 300 + 300 * math.sin(a + 0.25) + 150)], (50, 150, 70))
    elif tipo in ("montanha", "vulcao"):
        P.poly([(60, 880), (500, 150), (940, 880)], (120, 110, 105))
        if tipo == "montanha":
            P.poly([(380, 350), (500, 150), (620, 350), (560, 320), (500, 370), (440, 320)], (250, 250, 255))
        else:
            P.poly([(420, 280), (580, 280), (650, 400), (350, 400)], (120, 110, 105))
            P.poly([(420, 280), (470, 120), (520, 230), (560, 90), (580, 280)], (255, 110, 20))
    elif tipo == "ilha":
        P.ell(100, 700, 900, 900, (240, 210, 140))
        P.poly([(480, 760), (510, 360), (540, 360), (530, 760)], (150, 105, 55))
        for ang in range(-160, 0, 40):
            a = math.radians(ang)
            P.poly([(520, 360), (520 + 260 * math.cos(a), 360 + 260 * math.sin(a) + 120),
                    (520 + 230 * math.cos(a + 0.3), 360 + 230 * math.sin(a + 0.3) + 120)], (50, 150, 70))
    elif tipo == "sol":
        for i in range(12):
            a = math.radians(i * 30)
            P.poly([(500 + 300 * math.cos(a - .12), 500 + 300 * math.sin(a - .12)),
                    (500 + 460 * math.cos(a), 500 + 460 * math.sin(a)),
                    (500 + 300 * math.cos(a + .12), 500 + 300 * math.sin(a + .12))], (255, 170, 0))
        P.ell(230, 230, 770, 770, (255, 210, 40))
    elif tipo == "lua":
        P.ell(150, 150, 850, 850, (245, 240, 205))
        for x0, y0, r in [(380, 380, 70), (600, 560, 50), (420, 640, 35)]:
            P.ell(x0 - r, y0 - r, x0 + r, y0 + r, (215, 210, 175), False)
    elif tipo == "globo":
        P.ell(120, 120, 880, 880, (40, 140, 230))
        for pts in ([(260, 300), (430, 240), (470, 380), (380, 520), (300, 470)],
                    [(560, 260), (720, 300), (760, 450), (640, 520), (560, 420)],
                    [(420, 580), (560, 560), (600, 720), (480, 800), (400, 700)]):
            P.poly(pts, (70, 185, 90), False)
        P.ell(120, 120, 880, 880, None)
    elif tipo == "moeda":
        P.ell(130, 130, 870, 870, (255, 196, 30))
        P.ell(220, 220, 780, 780, (240, 175, 20))
        P.texto(500, 500, "$", 420, (200, 130, 0))
    elif tipo == "saco_dinheiro":
        P.ell(170, 330, 830, 920, (205, 160, 90))
        P.poly([(380, 340), (330, 160), (500, 230), (670, 160), (620, 340)], (205, 160, 90))
        P.line([(370, 330), (630, 330)], (140, 90, 40), 26)
        P.texto(500, 640, "$", 380, (70, 140, 60))
    elif tipo == "barra_ouro":
        for dx, dy in [(0, 0), (240, 0), (120, -200)]:
            P.poly([(180 + dx, 820 + dy), (260 + dx, 640 + dy), (500 + dx, 640 + dy), (580 + dx, 820 + dy)], (255, 196, 30))
    elif tipo == "bau_tesouro":
        P.rect(150, 480, 850, 880, (140, 85, 40))
        P.ell(130, 380, 870, 600, (255, 200, 40))
        for x in (300, 450, 600):
            P.ell(x - 50, 360, x + 50, 460, (255, 215, 60))
        P.rect(150, 480, 850, 560, (115, 70, 35))
        P.rect(450, 520, 550, 640, (255, 196, 30))
    elif tipo == "coroa":
        P.poly([(150, 750), (150, 300), (320, 520), (500, 220), (680, 520), (850, 300), (850, 750)], (255, 196, 0))
        P.rect(150, 700, 850, 800, (230, 170, 0))
        for x, cc in [(330, (220, 30, 60)), (500, (40, 120, 230)), (670, (220, 30, 60))]:
            P.ell(x - 40, 620, x + 40, 700, cc)
    elif tipo == "trono":
        P.rect(260, 120, 740, 600, (170, 25, 40), raio=60)
        P.rect(200, 560, 800, 700, (255, 196, 30))
        P.rect(230, 690, 300, 900, (255, 196, 30))
        P.rect(700, 690, 770, 900, (255, 196, 30))
    elif tipo == "espada":
        P.poly([(470, 80), (530, 80), (535, 640), (500, 700), (465, 640)], (215, 220, 230))
        P.rect(330, 640, 670, 700, (200, 150, 40))
        P.rect(465, 700, 535, 880, (110, 60, 30))
        P.ell(450, 870, 550, 950, (200, 150, 40))
    elif tipo == "escudo":
        P.poly([(170, 160), (830, 160), (800, 560), (500, 880), (200, 560)], (40, 80, 170))
        P.poly([(450, 160), (550, 160), (550, 850), (500, 880), (450, 850)], (240, 200, 40), False)
        P.rect(170, 380, 830, 460, (240, 200, 40), False)
        P.poly([(170, 160), (830, 160), (800, 560), (500, 880), (200, 560)], None)
    elif tipo == "canhao":
        P.poly([(160, 420), (820, 280), (860, 420), (200, 560)], (60, 60, 70))
        P.ell(780, 270, 900, 440, (45, 45, 55))
        P.ell(220, 520, 540, 840, (140, 85, 40))
        P.ell(340, 640, 420, 720, (90, 55, 25))
    elif tipo == "bomba":
        P.ell(170, 280, 830, 940, (40, 40, 48))
        P.rect(430, 220, 570, 320, (70, 70, 80))
        P.line([(500, 220), (560, 140), (640, 120)], (140, 100, 60), 20)
        P.texto(690, 100, "✹", 170, (255, 170, 0))
        P.ell(300, 420, 400, 520, (110, 110, 125), False)
    elif tipo == "explosao":
        pts = []
        for i in range(24):
            r = 470 if i % 2 == 0 else 250
            a = math.radians(i * 15)
            pts.append((500 + r * math.cos(a), 500 + r * math.sin(a)))
        P.poly(pts, (255, 120, 20))
        pts2 = [(500 + (0.6 * p[0] - 300), 500 + (0.6 * p[1] - 300)) for p in pts]
        P.poly(pts2, (255, 220, 60), False)
    elif tipo == "fogo":
        P.poly([(500, 60), (760, 470), (800, 700), (700, 890), (300, 890), (200, 700), (260, 450), (360, 560)], (255, 110, 20))
        P.poly([(500, 330), (650, 600), (620, 860), (380, 860), (350, 620), (420, 520)], (255, 205, 50), False)
    elif tipo == "bandeira":
        P.rect(140, 80, 180, 950, (110, 75, 40))
        P.ell(125, 50, 195, 120, (230, 190, 40))
        _bandeira_pano(P, 180, 110, 900, 560, pais or "vermelha")
    elif tipo == "mapa":
        P.poly([(100, 220), (370, 160), (630, 220), (900, 160), (900, 800), (630, 860), (370, 800), (100, 860)], (240, 222, 175))
        P.line([(370, 160), (370, 800)], (200, 180, 135), 10)
        P.line([(630, 220), (630, 860)], (200, 180, 135), 10)
        for i in range(9):
            x = 200 + i * 60
            P.line([(x, 640 - i * 35), (x + 30, 640 - i * 35 - 18)], (200, 40, 40), 16)
        P.line([(700, 300), (800, 400)], (200, 40, 40), 26)
        P.line([(800, 300), (700, 400)], (200, 40, 40), 26)
    elif tipo in ("documento", "jornal"):
        P.rect(200, 80, 800, 920, (250, 246, 232) if tipo == "documento" else (235, 235, 235), raio=20)
        if texto:
            P.texto(500, 200, texto[:14].upper(), 80, (40, 40, 40))
        for y in range(320, 840, 70):
            P.line([(270, y), (730 if y % 140 else 620, y)], (150, 150, 150), 14)
        if tipo == "documento":
            P.line([(560, 830), (620, 790), (680, 840), (740, 800)], (30, 60, 160), 12)
    elif tipo == "livro":
        P.poly([(120, 260), (500, 320), (880, 260), (880, 800), (500, 860), (120, 800)], (250, 246, 232))
        P.line([(500, 320), (500, 860)], OUT, 14)
        P.poly([(120, 800), (500, 860), (880, 800), (880, 840), (500, 900), (120, 840)], (150, 40, 40))
    elif tipo == "placa":
        P.rect(470, 450, 530, 950, (120, 75, 40))
        P.rect(100, 150, 900, 520, (180, 120, 60), raio=30)
        P.texto(500, 335, (texto or "?")[:12].upper(), 150 if len(texto or "?") <= 7 else 100, (255, 255, 255), 6)
    elif tipo == "seta":
        P.poly([(100, 400), (600, 400), (600, 220), (920, 500), (600, 780), (600, 600), (100, 600)], (230, 40, 40))
    elif tipo in ("interrogacao", "exclamacao"):
        P.texto(500, 500, "?" if tipo == "interrogacao" else "!", 900, (255, 215, 0), 30)
    elif tipo == "relogio":
        P.ell(120, 120, 880, 880, (250, 250, 250))
        for i in range(12):
            a = math.radians(i * 30)
            P.line([(500 + 300 * math.cos(a), 500 + 300 * math.sin(a)), (500 + 340 * math.cos(a), 500 + 340 * math.sin(a))], OUT, 16)
        P.line([(500, 500), (500, 260)], OUT, 26)
        P.line([(500, 500), (680, 560)], OUT, 26)
    elif tipo == "ampulheta":
        P.rect(220, 80, 780, 160, (140, 85, 40))
        P.rect(220, 840, 780, 920, (140, 85, 40))
        P.poly([(280, 160), (720, 160), (520, 500), (720, 840), (280, 840), (480, 500)], (210, 235, 250))
        P.poly([(340, 840), (660, 840), (500, 640)], (240, 200, 110), False)
        P.poly([(380, 250), (620, 250), (500, 420)], (240, 200, 110), False)
    elif tipo == "coracao":
        P.ell(130, 180, 520, 560, (220, 30, 60))
        P.ell(480, 180, 870, 560, (220, 30, 60))
        P.poly([(150, 450), (500, 880), (850, 450), (500, 380)], (220, 30, 60))
    elif tipo == "caveira":
        P.ell(200, 120, 800, 700, (245, 245, 240))
        P.rect(320, 600, 680, 860, (245, 245, 240), raio=40)
        P.ell(300, 330, 470, 500, OUT)
        P.ell(530, 330, 700, 500, OUT)
        P.poly([(500, 520), (450, 620), (550, 620)], OUT)
        for x in (400, 500, 600):
            P.line([(x, 720), (x, 850)], OUT, 14)
    elif tipo == "foguete":
        P.poly([(500, 60), (640, 260), (640, 700), (360, 700), (360, 260)], (235, 235, 240))
        P.poly([(360, 520), (220, 760), (360, 700)], (220, 40, 40))
        P.poly([(640, 520), (780, 760), (640, 700)], (220, 40, 40))
        P.ell(440, 300, 560, 420, (60, 160, 230))
        P.poly([(400, 700), (600, 700), (500, 950)], (255, 150, 20))
    elif tipo == "aviao":
        P.rect(120, 420, 880, 560, (235, 235, 240), raio=70)
        P.poly([(420, 470), (300, 180), (400, 180), (580, 470)], (200, 205, 215))
        P.poly([(420, 520), (300, 820), (400, 820), (580, 520)], (200, 205, 215))
        P.poly([(160, 440), (120, 280), (220, 280), (260, 440)], (220, 40, 40))
        for x in range(560, 820, 60):
            P.ell(x, 455, x + 34, 489, (60, 160, 230), False)
    elif tipo == "carro":
        P.rect(100, 480, 900, 720, (220, 50, 50), raio=60)
        P.poly([(260, 480), (360, 300), (660, 300), (760, 480)], (220, 50, 50))
        P.poly([(310, 470), (390, 340), (490, 340), (490, 470)], (170, 220, 245))
        P.poly([(530, 470), (530, 340), (630, 340), (710, 470)], (170, 220, 245))
        for x in (270, 730):
            P.ell(x - 100, 620, x + 100, 820, (40, 40, 45))
            P.ell(x - 40, 680, x + 40, 760, (180, 180, 185))
    elif tipo == "trem":
        P.rect(120, 300, 620, 760, (40, 90, 160))
        P.rect(620, 450, 900, 760, (40, 90, 160))
        P.rect(700, 240, 800, 450, (60, 60, 70))
        P.rect(200, 380, 330, 500, (170, 220, 245))
        P.rect(400, 380, 530, 500, (170, 220, 245))
        for x in (230, 450, 760):
            P.ell(x - 80, 700, x + 80, 860, (40, 40, 45))
    elif tipo == "nuvem":
        for x0, y0, r in [(330, 560, 190), (520, 450, 230), (700, 570, 170)]:
            P.ell(x0 - r, y0 - r, x0 + r, y0 + r, (250, 250, 255))
        P.rect(160, 560, 850, 740, (250, 250, 255), False)
    elif tipo == "raio":
        P.poly([(560, 60), (260, 540), (480, 540), (400, 940), (760, 400), (530, 400), (680, 60)], (255, 215, 0))
    elif tipo == "gota":
        P.poly([(500, 80), (760, 560), (240, 560)], (60, 160, 230))
        P.ell(240, 400, 760, 920, (60, 160, 230))
    elif tipo == "diamante":
        P.poly([(200, 380), (320, 200), (680, 200), (800, 380), (500, 860)], (120, 210, 245))
        P.line([(200, 380), (800, 380)], OUT, 12)
        P.line([(320, 200), (500, 860), (680, 200)], OUT, 10)
    elif tipo == "chave":
        P.ell(130, 330, 470, 670, (255, 196, 30))
        P.ell(240, 440, 360, 560, (0, 0, 0, 0))
        P.rect(440, 460, 900, 540, (255, 196, 30))
        P.rect(760, 540, 820, 650, (255, 196, 30))
        P.rect(840, 540, 890, 620, (255, 196, 30))
    elif tipo == "cadeado":
        P.line([(330, 450), (330, 300), (500, 170), (670, 300), (670, 450)], (150, 150, 160), 70)
        P.rect(220, 430, 780, 880, (255, 196, 30), raio=50)
        P.ell(460, 580, 540, 660, OUT)
        P.rect(480, 640, 520, 760, OUT)
    elif tipo == "lampada":
        P.ell(220, 100, 780, 660, (255, 225, 80))
        P.rect(380, 620, 620, 860, (160, 160, 170))
        P.line([(390, 700), (610, 700)], OUT, 12)
        P.line([(390, 780), (610, 780)], OUT, 12)
    elif tipo == "microfone":
        P.rect(380, 100, 620, 520, (60, 60, 70), raio=120)
        P.line([(500, 520), (500, 820)], OUT, 30)
        P.rect(330, 800, 670, 870, (60, 60, 70))
    elif tipo in ("grafico_sobe", "grafico_desce"):
        P.rect(120, 120, 880, 880, (250, 250, 250), raio=30)
        pts = [(200, 760), (360, 600), (500, 660), (640, 420), (800, 220)]
        if tipo == "grafico_desce":
            pts = [(x, 980 - y) for x, y in pts]
        P.line(pts, (40, 170, 80) if tipo == "grafico_sobe" else (220, 40, 40), 40)
    elif tipo == "tenda":
        P.poly([(100, 860), (500, 180), (900, 860)], (230, 200, 140))
        P.poly([(420, 860), (500, 520), (580, 860)], (120, 80, 40))
    elif tipo == "muro":
        for row in range(6):
            for col in range(5):
                off = 0 if row % 2 == 0 else 80
                P.rect(40 + col * 180 + off - (80 if row % 2 else 0), 300 + row * 100,
                       200 + col * 180 + off - (80 if row % 2 else 0), 390 + row * 100, (180, 80, 60))
    elif tipo == "porta":
        P.rect(260, 100, 740, 920, (130, 80, 40), raio=40)
        P.ell(630, 500, 690, 560, (255, 196, 30))
    elif tipo == "estrela":
        pts = []
        for i in range(10):
            r = 450 if i % 2 == 0 else 190
            a = math.radians(-90 + i * 36)
            pts.append((500 + r * math.cos(a), 520 + r * math.sin(a)))
        P.poly(pts, (255, 210, 30))
    elif tipo == "planeta":
        P.ell(220, 220, 780, 780, (230, 150, 80))
        P.d.ellipse(P._p([(60, 430), (940, 570)]), outline=(250, 220, 160), width=int(40 * P.s))
    elif tipo == "bola_cristal":
        P.ell(180, 100, 820, 740, (150, 110, 230))
        P.ell(300, 200, 420, 320, (220, 200, 255), False)
        P.rect(260, 700, 740, 860, (110, 70, 40), raio=30)
    else:
        P.texto(500, 500, "?", 800, (255, 215, 0), 30)
    return P.fim()
