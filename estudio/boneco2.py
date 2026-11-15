"""
Personagem cartoon (cabeca grande, corpo arredondado, maos, sapatos, rosto expressivo).
Usa os mesmos angulos de pose de desenhos.pose().
"""

import math

from PIL import Image, ImageDraw

import desenhos as D

OUT = D.OUT
SKIN = (250, 208, 170)
SKIN_SH = (226, 172, 132)
SS = 2

# comprimentos 1x
COXA, CANELA, TRONCO, BRACO, ANTEBRACO = 64, 58, 118, 60, 54
R_CAB = 86
L_PERNA, L_BRACO, L_TRONCO = 32, 28, 112
CONT = 6


def _vec(ang, d):
    a = math.radians(ang)
    return (d * math.sin(a), d * math.cos(a))


def desenhar(tipo="homem", acao="parado", t=0.0, olhar=1, emocao=None, cor=None, escala=1.0):
    cor_roupa, acess = D.TIPOS.get(tipo, D.TIPOS["homem"])
    cor_roupa = D.hexc(cor or cor_roupa)
    if emocao not in D.EMOCOES:
        emocao = {"susto": "assustado", "triste": "triste", "comemorar": "feliz", "lutar": "bravo",
                  "cair": "assustado", "pensar": "neutro", "correr": "assustado"}.get(acao, "neutro")
    if tipo == "crianca":
        escala *= 0.75
    k = escala * SS
    Wc, Hc = int(1100 * k), int(1000 * k)
    ax, ay = Wc / 2, Hc - 50 * k
    im = Image.new("RGBA", (Wc, Hc), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    p = D.pose(acao, t)
    dirx = 1 if olhar >= 0 else -1
    rot = math.radians(p["rot"] * dirx)
    # respiracao / squash
    resp = 1 + 0.015 * math.sin(t * 3)

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
    tv = _vec(180 - tilt, TRONCO * k * resp)
    sh = (hip[0] + tv[0] * dirx, hip[1] + tv[1])
    hv = _vec(180 - tilt, (R_CAB * 0.82) * k)
    head = (sh[0] + hv[0] * dirx, sh[1] + hv[1])
    ombro = (hip[0] + _vec(180 - tilt, (TRONCO - 22) * k)[0] * dirx, hip[1] + _vec(180 - tilt, (TRONCO - 22) * k)[1])

    def capsula(a, b, larg, cor):
        a, b = R(a), R(b)
        w, o = larg * k, CONT * k
        d.line([a, b], fill=OUT, width=int(w + 2 * o))
        for q in (a, b):
            d.ellipse([q[0] - w / 2 - o, q[1] - w / 2 - o, q[0] + w / 2 + o, q[1] + w / 2 + o], fill=OUT)
        d.line([a, b], fill=cor, width=int(w))
        for q in (a, b):
            d.ellipse([q[0] - w / 2, q[1] - w / 2, q[0] + w / 2, q[1] + w / 2], fill=cor)

    def membro(pts, larg, cor):
        pts = [R(q) for q in pts]
        w, o = larg * k, CONT * k
        d.line(pts, fill=OUT, width=int(w + 2 * o), joint="curve")
        for q in (pts[0], pts[-1]):
            d.ellipse([q[0] - w / 2 - o, q[1] - w / 2 - o, q[0] + w / 2 + o, q[1] + w / 2 + o], fill=OUT)
        d.line(pts, fill=cor, width=int(w), joint="curve")
        for q in (pts[0], pts[-1]):
            d.ellipse([q[0] - w / 2, q[1] - w / 2, q[0] + w / 2, q[1] + w / 2], fill=cor)

    def bola(c, r, cor, o=CONT):
        c = R(c)
        r, o = r * k, o * k
        d.ellipse([c[0] - r - o, c[1] - r - o, c[0] + r + o, c[1] + r + o], fill=OUT)
        d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=cor)

    def sapato(foot, cor):
        f = R(foot)
        fx = f[0] + 10 * k * dirx
        w, h, o = 34 * k, 17 * k, CONT * k
        d.ellipse([fx - w - o, f[1] - h - o, fx + w + o, f[1] + h + o], fill=OUT)
        d.ellipse([fx - w, f[1] - h, fx + w, f[1] + h], fill=cor)

    def perna(ang, joelho, cor, cor_sapato):
        knee = add(hip, V(ang, COXA))
        foot = add(knee, V(ang - joelho, CANELA))
        membro([hip, knee, foot], L_PERNA, cor)
        sapato(foot, cor_sapato)

    def braco(ang, cotovelo, cor, frente=True):
        # bracos levantados abrem para o lado, para nao cobrir o rosto
        if ang > 100:
            extra = (ang - 100) * 0.45
            ang = 100 + extra if frente else -(100 + extra)
            cotovelo = min(cotovelo, 25) if frente else -min(cotovelo, 25)
        base_ombro = (ombro[0] + (40 if frente else -32) * k * dirx, ombro[1])
        el = add(base_ombro, V(ang, BRACO))
        hand = add(el, V(ang + cotovelo, ANTEBRACO))
        membro([base_ombro, el, hand], L_BRACO, cor)
        bola(hand, 17, SKIN, 5)
        return

    def _braco_antigo(ang, cotovelo, cor):
        el = add(ombro, V(ang, BRACO))
        hand = add(el, V(ang + cotovelo, ANTEBRACO))
        membro([ombro, el, hand], L_BRACO, cor)
        bola(hand, 17, SKIN, 5)

    calca = D.shade(cor_roupa, 0.5) if tipo not in ("papa", "cientista") else (70, 72, 84)
    sap = (60, 40, 30) if tipo not in ("soldado", "policial", "ladrao", "presidente") else (25, 25, 30)
    if tipo in ("papa", "rei", "rainha", "farao"):
        calca = D.shade(cor_roupa, 0.75)

    # capa atras
    if "capa" in acess:
        a, b = R((ombro[0] - 45 * k * dirx, ombro[1] - 10 * k)), R((ombro[0] + 25 * k * dirx, ombro[1] - 10 * k))
        onda = 8 * math.sin(t * 4)
        c1 = R((hip[0] - (120 + onda) * k * dirx, hip[1] + 110 * k))
        c2 = R((hip[0] + 10 * k * dirx, hip[1] + 110 * k))
        d.polygon([a, b, c2, c1], fill=(178, 26, 44), outline=OUT, width=int(6 * k))
    if "cabelo_longo" in acess:
        hc = R(head)
        r = R_CAB * k
        d.rounded_rectangle([hc[0] - r * 1.05, hc[1] - r * 0.5, hc[0] + r * 1.05, hc[1] + r * 1.35],
                            radius=r * 0.55, fill=(92, 52, 30), outline=OUT, width=int(6 * k))

    perna(p["tr"], p["kr"], D.shade(calca, 0.82), D.shade(sap, 0.8))
    perna(p["tl"], p["kl"], calca, sap)
    braco(p["ab"], p["eb"], D.shade(cor_roupa, 0.8), frente=False)
    # tronco (capsula larga)
    capsula(hip, (sh[0], sh[1] + 18 * k), L_TRONCO, cor_roupa)
    # detalhes da roupa
    hpt, spt = R(hip), R(sh)
    if tipo in ("rei", "rainha"):
        d.line([R((sh[0] - 50 * k, sh[1] + 30 * k)), R((sh[0] + 50 * k, sh[1] + 30 * k))], fill=(250, 250, 245), width=int(26 * k))
        for i in range(-2, 3):
            q = R((sh[0] + i * 20 * k, sh[1] + 30 * k))
            d.ellipse([q[0] - 3 * k, q[1] - 3 * k, q[0] + 3 * k, q[1] + 3 * k], fill=OUT)
    if tipo in ("soldado", "romano", "policial", "explorador", "pirata", "marinheiro", "trabalhador"):
        b = R((hip[0], hip[1] - 12 * k))
        d.line([(b[0] - 50 * k, b[1]), (b[0] + 50 * k, b[1])], fill=(55, 35, 20), width=int(14 * k))
        d.rectangle([b[0] - 10 * k, b[1] - 9 * k, b[0] + 10 * k, b[1] + 9 * k], fill=(230, 190, 60))
    if tipo == "papa":
        c = R((sh[0] + 4 * k * dirx, sh[1] + 70 * k))
        d.line([(c[0], c[1] - 30 * k), (c[0], c[1] + 30 * k)], fill=(230, 180, 40), width=int(10 * k))
        d.line([(c[0] - 18 * k, c[1] - 10 * k), (c[0] + 18 * k, c[1] - 10 * k)], fill=(230, 180, 40), width=int(10 * k))
    if "gravata" in acess:
        a = R((sh[0] + 6 * k * dirx, sh[1] + 20 * k))
        b = R((sh[0] + 6 * k * dirx, sh[1] + 90 * k))
        d.line([a, b], fill=(200, 30, 40), width=int(14 * k))
    # cabeca
    hc = R(head)
    r = R_CAB * k
    o = CONT * k
    d.ellipse([hc[0] - r - o, hc[1] - r - o, hc[0] + r + o, hc[1] + r + o], fill=OUT)
    d.ellipse([hc[0] - r, hc[1] - r, hc[0] + r, hc[1] + r], fill=SKIN)
    D._cabelo_e_chapeu(d, hc, r, k * R_CAB / 52, acess, dirx, antes_rosto=True)
    _rosto(d, hc, r, k, dirx, emocao, acess, t)
    D._cabelo_e_chapeu(d, hc, r, k * R_CAB / 52, acess, dirx, antes_rosto=False)
    braco(p["af"], p["ef"], cor_roupa)
    _reacao(d, hc, r, k, dirx, emocao, acao, t)
    small = im.reduce(SS)
    return small, (ax / SS, ay / SS)


def _rosto(d, hc, r, k, dirx, emo, acess, t):
    fx = hc[0] + r * 0.16 * dirx  # rosto levemente virado para onde olha
    ey = hc[1] - r * 0.02
    piscar = (t % 3.1) < 0.11 and emo not in ("assustado", "surpreso")
    w, h = r * 0.2, r * 0.27
    if emo in ("assustado", "surpreso"):
        w, h = r * 0.25, r * 0.33
    lw = max(2, int(r * 0.06))
    for off in (-0.3, 0.3):
        cx = fx + off * r
        if piscar:
            d.arc([cx - w, ey - h * 0.4, cx + w, ey + h * 0.6], 200, 340, fill=OUT, width=lw)
        else:
            d.ellipse([cx - w, ey - h, cx + w, ey + h], fill=(255, 255, 255), outline=OUT, width=lw)
            pr = r * (0.08 if emo in ("assustado", "surpreso") else 0.12)
            px, py = cx + r * 0.07 * dirx, ey + r * 0.03
            d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=OUT)
            d.ellipse([px - pr * 0.35 + pr * 0.3, py - pr * 0.6, px + pr * 0.25 + pr * 0.3, py], fill=(255, 255, 255))
        # sobrancelhas
        by = ey - h - r * 0.12
        inc = {"bravo": 0.14, "triste": -0.12, "surpreso": -0.02, "assustado": -0.1}.get(emo, 0.0)
        s = 1 if off < 0 else -1  # inclina para o centro
        dy_in = inc * r * s
        lift = -r * 0.1 if emo in ("surpreso", "assustado") else 0
        d.line([cx - w * 1.1, by - dy_in + lift, cx + w * 1.1, by + dy_in + lift], fill=OUT, width=int(lw * 1.4))
    if "mascara" in acess:
        d.rounded_rectangle([hc[0] - r, ey - h * 1.2, hc[0] + r, ey + h * 1.1], radius=r * 0.2, fill=OUT)
        for off in (-0.3, 0.3):
            cx = fx + off * r
            d.ellipse([cx - w * 0.8, ey - h * 0.7, cx + w * 0.8, ey + h * 0.7], fill=(255, 255, 255))
            d.ellipse([cx - r * 0.07, ey - r * 0.07, cx + r * 0.07, ey + r * 0.07], fill=OUT)
    if "tapa_olho" in acess:
        cx = fx + 0.3 * r * dirx
        d.ellipse([cx - w * 1.2, ey - h * 1.1, cx + w * 1.2, ey + h * 1.1], fill=OUT)
        d.line([hc[0] - r, ey - r * 0.45, hc[0] + r, ey + r * 0.1], fill=OUT, width=lw)
    if "oculos" in acess:
        for off in (-0.3, 0.3):
            cx = fx + off * r
            d.ellipse([cx - w * 1.35, ey - h * 1.15, cx + w * 1.35, ey + h * 1.15], outline=OUT, width=lw)
        d.line([fx - r * 0.07, ey, fx + r * 0.07, ey], fill=OUT, width=lw)
    # nariz e bochechas
    nx = fx + r * 0.2 * dirx
    d.ellipse([nx - r * 0.09, ey + r * 0.16, nx + r * 0.09, ey + r * 0.3], fill=SKIN_SH)
    for off in (-0.48, 0.48):
        cx = fx + off * r
        d.ellipse([cx - r * 0.13, ey + r * 0.28, cx + r * 0.13, ey + r * 0.4], fill=(248, 160, 150))
    barba = "barba" in acess or "barba_branca" in acess
    if barba:
        cb = (240, 240, 240) if "barba_branca" in acess else (100, 58, 32)
        d.chord([hc[0] - r * 0.98, hc[1] - r * 0.15, hc[0] + r * 0.98, hc[1] + r * 1.3], 0, 180,
                fill=cb, outline=OUT, width=lw)
    mx, my = fx + r * 0.05 * dirx, hc[1] + r * 0.5
    mw = r * 0.26
    if emo == "feliz":
        d.chord([mx - mw, my - mw * 0.7, mx + mw, my + mw * 0.9], 0, 180, fill=(120, 25, 35), outline=OUT, width=lw)
        d.chord([mx - mw * 0.55, my + mw * 0.15, mx + mw * 0.55, my + mw * 0.85], 0, 180, fill=(240, 110, 120))
    elif emo == "triste":
        d.arc([mx - mw * 0.8, my, mx + mw * 0.8, my + mw * 0.9], 200, 340, fill=OUT, width=lw)
    elif emo in ("assustado", "surpreso"):
        d.ellipse([mx - mw * 0.55, my - mw * 0.45, mx + mw * 0.55, my + mw * 0.8], fill=(120, 25, 35), outline=OUT, width=lw)
    elif emo == "bravo":
        d.rounded_rectangle([mx - mw * 0.8, my - mw * 0.15, mx + mw * 0.8, my + mw * 0.35], radius=mw * 0.15,
                            fill=(255, 255, 255), outline=OUT, width=lw)
        d.line([mx - mw * 0.8, my + mw * 0.1, mx + mw * 0.8, my + mw * 0.1], fill=OUT, width=max(1, lw // 2))
    else:
        d.arc([mx - mw * 0.6, my - mw * 0.5, mx + mw * 0.6, my + mw * 0.3], 20, 160, fill=OUT, width=lw)


def _reacao(d, hc, r, k, dirx, emo, acao, t):
    """Simbolos de desenho animado perto da cabeca."""
    x0, y0 = hc[0] + r * 0.95 * dirx, hc[1] - r * 0.95
    pul = 1 + 0.12 * math.sin(t * 9)
    lw = int(r * 0.07)
    if emo == "bravo":
        s = r * 0.22 * pul
        for ang in (45, 135, 225, 315):
            a = math.radians(ang)
            cx, cy = x0 + math.cos(a) * s * 0.9, y0 + math.sin(a) * s * 0.9
            d.arc([cx - s * 0.6, cy - s * 0.6, cx + s * 0.6, cy + s * 0.6], ang + 90, ang + 270, fill=(220, 30, 40), width=lw)
    elif emo == "assustado":
        for i, (dx, dy) in enumerate([(0, 0), (0.35, 0.45)]):
            gx, gy = x0 + dx * r * dirx, y0 + dy * r + 8 * k * math.sin(t * 6 + i)
            s = r * 0.13
            d.polygon([(gx, gy - s * 1.6), (gx - s, gy), (gx + s, gy)], fill=(110, 190, 250), outline=OUT, width=int(lw * 0.6))
            d.ellipse([gx - s, gy - s, gx + s, gy + s], fill=(110, 190, 250), outline=OUT, width=int(lw * 0.6))
    elif emo == "triste":
        gx, gy = hc[0] + r * 0.45 * dirx, hc[1] + r * 0.2 + (t * 60 * k) % (r * 0.6)
        s = r * 0.08
        d.ellipse([gx - s, gy - s * 1.3, gx + s, gy + s * 1.3], fill=(110, 190, 250))
    elif emo == "feliz" and acao in ("comemorar", "pular", "acenar"):
        for i, (dx, dy) in enumerate([(0, 0), (-1.9, 0.1), (-0.9, -0.45)]):
            sx, sy = x0 + dx * r * dirx, y0 + dy * r
            s = r * 0.14 * (1 + 0.4 * math.sin(t * 8 + i * 2))
            d.polygon([(sx, sy - s), (sx + s * 0.3, sy - s * 0.3), (sx + s, sy), (sx + s * 0.3, sy + s * 0.3),
                       (sx, sy + s), (sx - s * 0.3, sy + s * 0.3), (sx - s, sy), (sx - s * 0.3, sy - s * 0.3)], fill=(255, 220, 40))
    if acao == "pensar":
        bx, by = hc[0] + r * 1.3 * dirx, hc[1] - r * 1.35
        for i, s in enumerate((0.1, 0.16)):
            cx, cy = hc[0] + r * (0.75 + i * 0.25) * dirx, hc[1] - r * (0.75 + i * 0.3)
            d.ellipse([cx - r * s, cy - r * s, cx + r * s, cy + r * s], fill=(255, 255, 255), outline=OUT, width=int(lw * 0.6))
        d.ellipse([bx - r * 0.55, by - r * 0.38, bx + r * 0.55, by + r * 0.38], fill=(255, 255, 255), outline=OUT, width=int(lw * 0.7))
        n = int(t * 2.5) % 4
        for i in range(n):
            px = bx - r * 0.25 + i * r * 0.25
            d.ellipse([px - r * 0.06, by - r * 0.06, px + r * 0.06, by + r * 0.06], fill=OUT)
    if acao == "falar":
        bx, by = hc[0] + r * 1.35 * dirx, hc[1] - r * 1.1
        d.rounded_rectangle([bx - r * 0.55, by - r * 0.35, bx + r * 0.55, by + r * 0.35], radius=r * 0.2,
                            fill=(255, 255, 255), outline=OUT, width=int(lw * 0.7))
        d.polygon([(bx - r * 0.35 * dirx, by + r * 0.3), (bx - r * 0.65 * dirx, by + r * 0.6), (bx - r * 0.1 * dirx, by + r * 0.3)],
                  fill=(255, 255, 255))
        n = 1 + int(t * 3) % 3
        for i in range(n):
            px = bx - r * 0.25 + i * r * 0.25
            d.ellipse([px - r * 0.06, by - r * 0.06, px + r * 0.06, by + r * 0.06], fill=OUT)
