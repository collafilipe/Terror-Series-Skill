"""
Pinta skins novas (1024x1024) para os bonecos Kenney, com aparencia brasileira.
Layout do atlas (medido em texture-*.png):
  Cabeca  cruz em x 0..512, y 0..384 (celulas de 128): topo (128,0); faixa y128: esq(0) frente(128) dir(256) costas(384); baixo (128,256)
  Tronco  topo (96,688,128x96); faixa y784..928: esq(0,96) frente(96,128) dir(224,96) costas(320,128); baixo (96,928,128x96)
  Bracos  esq em x480, dir em x768: tampa (x+64,534,64x64); faixa y598..768 com 4 lados de 64
  Pernas  esq em x480, dir em x768: tampa (x+64,800,64x64); faixa y864..1024 com 4 lados de 64
Uso: python fazer_skins.py   (gera texture-br_*.png e uma folha de conferencia)
"""
from pathlib import Path

from PIL import Image, ImageDraw

PASTA = Path(__file__).resolve().parent / "kenney" / "blocky-characters" / "Models" / "GLB format" / "Textures"
FUNDO = (27, 28, 33)


def esc(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


def pintar(nome, pele, cabelo, camisa, calca, sapato=(40, 40, 46), cabelo_tipo="curto", rosto=True, bigode=None,
           barba=None, oculos=False, batom=None, manga="curta", calca_tipo="longa", detalhe=None, cor2=None):
    im = Image.new("RGB", (1024, 1024), FUNDO)
    d = ImageDraw.Draw(im)
    sombra = esc(pele, 0.86)
    # ---------------- cabeca
    d.rectangle([128, 0, 255, 127], fill=cabelo if cabelo_tipo != "careca" else pele)      # topo
    d.rectangle([128, 256, 255, 383], fill=pele)                                            # baixo
    for x0 in (0, 128, 256, 384):
        d.rectangle([x0, 128, x0 + 127, 255], fill=pele)
    longo = cabelo_tipo in ("longo", "cacheado")
    alt_lado = 255 if longo else (176 if cabelo_tipo != "careca" else 150)
    # costas
    d.rectangle([384, 128, 511, 255 if longo else 226], fill=cabelo)
    # lados: cabelo em cima e na metade de tras; orelha na pele
    d.rectangle([0, 128, 127, alt_lado], fill=cabelo)
    d.rectangle([0, 128, 58, 255 if longo else 226], fill=cabelo)
    d.rectangle([256, 128, 383, alt_lado], fill=cabelo)
    d.rectangle([325, 128, 383, 255 if longo else 226], fill=cabelo)
    if not longo:
        d.ellipse([72, 186, 96, 218], fill=sombra)
        d.ellipse([288, 186, 312, 218], fill=sombra)
    # frente: franja
    fx, fy = 128, 128
    if cabelo_tipo == "careca":
        d.rectangle([fx, fy, fx + 14, fy + 60], fill=cabelo)
        d.rectangle([fx + 113, fy, fx + 127, fy + 60], fill=cabelo)
    elif cabelo_tipo == "cacheado":
        d.rectangle([fx, fy, fx + 127, fy + 30], fill=cabelo)
        for k in range(6):
            d.ellipse([fx - 8 + k * 24, fy + 14, fx + 22 + k * 24, fy + 46], fill=cabelo)
        d.rectangle([fx, fy, fx + 14, fy + 127], fill=cabelo)
        d.rectangle([fx + 113, fy, fx + 127, fy + 127], fill=cabelo)
    elif cabelo_tipo == "longo":
        d.rectangle([fx, fy, fx + 127, fy + 28], fill=cabelo)
        d.polygon([(fx, fy + 28), (fx + 70, fy + 28), (fx, fy + 70)], fill=cabelo)
        d.rectangle([fx, fy, fx + 12, fy + 127], fill=cabelo)
        d.rectangle([fx + 115, fy, fx + 127, fy + 127], fill=cabelo)
    else:
        d.rectangle([fx, fy, fx + 127, fy + 26], fill=cabelo)
        d.polygon([(fx, fy + 26), (fx + 127, fy + 26), (fx + 127, fy + 34), (fx + 64, fy + 30), (fx, fy + 40)], fill=cabelo)
    if rosto:
        escuro = (52, 34, 28)
        for ex in (38, 90):
            d.rounded_rectangle([fx + ex - 7, fy + 62, fx + ex + 7, fy + 82], radius=5, fill=escuro)
            d.ellipse([fx + ex - 1, fy + 65, fx + ex + 4, fy + 70], fill=(255, 255, 255))
            d.rounded_rectangle([fx + ex - 12, fy + 49, fx + ex + 12, fy + 55], radius=3, fill=esc(cabelo, 0.8))
        d.ellipse([fx + 55, fy + 80, fx + 73, fy + 94], fill=sombra)
        for bx in (22, 106):
            d.ellipse([fx + bx - 10, fy + 88, fx + bx + 10, fy + 102], fill=esc(pele, 0.93) if pele[0] < 150 else (240, 170, 150))
        if barba:
            d.rounded_rectangle([fx + 14, fy + 92, fx + 114, fy + 128], radius=18, fill=barba)
        if bigode:
            d.rounded_rectangle([fx + 36, fy + 94, fx + 92, fy + 106], radius=6, fill=bigode)
        else:
            d.arc([fx + 46, fy + 92, fx + 82, fy + 112], 20, 160, fill=batom or esc(pele, 0.55), width=5)
        if oculos:
            for ex in (38, 90):
                d.rounded_rectangle([fx + ex - 17, fy + 56, fx + ex + 17, fy + 88], radius=8, outline=(30, 30, 34), width=5)
            d.line([fx + 55, fy + 70, fx + 73, fy + 70], fill=(30, 30, 34), width=5)
    else:
        # sem rosto: so pele lisa com uma sombra leve onde seriam os olhos
        d.ellipse([fx + 24, fy + 58, fx + 52, fy + 84], fill=esc(pele, 0.95))
        d.ellipse([fx + 76, fy + 58, fx + 104, fy + 84], fill=esc(pele, 0.95))
    # ---------------- tronco
    d.rectangle([96, 688, 223, 783], fill=camisa)
    d.rectangle([0, 784, 447, 927], fill=camisa)
    d.rectangle([96, 928, 223, 1023], fill=calca)
    d.rectangle([0, 906, 447, 927], fill=esc(calca, 0.8))               # cintura
    tx, ty = 96, 784
    c2 = cor2 or esc(camisa, 0.7)
    if detalhe == "gola_v":
        d.polygon([(tx + 40, ty), (tx + 88, ty), (tx + 64, ty + 34)], fill=pele)
        d.line([(tx + 40, ty), (tx + 64, ty + 34), (tx + 88, ty)], fill=c2, width=7)
    elif detalhe == "selecao":
        d.polygon([(tx + 40, ty), (tx + 88, ty), (tx + 64, ty + 30)], fill=pele)
        d.line([(tx + 40, ty), (tx + 64, ty + 30), (tx + 88, ty)], fill=c2, width=9)
        d.rectangle([0, 784, 447, 792], fill=c2)
        d.ellipse([tx + 80, ty + 44, tx + 104, ty + 68], fill=c2)                      # escudo
        d.rectangle([320 + 44, 820, 320 + 54, 880], fill=c2)                             # numero 10 nas costas
        d.rounded_rectangle([320 + 66, 820, 320 + 92, 880], radius=10, outline=c2, width=9)
    elif detalhe == "uniforme":
        d.polygon([(tx + 44, ty), (tx + 84, ty), (tx + 64, ty + 26)], fill=(245, 245, 245))
        d.polygon([(tx + 58, ty + 14), (tx + 70, ty + 14), (tx + 74, ty + 86), (tx + 64, ty + 98), (tx + 54, ty + 86)], fill=c2)
        d.rectangle([tx + 84, ty + 40, tx + 110, ty + 58], fill=esc(camisa, 0.85))    # bolso
        d.rectangle([tx + 86, ty + 30, tx + 108, ty + 38], fill=(240, 200, 60))        # cracha
    elif detalhe == "listras":
        for k in range(0, 118, 26):
            d.rectangle([0, 794 + k, 447, 804 + k], fill=c2)
        d.polygon([(tx + 46, ty), (tx + 82, ty), (tx + 64, ty + 22)], fill=pele)
    elif detalhe == "xadrez":
        for k in range(0, 448, 32):
            d.rectangle([k, 784, k + 10, 905], fill=c2)
        for k in range(0, 118, 30):
            d.rectangle([0, 790 + k, 447, 798 + k], fill=c2)
        d.line([(tx + 64, ty), (tx + 64, ty + 120)], fill=esc(camisa, 0.6), width=4)
    elif detalhe == "florido":
        import random
        r = random.Random(7)
        for _ in range(110):
            x, y = r.randrange(0, 440), r.randrange(788, 900)
            d.ellipse([x, y, x + 12, y + 12], fill=c2)
            d.ellipse([x + 4, y + 4, x + 8, y + 8], fill=(255, 235, 150))
        d.polygon([(tx + 44, ty), (tx + 84, ty), (tx + 64, ty + 24)], fill=pele)
    elif detalhe == "botoes":
        d.polygon([(tx + 46, ty), (tx + 82, ty), (tx + 64, ty + 24)], fill=pele)
        d.line([(tx + 64, ty + 24), (tx + 64, ty + 120)], fill=c2, width=4)
        for k in (40, 66, 92):
            d.ellipse([tx + 60, ty + k, tx + 68, ty + k + 8], fill=(240, 240, 240))
    # ---------------- bracos e pernas
    for bx in (480, 768):
        d.rectangle([bx + 64, 534, bx + 127, 597], fill=camisa)
        d.rectangle([bx, 598, bx + 255, 767], fill=pele)
        fim_manga = 598 + (150 if manga == "longa" else 66)
        d.rectangle([bx, 598, bx + 255, fim_manga], fill=camisa)
        d.rectangle([bx, fim_manga - 9, bx + 255, fim_manga], fill=c2 if detalhe in ("selecao", "listras") else esc(camisa, 0.85))
        d.rectangle([bx, 744, bx + 255, 767], fill=sombra)
        d.rectangle([bx + 64, 864, bx + 127, 864], fill=calca)
    for px in (480, 768):
        d.rectangle([px + 64, 800, px + 127, 863], fill=calca)
        d.rectangle([px, 864, px + 255, 1023], fill=pele if calca_tipo == "curta" else calca)
        if calca_tipo == "curta":
            d.rectangle([px, 864, px + 255, 930], fill=calca)
        d.rectangle([px, 988, px + 255, 1023], fill=sapato)
        d.rectangle([px, 1012, px + 255, 1023], fill=(235, 235, 235) if sapato[0] > 150 else esc(sapato, 0.6))
    im.save(PASTA / f"texture-br_{nome}.png")
    return im


# tons
P_CLARA, P_PARDA, P_MORENA, P_NEGRA = (240, 198, 160), (214, 160, 118), (176, 120, 82), (112, 72, 50)
PRETO, CASTANHO, GRISALHO, BRANCO = (30, 26, 28), (72, 46, 30), (150, 150, 156), (232, 232, 236)
JEANS, JEANS_ESC, CAQUI, PRETO_C = (58, 92, 150), (40, 58, 100), (160, 130, 90), (38, 38, 44)

ELENCO = {
    "voce": dict(pele=P_PARDA, cabelo=PRETO, camisa=(36, 60, 110), calca=JEANS, sapato=(235, 235, 235), detalhe="gola_v",
                 cor2=(230, 230, 235)),
    "senhora": dict(pele=P_MORENA, cabelo=GRISALHO, camisa=(120, 60, 130), calca=(120, 60, 130), cabelo_tipo="longo",
                    oculos=True, batom=(170, 50, 70), detalhe="florido", cor2=(235, 120, 160), sapato=(90, 60, 50)),
    "motorista": dict(pele=P_MORENA, cabelo=GRISALHO, camisa=(140, 180, 220), calca=(40, 48, 70), bigode=(120, 120, 126),
                      detalhe="uniforme", cor2=(30, 40, 70)),
    "homem": dict(pele=P_CLARA, cabelo=CASTANHO, camisa=(225, 225, 230), calca=PRETO_C, detalhe="listras",
                  cor2=(60, 110, 170), barba=(92, 60, 40)),
    "trocado": dict(pele=P_CLARA, cabelo=CASTANHO, camisa=(225, 225, 230), calca=PRETO_C, detalhe="listras",
                    cor2=(60, 110, 170), rosto=False),
    "torcedor": dict(pele=P_NEGRA, cabelo=PRETO, camisa=(250, 210, 30), calca=(30, 70, 160), calca_tipo="curta",
                     detalhe="selecao", cor2=(20, 130, 70), sapato=(235, 235, 235)),
    "moca": dict(pele=P_NEGRA, cabelo=PRETO, camisa=(235, 110, 70), calca=JEANS_ESC, cabelo_tipo="cacheado",
                 batom=(170, 40, 60), detalhe="gola_v", cor2=(250, 220, 200), sapato=(235, 235, 235)),
    "idoso": dict(pele=P_PARDA, cabelo=BRANCO, camisa=(190, 70, 60), calca=CAQUI, cabelo_tipo="careca", bigode=BRANCO,
                  oculos=True, detalhe="xadrez", cor2=(250, 235, 210), manga="longa", sapato=(90, 60, 40)),
    "porteiro": dict(pele=P_NEGRA, cabelo=PRETO, camisa=(235, 235, 240), calca=PRETO_C, detalhe="botoes",
                     cor2=(170, 170, 180), manga="longa"),
    "jovem_mulher": dict(pele=P_PARDA, cabelo=CASTANHO, camisa=(60, 160, 140), calca=JEANS, cabelo_tipo="longo",
                         batom=(190, 70, 90), detalhe="gola_v", cor2=(240, 240, 240), sapato=(235, 235, 235)),
}

if __name__ == "__main__":
    for nome, cfg in ELENCO.items():
        pintar(nome, **cfg)
    print("skins:", ", ".join(ELENCO))
