"""
Gerador de Shorts ANIMADOS de historias e curiosidades (100% gratis).

Uso:
    .venv\\Scripts\\python.exe estudio\\animacao_shorts.py "Tema do video"

O Claude Code escreve a historia em cenas e dirige cada uma: cenario, bonecos
(com roupa, acao, emocao, para onde olham) e objetos. Este script desenha e
anima tudo por codigo (bonequinho articulado andando, correndo, pulando...),
grava a narracao, poe efeitos sonoros, legenda com palavra amarela e musica.
"""

import argparse
import json
import math
import random
import re
import shutil
import subprocess
import sys
import time
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import historia_shorts as base  # noqa: E402  (voz, legenda, utilidades)
import desenhos as D  # noqa: E402
import boneco2 as B2  # noqa: E402

W, H, FPS, SR = base.W, base.H, 30, 44100
ROOT = base.ROOT
TEXT_FONT = str(base.FONT_FILE)
D.FONT = TEXT_FONT
OUT_DIR = ROOT / "estudio" / "animados"
CHAO = 1340  # linha onde ficam os pes dos bonecos

FUNDOS = ["campo", "cidade", "palacio", "guerra", "deserto", "floresta", "noite", "mar", "ceu", "espaco",
          "papel", "neutro"]
ANIMS_OBJ = ["surgir", "cair", "flutuar", "balancar", "girar", "pulsar", "atravessar", "entrar_esquerda",
             "entrar_direita", "aproximar", "tremer"]
LUGAR_X = {"esquerda": 290, "centro": 540, "direita": 790}
TAM = {"p": 230, "m": 360, "g": 520}
NO_CHAO = {"castelo", "casa", "predio", "igreja", "piramide", "arvore", "palmeira", "montanha", "vulcao",
           "tenda", "canhao", "carro", "trem", "trono", "bau_tesouro", "placa", "bandeira", "muro", "porta",
           "saco_dinheiro", "barra_ouro", "ilha"}
VEL = {"andar": 150, "correr": 380, "empurrar": 70}

PLAN_PROMPT = """Voce e roteirista e diretor de um canal brasileiro de Shorts ANIMADOS com bonequinhos (estilo desenho simples, tipo stickman) que contam historias reais e curiosidades.
Tema: {tema}

1) ROTEIRO (portugues do Brasil), em {n} cenas, contado como HISTORIA:
- Cena 1: gancho com misterio ou choque que prenda em 2 segundos.
- Personagens com emocao, tensao crescente e "loops de curiosidade" ("Mas ninguem esperava o que viria depois...").
- Reviravolta perto do fim. Ultima cena: impacto ou pergunta que gere comentarios.
- Frases curtas e faladas. Nada de "ola", "neste video", "voce sabia". Fatos reais e corretos.
- Total entre 130 e 170 palavras. Cada cena 1 ou 2 frases (8 a 22 palavras).
- Marque UMA palavra-chave por cena entre asteriscos: *1494*.

2) DIRECAO (o desenho precisa MOSTRAR literalmente o que a frase conta, como num desenho animado):
- "fundo": um de {fundos}. Com bonecos, prefira fundos com chao (campo, cidade, palacio, guerra, deserto, floresta, noite, neutro). "mar"/"ceu"/"espaco" sao para cenas com navio, aviao, planeta etc. sem bonecos.
- "personagens": 0 a 2. Cada um:
  "tipo": um de {tipos},
  "acao": um de {acoes},
  "lugar": esquerda | centro | direita,
  "olhar": esquerda | direita (rivais se olham: quem esta a esquerda olha para a direita),
  "emocao": um de {emocoes},
  "rotulo": nome curto em CAIXA ALTA que aparece em cima da cabeca (ex: "PORTUGAL", "D. JOAO II", "PAPA") ou "",
  "cor": "" ou uma cor hex para a roupa (ex: "#0a7d3b" para Portugal).
- "objetos": 0 a 2. Cada um:
  "tipo": um de {objetos},
  "lugar": esquerda | centro | direita | topo,
  "tamanho": p | m | g,
  "anim": um de {anims},
  "pais": para "bandeira", um de {bandeiras}; senao "",
  "texto": texto curto para "placa"/"documento"/"jornal" (ex: "TRATADO"); senao "".
- Nao coloque personagem e objeto grande no mesmo lugar. Use a cena toda: ex. rei a esquerda apontando + bandeira a direita.
- MOVIMENTO: em pelo menos metade das cenas os bonecos devem fazer algo ativo (andar, correr, lutar, pular, comemorar, susto, empurrar, cair, falar). Evite "parado". Use "falar" quando alguem esta discutindo/negociando e "pensar" quando alguem planeja.
- EMOCAO: cada boneco tem uma emocao que combina com a frase (bravo, assustado, feliz, triste, surpreso). Evite "neutro".
- VARIEDADE: nao use o mesmo fundo em mais de 2 cenas seguidas; troque de lugar quando a historia muda de lugar (palacio -> mar -> campo -> guerra...).
- CONTINUIDADE: o mesmo personagem mantem sempre o mesmo "tipo", "cor" e "rotulo" no video inteiro.
- "numero": opcional, ano/valor curto que aparece GIGANTE (ex: "1494", "300 MIL") ou "".
- "efeito": "tremor" (explosao, guerra, choque), "flash" (revelacao) ou "nenhum".

Responda SOMENTE com JSON valido, sem markdown:
{{"titulo": "titulo curioso", "descricao": "descricao curta com 3 hashtags", "cenas": [{{"texto": "frase com *destaque*", "fundo": "palacio", "personagens": [{{"tipo": "rei", "acao": "apontar", "lugar": "esquerda", "olhar": "direita", "emocao": "bravo", "rotulo": "PORTUGAL", "cor": ""}}], "objetos": [{{"tipo": "mapa", "lugar": "direita", "tamanho": "m", "anim": "surgir", "pais": "", "texto": ""}}], "numero": "", "efeito": "nenhum"}}]}}
"""


# ------------------------------------------------------------------ utilidades
def lerp(a, b, t):
    return a + (b - a) * t


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out_back(t, s=1.70158):
    t = t - 1
    return t * t * ((s + 1) * t + s) + 1


def ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def ease_out_bounce(t):
    n1, d1 = 7.5625, 2.75
    if t < 1 / d1:
        return n1 * t * t
    if t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    if t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    t -= 2.625 / d1
    return n1 * t * t + 0.984375


hexc = D.hexc


def vgrad(c1, c2, w=W, h=H):
    a = np.linspace(0, 1, h)[:, None, None]
    arr = np.array(hexc(c1), float) * (1 - a) + np.array(hexc(c2), float) * a
    return Image.fromarray(np.broadcast_to(arr, (h, w, 3)).astype(np.uint8), "RGB")


def vignette(im, strength=0.55):
    y, x = np.ogrid[:H, :W]
    d = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2) / math.sqrt(2)
    mask = 1 - strength * np.clip(d, 0, 1) ** 1.6
    arr = np.asarray(im, float) * mask[..., None]
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGB")


_fc = {}


def fonte(size):
    if size not in _fc:
        _fc[size] = ImageFont.truetype(TEXT_FONT, size)
    return _fc[size]


def texto_img(txt, size, cor=(255, 215, 0), contorno=10):
    f = fonte(size)
    l, t, r, b = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), txt, font=f, stroke_width=contorno)
    im = Image.new("RGBA", (r - l + 20, b - t + 20), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10 - l, 10 - t), txt, font=f, fill=cor, stroke_width=contorno, stroke_fill=(0, 0, 0))
    return im


def rotulo_img(txt):
    f = fonte(42)
    l, t, r, b = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), txt, font=f)
    im = Image.new("RGBA", (r - l + 52, b - t + 28), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=20, fill=(15, 15, 25, 215))
    d.text((26 - l, 14 - t), txt, font=f, fill=(255, 255, 255))
    return im


def colar(frame, spr, cx, cy, escala=1.0, rot=0.0, alpha=1.0):
    if spr is None or escala <= 0.02 or alpha <= 0.01:
        return
    im = spr
    if abs(escala - 1) > 0.01:
        im = im.resize((max(1, int(im.width * escala)), max(1, int(im.height * escala))), Image.BILINEAR)
    if abs(rot) > 0.3:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 0.99:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    frame.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)


# ------------------------------------------------------------------ cenarios
class Fundo:
    def __init__(self, tipo, seed):
        self.tipo = tipo if tipo in FUNDOS else "neutro"
        self.rng = random.Random(seed)
        self.base = self._base()
        r = self.rng
        self.estrelas = [(r.randrange(W), r.randrange(int(H * 0.6)), r.uniform(1.5, 4), r.uniform(0, 6.28))
                         for _ in range(90)]
        self.nuvens = [(r.uniform(0, W + 400), r.uniform(150, 600), r.uniform(0.7, 1.3), r.uniform(15, 40))
                       for _ in range(5)]
        self.particulas = [(r.uniform(0, W), r.uniform(0, H), r.uniform(40, 140), r.uniform(3, 9))
                           for _ in range(45)]

    def _base(self):
        t, r, S = self.tipo, self.rng, 2
        if t == "mar":
            full = Image.new("RGB", (W * S, H * S))
            full.paste(vgrad("#24345f", "#f39a63", W * S, 1000 * S), (0, 0))
            d = ImageDraw.Draw(full)
            d.ellipse([W * S / 2 - 170 * S, 830 * S, W * S / 2 + 170 * S, 1170 * S], fill=hexc("#ffd36e"))
            full.paste(vgrad("#2368a2", "#0a1f3d", W * S, (H - 1000) * S), (0, 1000 * S))
        elif t == "ceu":
            full = vgrad("#3d8fd6", "#cdeeff", W * S, H * S)
        elif t == "noite":
            full = vgrad("#070b1f", "#2c2f63", W * S, H * S)
            d = ImageDraw.Draw(full)
            d.ellipse([780 * S, 260 * S, 960 * S, 440 * S], fill=hexc("#f5f1cf"))
            d.rectangle([0, CHAO * S, W * S, H * S], fill=hexc("#151a33"))
        elif t == "espaco":
            full = vgrad("#04010d", "#1d0b40", W * S, H * S)
            d = ImageDraw.Draw(full)
            for _ in range(220):
                x, y, rr = r.uniform(0, W * S), r.uniform(0, H * S), r.uniform(1, 3) * S
                d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(255, 255, 255))
        elif t == "deserto":
            full = vgrad("#f2a54a", "#fbe0a0", W * S, H * S)
            d = ImageDraw.Draw(full)
            d.ellipse([700 * S, 260 * S, 940 * S, 500 * S], fill=hexc("#fff3b0"))
            for i, (yb, cor) in enumerate([(1100, "#e9b864"), (CHAO - 20, "#d9a050")]):
                pts = [(x * S, (yb + 50 * math.sin(x / 170 + i * 2)) * S) for x in range(0, W + 20, 20)]
                d.polygon(pts + [(W * S, H * S), (0, H * S)], fill=hexc(cor))
            d.rectangle([0, CHAO * S, W * S, H * S], fill=hexc("#c98d40"))
        elif t == "floresta":
            full = vgrad("#7cc6f2", "#dff3ff", W * S, H * S)
            d = ImageDraw.Draw(full)
            pts = [(x * S, (1050 + 70 * math.sin(x / 210)) * S) for x in range(0, W + 20, 20)]
            d.polygon(pts + [(W * S, H * S), (0, H * S)], fill=hexc("#5aa865"))
            for _ in range(10):
                x, y, h = r.uniform(0, W), r.uniform(1080, 1250), r.uniform(160, 300)
                d.polygon([(x * S, (y - h) * S), ((x - h / 3) * S, y * S), ((x + h / 3) * S, y * S)], fill=hexc("#2f6b3c"))
            d.rectangle([0, CHAO * S, W * S, H * S], fill=hexc("#3f8a47"))
        elif t == "cidade":
            full = vgrad("#1b2547", "#e68867", W * S, H * S)
            d = ImageDraw.Draw(full)
            x = -20
            while x < W:
                bw, bh = r.uniform(110, 210), r.uniform(350, 800)
                d.rectangle([x * S, (CHAO - bh) * S, (x + bw) * S, CHAO * S], fill=hexc("#232842"))
                for wy in range(int(CHAO - bh + 30), CHAO - 30, 60):
                    for wx in range(int(x + 20), int(x + bw - 30), 45):
                        if r.random() < 0.4:
                            d.rectangle([wx * S, wy * S, (wx + 22) * S, (wy + 30) * S], fill=hexc("#ffd57a"))
                x += bw + r.uniform(5, 25)
            d.rectangle([0, CHAO * S, W * S, H * S], fill=hexc("#3b3f52"))
        elif t == "palacio":
            full = vgrad("#7a2232", "#3a0f18", W * S, H * S)
            d = ImageDraw.Draw(full)
            for cx in (70, 1010):
                d.rectangle([(cx - 55) * S, 200 * S, (cx + 55) * S, CHAO * S], fill=hexc("#d9c49c"))
                d.rectangle([(cx - 75) * S, 170 * S, (cx + 75) * S, 230 * S], fill=hexc("#c4ad80"))
            for i in range(9):
                x0 = i * 130 - 40
                d.pieslice([x0 * S, -120 * S, (x0 + 220) * S, 260 * S], 0, 180, fill=hexc("#a01c2c"))
            for row in range(10):
                for col in range(10):
                    cor = "#2a1810" if (row + col) % 2 else "#c9a46a"
                    y0 = CHAO + row * 60
                    d.rectangle([col * 108 * S, y0 * S, (col + 1) * 108 * S, (y0 + 60) * S], fill=hexc(cor))
        elif t == "guerra":
            full = vgrad("#220707", "#b0401c", W * S, H * S)
            fum = Image.new("RGB", (W * S, H * S))
            fd = ImageDraw.Draw(fum)
            for _ in range(10):
                x, y, rr = r.uniform(0, W * S), r.uniform(200 * S, 1200 * S), r.uniform(150, 350) * S
                fd.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(30, 20, 20))
            full = Image.blend(full, fum.filter(ImageFilter.GaussianBlur(90 * S)), 0.45)
            d = ImageDraw.Draw(full)
            pts = [(x * S, (CHAO - 30 + 30 * math.sin(x / 150)) * S) for x in range(0, W + 20, 20)]
            d.polygon(pts + [(W * S, H * S), (0, H * S)], fill=hexc("#3a2418"))
        elif t == "papel":
            arr = np.full((H, W, 3), hexc("#efdcae"), float)
            arr += np.random.default_rng(r.randrange(10 ** 6)).normal(0, 7, (H, W, 1))
            full = vignette(Image.fromarray(arr.clip(0, 255).astype(np.uint8)), 0.6).resize((W * S, H * S))
        elif t == "campo":
            full = vgrad("#7fcaf7", "#e3f6ff", W * S, H * S)
            d = ImageDraw.Draw(full)
            d.ellipse([760 * S, 230 * S, 960 * S, 430 * S], fill=hexc("#ffe27a"))
            pts = [(x * S, (1150 + 40 * math.sin(x / 260)) * S) for x in range(0, W + 20, 20)]
            d.polygon(pts + [(W * S, H * S), (0, H * S)], fill=hexc("#7cc35a"))
            d.rectangle([0, CHAO * S, W * S, H * S], fill=hexc("#5fa844"))
        else:  # neutro
            full = vgrad("#2b3654", "#121729", W * S, H * S)
            d = ImageDraw.Draw(full)
            d.rectangle([0, CHAO * S, W * S, H * S], fill=hexc("#0d1120"))
        im = full.resize((W, H), Image.LANCZOS)
        return vignette(im, 0.3) if t != "papel" else im

    def quadro(self, t):
        im = self.base.copy()
        d = ImageDraw.Draw(im)
        tipo = self.tipo
        if tipo == "mar":
            for k in range(14):
                y0 = 1030 + k * k * 4.5 + k * 20
                amp, fase = 6 + k * 1.2, t * (1.2 + k * 0.08) + k
                pts = [(x, y0 + amp * math.sin(x / (70 + k * 6) + fase)) for x in range(0, W + 30, 30)]
                d.line(pts, fill=(120, 180, 230) if k % 2 else (70, 130, 200), width=4 + k // 4)
        if tipo in ("ceu", "floresta", "campo"):
            for x0, y0, sc, vel in self.nuvens:
                x = (x0 + t * vel) % (W + 500) - 250
                for dx, dy, rr in [(0, 0, 70), (60, -25, 80), (125, 0, 65), (60, 20, 70)]:
                    rr *= sc
                    d.ellipse([x + dx * sc - rr, y0 + dy * sc - rr, x + dx * sc + rr, y0 + dy * sc + rr], fill=(255, 255, 255))
        if tipo in ("noite", "espaco"):
            for x, y, rr, fase in self.estrelas:
                b = 0.5 + 0.5 * math.sin(t * 2.5 + fase)
                c = int(150 + 105 * b)
                rr2 = rr * (0.6 + 0.6 * b)
                d.ellipse([x - rr2, y - rr2, x + rr2, y + rr2], fill=(c, c, min(255, c + 20)))
        if tipo == "guerra":
            for x0, y0, vel, rr in self.particulas:
                y = (y0 - t * vel) % H
                x = x0 + 25 * math.sin(t + y0)
                d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(255, 140 + int(rr * 8), 40))
        if tipo in ("neutro", "deserto", "palacio"):
            for x0, y0, vel, rr in self.particulas[:25]:
                y = (y0 - t * vel * 0.3) % H
                d.ellipse([x0 - rr / 2, y - rr / 2, x0 + rr / 2, y + rr / 2], fill=(255, 235, 200))
        return im


# ------------------------------------------------------------------ atores
def chave_personagem(spec):
    return f"{spec.get('tipo')}|{(spec.get('rotulo') or '').strip().upper()}"


class Personagem:
    ENTRADA_DUR = 0.85

    def __init__(self, spec, idx, dur, ja_estava=False):
        self.tipo = spec.get("tipo") if spec.get("tipo") in D.TIPOS else "homem"
        self.acao = spec.get("acao") if spec.get("acao") in D.ACOES else "parado"
        lugar = spec.get("lugar") if spec.get("lugar") in LUGAR_X else "centro"
        self.x0 = LUGAR_X[lugar]
        olhar = spec.get("olhar")
        if olhar not in ("esquerda", "direita"):
            olhar = "direita" if lugar == "esquerda" else "esquerda" if lugar == "direita" else "direita"
        self.dir = 1 if olhar == "direita" else -1
        self.emocao = spec.get("emocao")
        self.cor = spec.get("cor") if re.fullmatch(r"#[0-9a-fA-F]{6}", spec.get("cor") or "") else None
        rot = (spec.get("rotulo") or "").strip().upper()[:20]
        self.rot = rotulo_img(rot) if rot else None
        self.dur = dur
        self.vel = VEL.get(self.acao, 0)
        self.ja_estava = ja_estava
        self.entra_andando = False
        if ja_estava:
            self.entrada = 0.0
        else:
            self.entrada = 0.05 + 0.35 * idx
            if self.vel:  # ja chega andando/correndo e atravessa
                self.x0 -= self.dir * self.vel * 0.9
            else:  # entra andando pela lateral ate o seu lugar
                self.entra_andando = True
                if lugar == "esquerda" or (lugar == "centro" and self.dir < 0):
                    self.x_ini = -170
                else:
                    self.x_ini = W + 170

    def posicao(self, t):
        te = t - self.entrada
        if self.entra_andando and te < self.ENTRADA_DUR:
            return lerp(self.x_ini, self.x0, te / self.ENTRADA_DUR)
        return self.x0 + self.dir * self.vel * te

    def desenhar(self, frame, t):
        te = t - self.entrada
        if te < 0:
            return
        x = self.posicao(t)
        if self.entra_andando and te < self.ENTRADA_DUR:
            acao, dirx, ta = "andar", (1 if self.x0 > self.x_ini else -1), te
            emo = "neutro" if self.emocao in (None, "", "neutro") else self.emocao
        else:
            acao, dirx = self.acao, self.dir
            ta = te - (self.ENTRADA_DUR if self.entra_andando else 0)
            emo = self.emocao
        im, (ax, ay) = B2.desenhar(self.tipo, acao, ta, dirx, emo, self.cor, escala=1.25)
        d = ImageDraw.Draw(frame)
        # sombra no chao
        d.ellipse([x - 85, CHAO - 14, x + 85, CHAO + 14], fill=(0, 0, 0))
        if acao == "correr":  # linhas de velocidade
            for i, yy in enumerate((CHAO - 330, CHAO - 230, CHAO - 130)):
                comp = 120 + 40 * math.sin(t * 20 + i)
                xs = x - dirx * (130 + i * 15)
                d.line([(xs, yy), (xs - dirx * comp, yy)], fill=(255, 255, 255), width=8)
        frame.paste(im, (int(x - ax), int(CHAO - ay)), im)
        if self.rot is not None:
            bb = im.getbbox()
            topo = CHAO - ay + (bb[1] if bb else 0)
            colar(frame, self.rot, x, topo - 40, 1.0, 0, 1.0)


class Objeto:
    def __init__(self, spec, idx, dur, fundo):
        self.tipo = spec.get("tipo") if spec.get("tipo") in D.OBJETOS else "interrogacao"
        self.anim = spec.get("anim") if spec.get("anim") in ANIMS_OBJ else "surgir"
        lugar = spec.get("lugar") if spec.get("lugar") in ("esquerda", "centro", "direita", "topo") else "centro"
        tam = TAM.get(spec.get("tamanho"), TAM["m"])
        pais = spec.get("pais") if spec.get("pais") in D.BANDEIRAS else ""
        self.spr = D.desenhar_objeto(self.tipo, tam, (spec.get("texto") or "")[:14], pais)
        self.x = LUGAR_X.get(lugar, 540)
        if lugar == "topo":
            self.y = 560
        elif self.tipo in ("navio", "caravela") and fundo == "mar":
            self.y = 1000 - self.spr.height * 0.25
        elif self.tipo in NO_CHAO:
            self.y = CHAO - self.spr.height / 2 + 10
        else:
            self.y = 820
        self.entrada = 0.2 + 0.35 * idx
        self.dur = dur
        self.seed = idx * 1.3

    def desenhar(self, frame, t):
        te = t - self.entrada
        if te < 0:
            return
        a, x, y, s, r = self.anim, self.x, self.y, 1.0, 0.0
        p = clamp(te / 0.45)
        alpha = clamp(te / 0.12)
        bob = 8 * math.sin(2 * math.pi * 0.6 * te + self.seed)
        if a == "entrar_esquerda":
            x = lerp(-self.spr.width, self.x, ease_out_back(p))
        elif a == "entrar_direita":
            x = lerp(W + self.spr.width, self.x, ease_out_back(p))
        elif a == "cair":
            y = lerp(-self.spr.height, self.y, ease_out_bounce(clamp(te / 0.7)))
        elif a == "atravessar":
            x = lerp(-self.spr.width * 0.6, W + self.spr.width * 0.6, clamp(te / max(self.dur - self.entrada, 0.5)))
            y += bob; r = 3 * math.sin(te * 2)
        elif a == "aproximar":
            s = lerp(0.35, 1.15, ease_out_cubic(clamp(te / max(self.dur - self.entrada, 0.5))))
        else:
            s = ease_out_back(p)
            if a == "balancar":
                r = 7 * math.sin(2 * math.pi * 0.5 * te); y += 12 * math.sin(2 * math.pi * 0.5 * te + 1)
            elif a == "tremer":
                x += 10 * math.sin(te * 55); r = 3 * math.sin(te * 40)
            elif a == "girar":
                r = -te * 60
            elif a == "pulsar":
                s *= 1 + 0.08 * math.sin(2 * math.pi * 1.6 * te)
            elif a == "flutuar":
                y += 25 * math.sin(2 * math.pi * 0.4 * te + self.seed)
        if self.tipo == "fogo":
            s *= 1 + 0.06 * math.sin(te * 17)
        colar(frame, self.spr, x, y, s, r, alpha)


class Cena:
    def __init__(self, spec, inicio, dur, idx, anteriores=None, fundo_anterior=None):
        self.inicio, self.dur, self.idx = inicio, dur, idx
        fundo = spec.get("fundo", "neutro")
        self.fundo = Fundo(fundo, seed=idx * 97 + 3)
        self.objetos = [Objeto(o, i, dur, fundo) for i, o in enumerate((spec.get("objetos") or [])[:2])]
        anteriores = anteriores or set()
        mesmo_lugar = fundo == fundo_anterior
        self.pers = [Personagem(p, i, dur, ja_estava=mesmo_lugar and chave_personagem(p) in anteriores)
                     for i, p in enumerate((spec.get("personagens") or [])[:2])]
        self.chaves = {chave_personagem(p) for p in (spec.get("personagens") or [])[:2]}
        self.fundo_nome = fundo
        # camera: zoom lento na direcao dos personagens, alternando aproximar/afastar
        self.zoom_in = idx % 3 != 2
        num = (spec.get("numero") or "").strip().upper()[:12]
        self.numero = texto_img(num, 210 if len(num) <= 6 else 150) if num else None
        self.efeito = spec.get("efeito", "nenhum")

    def entradas(self):
        return [self.inicio + a.entrada for a in self.objetos + self.pers]

    def quadro(self, t_abs, progresso):
        t = t_abs - self.inicio
        frame = self.fundo.quadro(t)
        for o in self.objetos:
            o.desenhar(frame, t)
        for p in self.pers:
            p.desenhar(frame, t)
        # camera viva
        prog = clamp(t / max(self.dur, 0.1))
        z = 1 + 0.09 * (prog if self.zoom_in else 1 - prog)
        if self.pers:
            fx = sum(p.posicao(t) for p in self.pers) / len(self.pers)
        else:
            fx = W / 2
        fy = CHAO - 380
        cw, ch = W / z, H / z
        x0 = clamp(fx - cw / 2, 0, W - cw)
        y0 = clamp(fy - ch / 2, 0, H - ch)
        if z > 1.005:
            frame = frame.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))
        if self.numero is not None:
            s = ease_out_back(clamp((t - 0.05) / 0.4)) * (1 + 0.04 * math.sin(t * 5))
            colar(frame, self.numero, W / 2, 300, s, 0, clamp(t / 0.1))
        if self.efeito == "tremor" and t < 0.9:
            k = (0.9 - t) / 0.9
            moved = Image.new("RGB", (W, H))
            moved.paste(frame, (int(28 * k * math.sin(t * 75)), int(22 * k * math.cos(t * 63))))
            frame = moved
        if t < 0.2:
            z = 1 + 0.07 * (1 - t / 0.2)
            big = frame.resize((int(W * z), int(H * z)), Image.BILINEAR)
            ox, oy = (big.width - W) // 2, (big.height - H) // 2
            frame = big.crop((ox, oy, ox + W, oy + H))
        if self.efeito == "flash" and t < 0.3:
            frame = Image.blend(frame, Image.new("RGB", (W, H), (255, 255, 255)), 0.85 * (1 - t / 0.3))
        ImageDraw.Draw(frame).rectangle([0, 0, int(W * progresso), 12], fill=(255, 215, 0))
        return frame


# ------------------------------------------------------------------ som
def sfx_track(total, inicios_cena, entradas, tremores, seed=1):
    n = int(total * SR) + SR
    buf = np.zeros(n, np.float32)
    rng = np.random.default_rng(seed)

    def add(start, sig):
        i = int(start * SR)
        if i >= n:
            return
        j = min(n, i + len(sig))
        buf[i:j] += sig[: j - i]

    L = int(0.45 * SR)
    tt = np.linspace(0, 1, L)
    ruido = np.convolve(rng.normal(0, 1, L), np.ones(40) / 40, mode="same")
    whoosh = (ruido * np.sin(np.pi * tt) ** 2 * 0.9).astype(np.float32)
    Lp = int(0.12 * SR)
    tp = np.arange(Lp) / SR
    pop = (np.sin(2 * np.pi * np.cumsum(np.linspace(900, 260, Lp)) / SR) * np.exp(-tp * 30) * 0.3).astype(np.float32)
    Lb = int(0.9 * SR)
    tb = np.arange(Lb) / SR
    boom = (np.sin(2 * np.pi * 55 * tb) * np.exp(-tb * 5) * 0.8
            + np.convolve(rng.normal(0, 1, Lb), np.ones(60) / 60, mode="same") * np.exp(-tb * 7) * 0.9).astype(np.float32)
    for s in inicios_cena[1:]:
        add(max(s - 0.12, 0), whoosh)
    for s in entradas:
        add(s, pop)
    for s in tremores:
        add(s, boom)
    return np.clip(buf, -1, 1)


def salvar_wav(path, sig):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((sig * 32767).astype(np.int16).tobytes())


# ------------------------------------------------------------------ principal
def planejar(tema, n):
    prompt = PLAN_PROMPT.format(
        tema=tema, n=n, fundos=" | ".join(FUNDOS), tipos=" | ".join(D.TIPOS), acoes=" | ".join(D.ACOES),
        emocoes=" | ".join(D.EMOCOES), objetos=", ".join(D.OBJETOS), anims=" | ".join(ANIMS_OBJ),
        bandeiras=", ".join(D.BANDEIRAS))
    for tentativa in range(3):
        raw = base.llm._strip_code_fence(base.llm._generate_response(prompt) or "").strip()
        m = re.search(r"\{.*\}", raw, re.S)
        try:
            plan = json.loads(m.group(0) if m else raw)
            cenas = [c for c in plan["cenas"] if c.get("texto", "").strip()]
            if len(cenas) >= 4:
                plan["cenas"] = cenas
                return plan
        except Exception as exc:  # noqa: BLE001
            base.log(f"roteiro invalido (tentativa {tentativa + 1}): {exc}")
    raise RuntimeError("o Claude Code nao devolveu um roteiro valido")


def main():
    ap = argparse.ArgumentParser(description="Gera um Short animado de historia/curiosidade.")
    ap.add_argument("tema")
    ap.add_argument("--cenas", type=int, default=10)
    ap.add_argument("--velocidade", default="+10%")
    ap.add_argument("--musica", type=float, default=0.07)
    ap.add_argument("--roteiro", help="JSON de roteiro pronto (pula o Claude Code)")
    args = ap.parse_args()

    if args.roteiro:
        plan = json.loads(Path(args.roteiro).read_text(encoding="utf-8"))
    else:
        base.log("1/5 Claude Code escrevendo e dirigindo a historia...")
        plan = planejar(args.tema, args.cenas)
    work = OUT_DIR / f"{time.strftime('%Y%m%d-%H%M%S')}-{base.slugify(plan.get('titulo') or args.tema)}"
    work.mkdir(parents=True, exist_ok=True)
    (work / "roteiro.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    base.log(f"   titulo: {plan.get('titulo')} ({len(plan['cenas'])} cenas)")

    base.log("2/5 gravando a narracao cena por cena...")
    palavras, audios, duracoes, off = [], [], [], 0.0
    pausa = 0.15
    for i, c in enumerate(plan["cenas"]):
        destaque = {base.norm(x) for d in re.findall(r"\*([^*]+)\*", c["texto"]) for x in d.split()}
        mp3 = work / f"voz_{i:02d}.mp3"
        ws = base.tts(c["texto"].replace("*", ""), mp3, args.velocidade)
        dur = base.probe_duration(mp3) + pausa
        for s, e, txt in ws:
            palavras.append({"start": off + s, "end": off + e, "text": txt, "cena": i,
                             "destaque": base.norm(txt) in destaque and base.norm(txt) != ""})
        audios.append(mp3)
        duracoes.append(dur)
        off += dur
    total = off
    base.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"anullsrc=r={SR}:cl=mono", "-t", str(pausa),
              "pausa.wav"], cwd=work)
    for mp3 in audios:  # normaliza cada trecho para wav (concat exato)
        base.run(["ffmpeg", "-y", "-v", "error", "-i", mp3.name, "-ar", str(SR), "-ac", "1", mp3.stem + ".wav"], cwd=work)
    (work / "voz_lista.txt").write_text("".join(f"file '{m.stem}.wav'\nfile 'pausa.wav'\n" for m in audios), encoding="utf-8")
    base.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", "voz_lista.txt",
              "-c:a", "pcm_s16le", "narracao.wav"], cwd=work)
    base.log(f"   narracao: {total:.1f}s")

    base.log("3/5 desenhando as animacoes...")
    cenas, ini = [], 0.0
    for i, (c, dur) in enumerate(zip(plan["cenas"], duracoes)):
        ant = cenas[-1] if cenas else None
        cenas.append(Cena(c, ini, dur, i, ant.chaves if ant else None, ant.fundo_nome if ant else None))
        ini += dur
    nframes = int(round(total * FPS))
    enc = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "visual.mp4"],
        cwd=work, stdin=subprocess.PIPE)
    ci, t0 = 0, time.time()
    for f in range(nframes):
        t = f / FPS
        while ci + 1 < len(cenas) and t >= cenas[ci + 1].inicio:
            ci += 1
        enc.stdin.write(cenas[ci].quadro(t, (f + 1) / nframes).tobytes())
        if f % (FPS * 10) == 0 and f:
            base.log(f"   {t:.0f}s de {total:.0f}s ({time.time() - t0:.0f}s)")
    enc.stdin.close()
    if enc.wait() != 0:
        raise RuntimeError("falha ao codificar o video")

    base.log("4/5 efeitos sonoros e legendas...")
    salvar_wav(work / "sfx.wav", sfx_track(total, [c.inicio for c in cenas], [s for c in cenas for s in c.entradas()],
                                           [c.inicio for c in cenas if c.efeito == "tremor"]))
    base.build_ass(palavras, work / "legendas.ass", y_pos=1560)
    (work / "fonts").mkdir(exist_ok=True)
    shutil.copy(base.FONT_FILE, work / "fonts" / base.FONT_FILE.name)

    base.log("5/5 juntando tudo...")
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", "visual.mp4", "-i", "narracao.wav", "-i", "sfx.wav"]
    songs = sorted(base.SONGS_DIR.glob("*.mp3"))
    if args.musica > 0 and songs:
        cmd += ["-stream_loop", "-1", "-i", str(random.choice(songs))]
        fc = (f"[0:v]subtitles=legendas.ass:fontsdir=fonts[v];[2:a]volume=0.5[s];"
              f"[3:a]volume={args.musica},afade=t=out:st={max(total - 2, 0):.2f}:d=2[m];"
              f"[1:a][s][m]amix=inputs=3:duration=first:normalize=0[a]")
    else:
        fc = "[0:v]subtitles=legendas.ass:fontsdir=fonts[v];[2:a]volume=0.5[s];[1:a][s]amix=inputs=2:duration=first:normalize=0[a]"
    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", f"{total:.2f}", "-c:v", "libx264",
            "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", "final.mp4"]
    base.run(cmd, cwd=work)
    (work / "publicar.txt").write_text(
        f"TITULO:\n{plan.get('titulo', '')}\n\nDESCRICAO:\n{plan.get('descricao', '')}\n\nROTEIRO:\n"
        + "\n".join(c["texto"].replace("*", "") for c in plan["cenas"]) + "\n", encoding="utf-8")
    for tmp in list(work.glob("voz_*")) + [work / "visual.mp4", work / "pausa.wav", work / "sfx.wav"]:
        tmp.unlink(missing_ok=True)
    base.log(f"PRONTO: {work / 'final.mp4'}")
    print(f"VIDEO_FILE={work / 'final.mp4'}")


if __name__ == "__main__":
    main()
