"""Texturas da serie Ultima Parada: paineis luminosos do onibus e tela do celular."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

AQUI = Path(__file__).resolve().parent
OUT = AQUI / "texturas"
OUT.mkdir(exist_ok=True)
F = str(AQUI.parent.parent / "resource" / "fonts" / "BeVietnamPro-Bold.ttf")
LARANJA = (255, 150, 20)


def painel(nome, linha1, linha2=""):
    W, H = 1200, 240
    im = Image.new("RGB", (W, H), (8, 8, 10))
    d = ImageDraw.Draw(im)
    if linha2:
        d.text((W / 2, 70), linha1, font=ImageFont.truetype(F, 78), fill=LARANJA, anchor="mm")
        d.text((W / 2, 170), linha2, font=ImageFont.truetype(F, 78), fill=LARANJA, anchor="mm")
    else:
        d.text((W / 2, H / 2), linha1, font=ImageFont.truetype(F, 130), fill=LARANJA, anchor="mm")
    for y in range(0, H, 6):   # efeito de pontinhos de LED
        d.line([(0, y), (W, y)], fill=(8, 8, 10), width=2)
    for x in range(0, W, 6):
        d.line([(x, 0), (x, H)], fill=(8, 8, 10), width=2)
    im.save(OUT / f"painel_{nome}.png")


def celular():
    W, H = 640, 1180
    im = Image.new("RGB", (W, H), (18, 22, 30))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 110], fill=(30, 36, 48))
    d.text((W / 2, 55), "LINHA 409", font=ImageFont.truetype(F, 54), fill=(255, 255, 255), anchor="mm")
    # mapa
    d.rectangle([30, 140, W - 30, 700], fill=(34, 42, 54))
    for k in range(6):
        d.line([(30, 190 + k * 90), (W - 30, 230 + k * 90)], fill=(48, 58, 74), width=10)
        d.line([(90 + k * 95, 140), (60 + k * 95, 700)], fill=(48, 58, 74), width=10)
    d.line([(120, 640), (220, 480), (360, 430), (520, 250)], fill=(90, 100, 115), width=12)
    d.ellipse([92, 612, 148, 668], fill=(60, 150, 255), outline=(255, 255, 255), width=6)
    d.rounded_rectangle([40, 730, W - 40, 900], radius=24, fill=(190, 30, 30))
    d.text((W / 2, 780), "LINHA DESATIVADA", font=ImageFont.truetype(F, 50), fill=(255, 255, 255), anchor="mm")
    d.text((W / 2, 850), "desde 2011", font=ImageFont.truetype(F, 46), fill=(255, 220, 220), anchor="mm")
    d.text((W / 2, 980), "Você está em:", font=ImageFont.truetype(F, 38), fill=(170, 180, 195), anchor="mm")
    d.text((W / 2, 1040), "Terminal Central", font=ImageFont.truetype(F, 50), fill=(255, 255, 255), anchor="mm")
    d.text((W / 2, 1110), "parado há 41 min", font=ImageFont.truetype(F, 40), fill=(255, 190, 60), anchor="mm")
    im.save(OUT / "celular_409.png")


painel("409", "409  TERMINAL")
painel("proxima", "PRÓXIMA PARADA")
painel("rua", "PRÓXIMA PARADA", "RUA DAS ACÁCIAS, 58")
celular()
print("ok")
