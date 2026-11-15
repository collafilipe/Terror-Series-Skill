"""
Caderno do detetive: as pistas aparecem escritas a mao na tela, numeradas, para qualquer pessoa acompanhar.

No plano, cada cena pode ter:
  "nota": "Sala trancada por dentro"   -> o caderninho desce do alto quando toca ("som", "lapis") e a pista e escrita;
                                          as pistas das cenas anteriores continuam nele.
  "caderno_cheio": True                -> cena de recapitulacao: caderno grande, uma pista a cada fala do narrador
                                          (a 1a fala abre o caderno; a 2a mostra a pista 1, e assim por diante).
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONTES = Path(__file__).resolve().parent.parent / "resource" / "fonts"
MAO = str(FONTES / "Charm-Bold.ttf")
TITULO = str(FONTES / "BeVietnamPro-Bold.ttf")
PAPEL, LINHA, MARGEM = (246, 238, 214), (176, 196, 222), (214, 96, 96)
TINTA, NOVA, CINZA = (30, 38, 92), (196, 28, 28), (120, 110, 96)
W = 1080


def _quebrar(d, texto, fonte, largura):
    linhas, atual = [], ""
    for p in texto.split():
        t = (atual + " " + p).strip()
        if d.textlength(t, font=fonte) > largura and atual:
            linhas.append(atual)
            atual = p
        else:
            atual = t
    return linhas + ([atual] if atual else [])


def _folha(notas, visiveis, letras_ultima, grande):
    """Desenha o caderno com as `visiveis` primeiras notas; a ultima visivel aparece em vermelho, com
    `letras_ultima` letras ja escritas (None = inteira)."""
    larg = 940 if grande else 900
    tam = 58 if grande else 46
    passo = 76 if grande else 60
    fm, ft = ImageFont.truetype(MAO, tam), ImageFont.truetype(TITULO, 30 if grande else 24)
    d0 = ImageDraw.Draw(Image.new("RGB", (4, 4)))
    x_txt = 96
    blocos = []
    for k, n in enumerate(notas):
        blocos.append(_quebrar(d0, f"{k + 1}. {n}", fm, larg - x_txt - 36))
    n_linhas = sum(len(b) for b in (blocos if grande else blocos[:visiveis]))
    topo = 104 if grande else 82
    alt = topo + n_linhas * passo + (44 if grande else 30)
    im = Image.new("RGBA", (larg + 24, alt + 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([14, 16, larg + 14, alt + 16], radius=20, fill=(0, 0, 0, 120))          # sombra
    d.rounded_rectangle([0, 0, larg, alt], radius=20, fill=PAPEL, outline=(60, 50, 40), width=4)
    for x in range(46, larg - 30, 62):                                                          # espiral
        d.ellipse([x, 12, x + 20, 32], fill=(40, 36, 34))
        d.rounded_rectangle([x + 6, -6, x + 14, 24], radius=4, fill=(150, 150, 156))
    d.text((x_txt, 40 if grande else 36), "CADERNO DO DETETIVE", font=ft, fill=CINZA)
    y = topo
    for _ in range(n_linhas):
        d.line([(24, y + passo - 8), (larg - 24, y + passo - 8)], fill=LINHA, width=2)
        y += passo
    d.line([(74, 50), (74, alt - 16)], fill=MARGEM, width=3)
    y = topo
    for k, bloco in enumerate(blocos[:visiveis]):
        ultima = k == visiveis - 1
        resto = None if not ultima or letras_ultima is None else letras_ultima
        for ln in bloco:
            txt = ln
            if resto is not None:
                txt = ln[:resto]
                resto = max(0, resto - len(ln))
            cor = NOVA if ultima else TINTA
            d.text((x_txt, y - 6), txt, font=fm, fill=cor)
            if ultima and txt == ln and (resto is None or resto > 0 or ln is bloco[-1]) and letras_ultima is None:
                wl = d.textlength(ln, font=fm)
                d.line([(x_txt, y + passo - 12), (x_txt + wl, y + passo - 12)], fill=NOVA, width=4)
            y += passo
        if grande and not ultima:
            pass
    if grande:
        # no caderno grande as linhas ainda nao reveladas ficam em branco (o espaco ja existe)
        pass
    return im.rotate(-1.2 if not grande else 1.0, resample=Image.BICUBIC, expand=True)


def overlay(plano, i, marcas, frames):
    """Devolve funcao (frame, f) -> frame para a cena i, ou None se ela nao mostra o caderno."""
    cenas = plano["cenas"]
    c = cenas[i]
    anteriores = [x["nota"] for x in cenas[:i] if x.get("nota")]
    cache = {}

    def folha(notas, vis, letras, grande):
        ch = (vis, letras, grande)
        if ch not in cache:
            cache[ch] = _folha(notas, vis, letras, grande)
        return cache[ch]

    def colar(frame, img, y, k):
        k = max(0.0, min(1.0, k))
        k = 1 - (1 - k) ** 3
        yy = int(-img.height + (y + img.height) * k)
        frame.paste(img, ((W - img.width) // 2, yy), img)
        return frame

    if c.get("nota"):
        notas = anteriores + [c["nota"]]
        f0 = marcas.get("lapis", max(1, marcas.get("fim_falas", frames) - 40))
        total = len(f"{len(notas)}. {c['nota']}")

        def fn(frame, f):
            if f < f0:
                return frame
            k = f - f0
            letras = int(total * min(1.0, max(0, k - 6) / 24))
            img = folha(notas, len(notas), None if letras >= total else letras, False)
            return colar(frame, img, 262, k / 9)
        return fn

    if c.get("caderno_cheio"):
        notas = anteriores
        falas = sorted(v for ch, v in marcas.items() if ch[:1] == "l" and ch[1:].isdigit())
        ini = falas[0] if falas else 1
        tempos = (falas[1:] + [frames] * len(notas))[:len(notas)]

        def fn(frame, f):
            if f < ini:
                return frame
            escuro = Image.new("RGB", frame.size, (0, 0, 0))
            frame = Image.blend(frame, escuro, min(0.5, (f - ini) / 24))
            vis = sum(1 for t in tempos if f >= t)
            letras = None
            if vis:
                total = len(f"{vis}. {notas[vis - 1]}")
                n = int(total * min(1.0, (f - tempos[vis - 1]) / 22))
                letras = None if n >= total else n
            img = folha(notas, vis, letras, True)
            return colar(frame, img, 330, (f - ini) / 10)
        return fn
    return None


if __name__ == "__main__":   # teste visual: python caderno.py
    plano = {"cenas": [{"nota": "Sala trancada por dentro"}, {"nota": "As câmeras perderam 7 minutos"},
                       {"nota": "O relógio avisa: alguém morre às 4h40"}, {"nota": "O assassino está dentro do palácio"},
                       {"nota": "A médica sumiu"}, {"nota": "Alguém assinou o MEU nome às 1h52"}, {"caderno_cheio": True}]}
    folha = Image.new("RGB", (W * 3, 1920), (40, 44, 60))
    for k, (i, m, f) in enumerate(((2, {"lapis": 10}, 30), (5, {"lapis": 10}, 90),
                                   (6, {"l0": 1, "l1": 20, "l2": 40, "l3": 60, "l4": 80, "l5": 100, "l6": 120}, 150))):
        fr = overlay(plano, i, m, 200)(Image.new("RGB", (W, 1920), (40, 44, 60)), f)
        folha.paste(fr, (k * W, 0))
    folha.resize((W * 3 // 3, 640)).save(Path(__file__).resolve().parent / "caderno_teste.jpg", quality=88)
    print("ok")
