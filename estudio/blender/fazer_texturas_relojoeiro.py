"""Texturas de O Relojoeiro: relogio parado em 4h40, janela com chuva, telas das cameras, livro da portaria, marmore."""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

AQUI = Path(__file__).resolve().parent
OUT = AQUI / "texturas"
FONTES = AQUI.parent.parent / "resource" / "fonts"
BOLD = str(FONTES / "BeVietnamPro-Bold.ttf")
MAO = str(FONTES / "Charm-Bold.ttf")


def relogio():
    S = 768
    im = Image.new("RGB", (S, S), (58, 36, 22))                         # pulseira de couro
    d = ImageDraw.Draw(im)
    for y in range(0, S, 48):
        d.line([(S * 0.2, y), (S * 0.2, y + 24)], fill=(190, 160, 110), width=5)
        d.line([(S * 0.8, y), (S * 0.8, y + 24)], fill=(190, 160, 110), width=5)
    c = S // 2
    d.ellipse([c - 330, c - 330, c + 330, c + 330], fill=(120, 88, 30))
    d.ellipse([c - 316, c - 316, c + 316, c + 316], fill=(212, 170, 70))
    d.ellipse([c - 282, c - 282, c + 282, c + 282], fill=(60, 44, 18))
    d.ellipse([c - 270, c - 270, c + 270, c + 270], fill=(242, 234, 212))
    f = ImageFont.truetype(BOLD, 62)
    for h in range(1, 13):
        a = math.radians(h * 30 - 90)
        x, y = c + math.cos(a) * 212, c + math.sin(a) * 212
        d.text((x, y), str(h), font=f, fill=(28, 24, 20), anchor="mm")
    for m in range(60):
        a = math.radians(m * 6 - 90)
        r0 = 252 if m % 5 else 244
        d.line([(c + math.cos(a) * r0, c + math.sin(a) * r0), (c + math.cos(a) * 266, c + math.sin(a) * 266)],
               fill=(28, 24, 20), width=3 if m % 5 else 7)
    for ang, comp, larg in (((4 + 40 / 60) * 30, 130, 22), (40 * 6, 200, 14)):
        a = math.radians(ang - 90)
        d.line([(c - math.cos(a) * 26, c - math.sin(a) * 26), (c + math.cos(a) * comp, c + math.sin(a) * comp)],
               fill=(20, 18, 16), width=larg)
    a = math.radians(11 * 6 - 90)                                        # ponteiro dos segundos, parado
    d.line([(c, c), (c + math.cos(a) * 220, c + math.sin(a) * 220)], fill=(190, 30, 30), width=5)
    d.ellipse([c - 18, c - 18, c + 18, c + 18], fill=(190, 30, 30))
    im.save(OUT / "relogio_440.png")


def janela():
    w, h = 640, 800
    r = random.Random(3)
    im = Image.new("RGB", (w, h), (16, 24, 46))
    d = ImageDraw.Draw(im)
    for y in range(h):
        k = y / h
        d.line([(0, y), (w, y)], fill=(int(14 + 22 * k), int(22 + 30 * k), int(44 + 44 * k)))
    for _ in range(26):                                                  # luzes distantes borradas
        x, y, s = r.randrange(w), r.randrange(int(h * 0.55), h), r.randrange(6, 16)
        d.ellipse([x, y, x + s, y + s], fill=r.choice([(255, 196, 110), (255, 230, 170), (190, 210, 255)]))
    im = im.filter(ImageFilter.GaussianBlur(7))
    d = ImageDraw.Draw(im)
    for _ in range(520):                                                 # riscos de chuva
        x, y, L = r.randrange(w), r.randrange(h), r.randrange(18, 60)
        c = r.randrange(120, 200)
        d.line([(x, y), (x - 4, y + L)], fill=(c, c + 10, min(255, c + 40)), width=2)
    d.rectangle([w // 2 - 9, 0, w // 2 + 9, h], fill=(36, 26, 20))
    for y in (h // 3, 2 * h // 3):
        d.rectangle([0, y - 8, w, y + 8], fill=(36, 26, 20))
    d.rectangle([0, 0, w - 1, h - 1], outline=(36, 26, 20), width=22)
    im.save(OUT / "janela_chuva.png")


def cameras():
    w, h = 640, 400
    fonte = ImageFont.truetype(BOLD, 74)
    peq = ImageFont.truetype(BOLD, 30)
    for k, nome in enumerate(("CORREDOR NORTE", "PORTA DO GABINETE", "ESCADARIA", "JARDIM")):
        base = Image.new("RGB", (w, h), (30, 44, 40))
        d = ImageDraw.Draw(base)
        d.polygon([(0, h), (w, h), (w * 0.62, h * 0.52), (w * 0.38, h * 0.52)], fill=(64, 84, 76))
        d.polygon([(0, 0), (w * 0.38, h * 0.2), (w * 0.38, h * 0.52), (0, h)], fill=(44, 62, 56))
        d.polygon([(w, 0), (w * 0.62, h * 0.2), (w * 0.62, h * 0.52), (w, h)], fill=(40, 56, 52))
        d.rectangle([w * 0.38, h * 0.2, w * 0.62, h * 0.52], fill=(22, 30, 30) if k != 1 else (70, 50, 34))
        if k == 1:
            d.ellipse([w * 0.565, h * 0.37, w * 0.585, h * 0.4], fill=(210, 180, 90))
        for y in range(0, h, 4):
            d.line([(0, y), (w, y)], fill=(0, 0, 0), width=1)
        ruido = Image.effect_noise((w, h), 26).convert("RGB")
        base = Image.blend(base, ruido, 0.12)
        for hora in ("0210", "0217"):
            im = base.copy()
            d = ImageDraw.Draw(im)
            d.text((16, 10), f"CAM {37 + k * 41:03d}  {nome}", font=peq, fill=(230, 240, 230))
            d.ellipse([w - 46, 18, w - 22, 42], fill=(230, 40, 40))
            d.rectangle([0, h - 104, 300, h], fill=(0, 0, 0))
            d.text((14, h - 100), f"{hora[:2]}:{hora[2:]}", font=fonte,
                   fill=(255, 255, 255) if hora == "0210" else (255, 70, 60))
            im.save(OUT / f"cam{k}_{hora}.png")
    Image.effect_noise((w, h), 90).convert("RGB").save(OUT / "cam_ruido.png")


def livro():
    """Pagina em pe (o video e vertical): hora + assinatura, a ultima linha em vermelho."""
    w, h = 1000, 1300
    im = Image.new("RGB", (w, h), (240, 232, 208))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], outline=(70, 46, 30), width=22)
    ft, fc = ImageFont.truetype(BOLD, 50), ImageFont.truetype(BOLD, 34)
    fm = ImageFont.truetype(MAO, 96)
    d.text((70, 48), "LIVRO DE ENTRADAS", font=ft, fill=(60, 44, 32))
    d.text((70, 108), "PALÁCIO DAS ÁGUAS", font=fc, fill=(120, 100, 80))
    d.text((70, 176), "HORA", font=fc, fill=(120, 100, 80))
    d.text((380, 176), "ASSINATURA", font=fc, fill=(120, 100, 80))
    linhas = [("19:05", "Cida Moura"), ("20:30", "Tenório Paz"), ("22:10", "Dra. Lívia"), ("23:45", "Cabo Nunes"),
              ("01:52", "Det. Ramos")]
    y = 230
    for k in range(7):
        d.line([(50, y + 140), (w - 50, y + 140)], fill=(150, 170, 200), width=3)
        if k < len(linhas):
            hora, nome = linhas[k]
            ult = k == len(linhas) - 1
            cor = (170, 20, 20) if ult else (30, 38, 92)
            d.text((70, y + 30), hora, font=ImageFont.truetype(BOLD, 88 if ult else 78), fill=cor)
            d.text((380, y + 4), nome, font=fm, fill=cor)
        y += 150
    im.save(OUT / "livro.png")


def marmore():
    S, n = 512, 4
    r = random.Random(2)
    im = Image.new("RGB", (S, S))
    d = ImageDraw.Draw(im)
    q = S // n
    for i in range(n):
        for j in range(n):
            claro = (i + j) % 2 == 0
            d.rectangle([i * q, j * q, (i + 1) * q, (j + 1) * q], fill=(206, 200, 188) if claro else (58, 60, 68))
            for _ in range(3):
                x, y = i * q + r.randrange(q), j * q + r.randrange(q)
                d.line([(x, y), (x + r.randrange(-50, 50), y + r.randrange(-50, 50))],
                       fill=(176, 170, 160) if claro else (84, 86, 96), width=2)
            d.rectangle([i * q, j * q, (i + 1) * q, (j + 1) * q], outline=(30, 30, 34), width=2)
    im.save(OUT / "marmore.png")


if __name__ == "__main__":
    relogio(); janela(); cameras(); livro(); marmore()
    folha = Image.new("RGB", (1500, 400), (30, 30, 30))
    x = 0
    for n in ("relogio_440.png", "janela_chuva.png", "cam1_0217.png", "livro.png", "marmore.png"):
        t = Image.open(OUT / n)
        t.thumbnail((300, 380))
        folha.paste(t, (x, 10)); x += 300
    folha.save(AQUI / "texturas_relojoeiro_teste.jpg", quality=85)
    print("ok")
