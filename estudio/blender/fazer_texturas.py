"""Gera as texturas da serie Portaria da Noite (roda com o Python do .venv, usa PIL)."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

AQUI = Path(__file__).resolve().parent
OUT = AQUI / "texturas"
OUT.mkdir(exist_ok=True)
FONTES = AQUI.parent.parent / "resource" / "fonts"
MANUSCRITA = str(FONTES / "Charm-Bold.ttf")
NORMAL = str(FONTES / "BeVietnamPro-Bold.ttf")


def piso():
    n, t = 12, 64
    im = Image.new("RGB", (n * t, n * t))
    d = ImageDraw.Draw(im)
    for i in range(n):
        for j in range(n):
            d.rectangle([i * t, j * t, (i + 1) * t, (j + 1) * t], fill=(214, 208, 196) if (i + j) % 2 else (58, 56, 62))
    im.save(OUT / "piso.png")


def folha():
    W, H = 1000, 1400
    im = Image.new("RGB", (W, H), (236, 222, 178))
    d = ImageDraw.Draw(im)
    for y in range(0, H, 7):  # textura de papel
        d.line([(0, y), (W, y)], fill=(230, 215, 170))
    d.text((W / 2, 110), "TURNO DA NOITE", font=ImageFont.truetype(NORMAL, 78), fill=(60, 30, 20), anchor="mm")
    d.text((W / 2, 200), "regras", font=ImageFont.truetype(MANUSCRITA, 80), fill=(60, 30, 20), anchor="mm")
    f = ImageFont.truetype(MANUSCRITA, 66)
    regras = [("1.", ["Depois da meia-noite,", "ninguém sobe pelo", "elevador de serviço."]),
              ("2.", ["Se o interfone do 704", "tocar, NÃO ATENDA."]),
              ("3.", ["O prédio tem 12 andares.", "Se o elevador mostrar 13,", "saia do hall."])]
    y = 320
    for num, linhas in regras:
        d.text((70, y), num, font=f, fill=(150, 20, 20))
        for ln in linhas:
            d.text((160, y), ln, font=f, fill=(35, 30, 60))
            if "704" in ln or "ATENDA" in ln:
                w = d.textlength(ln, font=f)
                for dy in (84, 94):
                    d.line([(160, y + dy), (160 + w, y + dy)], fill=(170, 20, 20), width=5)
            y += 98
        y += 60
    d.ellipse([720, 1180, 900, 1330], outline=(120, 90, 60), width=6)  # marca de cafe
    im.save(OUT / "folha.png")


def cftv(nome, porta_aberta=False, crianca=False):
    W, H = 800, 560
    im = Image.new("RGB", (W, H), (38, 40, 40))
    d = ImageDraw.Draw(im)
    fx0, fy0, fx1, fy1 = 320, 190, 480, 380  # parede do fundo do corredor
    d.polygon([(0, 0), (W, 0), (fx1, fy0), (fx0, fy0)], fill=(70, 72, 72))          # teto
    d.polygon([(0, H), (W, H), (fx1, fy1), (fx0, fy1)], fill=(92, 94, 92))          # chao
    d.polygon([(0, 0), (fx0, fy0), (fx0, fy1), (0, H)], fill=(120, 122, 120))       # parede esq
    d.polygon([(W, 0), (fx1, fy0), (fx1, fy1), (W, H)], fill=(108, 110, 108))       # parede dir
    d.rectangle([fx0, fy0, fx1, fy1], fill=(56, 58, 58))
    # portas nas paredes (em perspectiva)
    for k, (xa, xb) in enumerate(((40, 130), (190, 250), (290, 315))):
        ya0, ya1 = 60 + xa * 0.4, H - 20 - xa * 0.52
        yb0, yb1 = 60 + xb * 0.4, H - 20 - xb * 0.52
        cor = (20, 20, 20) if (porta_aberta and k == 1) else (150, 150, 146)
        d.polygon([(xa, ya0), (xb, yb0), (xb, yb1), (xa, ya1)], fill=cor, outline=(40, 40, 40))
        d.polygon([(W - xa, ya0), (W - xb, yb0), (W - xb, yb1), (W - xa, ya1)], fill=(140, 140, 136), outline=(40, 40, 40))
    if crianca:  # silhueta pequena, de costas, no fim do corredor
        cx, base = 400, 378
        d.rectangle([cx - 16, base - 62, cx + 16, base], fill=(12, 12, 12))
        d.ellipse([cx - 15, base - 92, cx + 15, base - 60], fill=(12, 12, 12))
    im = im.filter(ImageFilter.GaussianBlur(1.2))
    d = ImageDraw.Draw(im)
    for y in range(0, H, 4):
        d.line([(0, y), (W, y)], fill=(0, 0, 0), width=1)
    f = ImageFont.truetype(NORMAL, 30)
    d.text((24, 18), "CAM 07 · 7º ANDAR", font=f, fill=(235, 235, 235))
    d.text((W - 24, H - 22), "03:07:41", font=f, fill=(235, 235, 235), anchor="rs")
    d.ellipse([W - 60, 22, W - 36, 46], fill=(220, 30, 30))
    im.save(OUT / f"cftv_{nome}.png")


piso()
folha()
cftv("vazio")
cftv("porta", porta_aberta=True)
cftv("crianca", porta_aberta=True, crianca=True)
print("ok", sorted(p.name for p in OUT.glob("*.png")))
