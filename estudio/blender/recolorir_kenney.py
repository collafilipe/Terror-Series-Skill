"""Cria texturas novas dos personagens Kenney (ex: preso de laranja) trocando a cor da roupa."""
import colorsys
import sys
from pathlib import Path

from PIL import Image

PASTA = Path(__file__).resolve().parent / "kenney" / "blocky-characters" / "Models" / "GLB format" / "Textures"


def recolorir(origem, destino, faixas_hue, nova_hue, sat_min=0.25, nova_sat=None):
    im = Image.open(PASTA / origem).convert("RGBA")
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            hd = h * 360
            if s >= sat_min and any(lo <= hd <= hi for lo, hi in faixas_hue):
                ns = nova_sat if nova_sat is not None else max(s, 0.75)
                nv = min(1.0, v * 1.08 + 0.05)
                r2, g2, b2 = colorsys.hsv_to_rgb(nova_hue / 360, ns, nv)
                px[x, y] = (int(r2 * 255), int(g2 * 255), int(b2 * 255), a)
    im.save(PASTA / destino)
    print("ok", destino)


def sem_rosto(origem, destino, cor=(222, 224, 228)):
    """Lava a textura inteira para um cinza-claro quase uniforme (multidao sem rosto, tipo manequim)."""
    im = Image.open(PASTA / origem).convert("RGBA")
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            lum = (0.3 * r + 0.59 * g + 0.11 * b) / 255
            k = 0.9 + 0.12 * (lum - 0.5)  # quase sem contraste: some o rosto e a roupa
            px[x, y] = (int(cor[0] * k), int(cor[1] * k), int(cor[2] * k), a)
    im.save(PASTA / destino)
    print("ok", destino)


if __name__ == "__main__":
    sem_rosto("texture-c.png", "texture-semrosto.png")
    # preso: macacao vermelho + calca azul do personagem B viram laranja
    recolorir("texture-b.png", "texture-preso.png", [(0, 14), (335, 360), (195, 255)], 24)
    # guarda de presidio: policial J com farda cinza-escuro em vez de azul
    recolorir("texture-j.png", "texture-guarda.png", [(195, 250)], 210, nova_sat=0.12)
    sys.exit(0)
