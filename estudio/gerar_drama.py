"""
Gera um capitulo de serie "dirigido a mao": plano em Python com cenas, falas por personagem, sons e codigo 3D.

Uso:
  .venv\\Scripts\\python.exe estudio\\gerar_drama.py estudio\\series\\portaria\\cap1_plano.py            (video final)
  .venv\\Scripts\\python.exe estudio\\gerar_drama.py estudio\\series\\portaria\\cap1_plano.py --previa   (3 quadros por cena)

Plano (arquivo .py com um dict PLANO):
  titulo, rotulo, pergunta, opcao_a, opcao_b, legenda_post
  cenas: [{hud, amb: [chuva, zumbido, grilos, tique, coracao, ronco], linhas: [(quem, texto) ...], codigo}]
  linhas: ("narrador"|personagem de drama.PERSONAGENS, "texto com *destaque*"), ("som", nome), ("pausa", segundos),
          ("fundo", nome) = som que toca por baixo, sem segurar a narracao
  sons_em: [("palavra", nome)] = som no instante em que o narrador diz a palavra
  amb (camadas continuas): chuva, chuva_forte, vento, trovoada, zumbido, bipes, tique, grilos, coracao, tensao, ronco, motor
  No codigo 3D: F = quadros da cena; T = quadro de cada evento ("som" pelo nome, falas como "l0", "l1"...).
"""

import argparse
import json
import re
import runpy
import shutil
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import historia_shorts as base  # noqa: E402
import drama as D  # noqa: E402
import gerar3d as G  # noqa: E402
import caderno as C  # noqa: E402

FPS, SR = 30, D.SR
CARD = 3.5  # segundos da tela de escolha
CARD_NARRADO = 2.2   # sobra depois que o narrador termina de ler as opcoes
VOL_AMBIENTE = 0.3   # camadas de fundo (chuva, zumbido, grilos, coracao...) bem abaixo das vozes
VOL_EFEITO = 0.55    # sons pontuais (interfone, elevador, radio, impacto)

SONS = {  # nome -> (funcao, tempo que o roteiro avanca)
    "radio": (lambda: D.chiado_radio(0.5), 0.7),
    "radio_fim": (lambda: D.chiado_radio(0.3, bip=False), 0.5),
    "elevador": (lambda: np_concat(D.plim_elevador(), D.porta_arrastando()), 1.9),
    "porta": (lambda: D.porta_arrastando(), 1.3),
    "interfone": (lambda: D.interfone(3), 3.2),
    "interfone_longo": (lambda: D.interfone(5), 5.0),
    "impacto": (lambda: D.impacto(), 0.3),
    "passos": (lambda: D.passos(4), 2.0),
    "estatica": (lambda: D.chiado_radio(0.35, bip=False), 0.2),
    "campainha": (lambda: D.campainha(), 1.1),
    "freio": (lambda: D.freio_ar(), 1.0),
    "silencio": (None, 0.6),
    "trovao": (lambda: D.trovao(), 0.6),
    "pagina": (lambda: D.pagina(), 0.5),
    "lapis": (lambda: D.lapis(1.2), 1.8),      # o caderno aparece e a pista e anotada
    "luz_cai": (lambda: D.luz_cai(), 0.9),
    "alarme": (lambda: D.alarme(2), 1.2),
    "portao": (lambda: D.portao(), 1.6),
    "portao_fundo": (lambda: D.portao(), 0.5),      # a narracao segue por cima
    "tique_para": (lambda: D.tique_para(4), 0.5),
    "passos_marmore": (lambda: D.passos_marmore(4), 1.6),
    "passos_fundo": (lambda: D.passos_marmore(5), 0.4),
    "passos_longos": (lambda: D.passos_marmore(12, 0.55), 0.0),
    "passos_agua": (lambda: D.passos_agua(16), 0.0),
    "passos_chegando": (lambda: D.passos_chegando(13.0), 0.0),
    "macaneta": (lambda: D.macaneta(), 0.9),
    "rangido": (lambda: D.rangido(), 0.6),
    "grilo_para": (None, 0.0),
}


def np_concat(a, b):
    import numpy as np
    return np.concatenate([a[: int(0.6 * SR)], b])


def montar_cena_audio(cena, i, pasta, ultima):
    """Devolve (audio numpy, duracao, marcas em quadros, legendas [(ini, fim, quem, [(a,b,palavra,destaque)])])."""
    import numpy as np
    m = D.Mix(90)
    t = 0.25
    marcas, legendas = {}, []
    for k, (quem, txt) in enumerate(cena["linhas"]):
        if quem == "pausa":
            t += float(txt)
        elif quem == "fundo":      # som que toca sem segurar a narracao
            fn, _ = SONS[txt]
            marcas[txt] = int(t * FPS) + 1
            if fn:
                m.add(fn(), t, VOL_EFEITO)
        elif quem == "som":
            fn, avanco = SONS[txt]
            marcas[txt] = int(t * FPS) + 1
            if fn:
                m.add(fn(), t, VOL_EFEITO)
            t += avanco
        else:
            destaque = {base.norm(x) for d in re.findall(r"\*([^*]+)\*", txt) for x in d.split()}
            limpo = txt.replace("*", "")
            audio, palavras = D.falar(quem, limpo, pasta / "vozes", f"c{i:02d}_l{k:02d}")
            marcas[f"l{k}"] = int(t * FPS) + 1
            m.add(audio, t, 1.0)
            legendas.append((t, t + len(audio) / SR, quem,
                             [(t + a, t + b, p, base.norm(p) in destaque and base.norm(p) != "") for a, b, p in palavras]))
            t += len(audio) / SR + (0.32 if quem.startswith("narrador") else 0.22)
    for palavra, nome in cena.get("sons_em", []):   # som no instante em que o narrador diz a palavra
        quando = [a for _, _, quem, pal in legendas for a, _, p, _ in pal if base.norm(p) == base.norm(palavra)]
        if quando and SONS[nome][0]:
            m.add(SONS[nome][0](), quando[0], VOL_EFEITO)
            marcas.setdefault(nome, int(quando[0] * FPS) + 1)
    opc = [a for _, _, quem, pal in legendas if quem.startswith("narrador")
           for a, _, p, _ in pal if base.norm(p).startswith("opc")]
    if ultima and len(opc) >= 2:
        # opcoes narradas: a tela de escolha entra quando o narrador diz "Opcao A" e a B quando ele chega nela
        com = [a for _, _, quem, pal in legendas for a, _, p, _ in pal if base.norm(p) == "comenta"]
        dur = t + 0.3 + CARD_NARRADO
        marcas["card"] = int((opc[0] - 0.25) * FPS)
        marcas["card_b"] = int((opc[1] - 0.15) * FPS)
        marcas["card_fim"] = int(((com[-1] if com else t) - 0.1) * FPS)
        m.add(D.impacto(), opc[0] - 0.25, VOL_EFEITO * 0.6)
    else:
        dur = t + 0.3 + (CARD if ultima else 0)
        if ultima:
            marcas["card"] = int((dur - CARD) * FPS)
            m.add(D.impacto(), dur - CARD, VOL_EFEITO)
    amb = cena.get("amb", [])
    fim_grilo = (marcas["grilo_para"] / FPS) if "grilo_para" in marcas else dur
    camadas = {"chuva": (D.chuva, 1.0, dur), "zumbido": (D.zumbido, 1.0, dur), "tique": (D.tique, 1.0, dur),
               "grilos": (D.grilos, 1.0, fim_grilo), "coracao": (D.coracao, 0.9, dur),
               "motor": (D.motor, 1.0, dur), "chuva_forte": (D.chuva_forte, 1.0, dur),
               "vento": (D.vento, 1.0, dur), "trovoada": (D.trovoada, 1.0, dur), "bipes": (D.bipes, 1.0, dur),
               "tensao": (D.tensao, 1.0, dur),
               "ronco": (lambda d: D.ronco_grave(d, cresce=True), 0.8, dur)}
    for nome in amb:
        fn, vol, d = camadas[nome]
        if d > 0.2:
            m.add(fn(d), 0, vol * VOL_AMBIENTE, fade=0.04 if nome != "ronco" else 0.0)
    marcas["fim_falas"] = int(t * FPS)
    return m.buf[: int(dur * SR)].astype(np.float32), dur, marcas, legendas


def escrever_ass(legendas_abs, destino, y=1480):
    cab = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Narrador,{base.FONT_NAME},92,&H00FFFFFF,&H000000FF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,7,3,5,60,60,0,1
Style: Fala,{base.FONT_NAME},78,&H0000D7FF,&H000000FF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,7,3,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    linhas = []
    for ini, fim, quem, palavras in legendas_abs:
        narr = quem.startswith("narrador")
        maxp = 3 if narr else 4
        grupos, cur = [], []
        for p in palavras:
            cur.append(p)
            if len(cur) >= maxp or sum(len(x[2]) for x in cur) >= (14 if narr else 20) or p[2][-1:] in ".?!":
                grupos.append(cur)
                cur = []
        if cur:
            grupos.append(cur)
        for gi, gr in enumerate(grupos):
            a = gr[0][0]
            b = grupos[gi + 1][0][0] if gi + 1 < len(grupos) else min(fim + 0.25, gr[-1][1] + 0.6)
            partes = []
            for _, _, p, dest in gr:
                txt = p.upper() if narr else p
                partes.append(r"{\c&H002B2BFF&}" + txt + r"{\c&H00FFFFFF&}" if (dest and narr) else txt)
            anim = rf"{{\pos(540,{y})\fscx75\fscy75\t(0,100,\fscx100\fscy100)}}"
            linhas.append(f"Dialogue: 0,{base.ass_time(a)},{base.ass_time(b)},{'Narrador' if narr else 'Fala'},,0,0,0,,{anim}{' '.join(partes)}")
    destino.write_text(cab + "\n".join(linhas) + "\n", encoding="utf-8")


def main():
    import numpy as np
    ap = argparse.ArgumentParser()
    ap.add_argument("plano")
    ap.add_argument("--previa", action="store_true", help="so 3 quadros por cena, em resolucao reduzida")
    ap.add_argument("--cenas", help="so estas cenas na previa, ex: 3,7")
    ap.add_argument("--amostras", type=int, default=3, help="quadros por cena na previa")
    ap.add_argument("--so-audio", action="store_true", help="refaz so o som e troca no final.mp4 existente")
    args = ap.parse_args()
    arq = Path(args.plano).resolve()
    plano = runpy.run_path(str(arq))["PLANO"]
    work = arq.parent / arq.stem.replace("_plano", "")
    work.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    base.log("1/4 gravando falas e montando o som de cada cena...")
    audios, duracoes, frames, marcas_c, legendas_abs, off = [], [], [], [], [], 0.0
    n = len(plano["cenas"])
    for i, c in enumerate(plano["cenas"]):
        a, dur, marcas, legs = montar_cena_audio(c, i, work, i == n - 1)
        nf = int(round(dur * FPS))
        a = np.concatenate([a, np.zeros(max(0, int(nf / FPS * SR) - len(a)), dtype=np.float32)])[: int(nf / FPS * SR)]
        for ini, fim, quem, pal in legs:
            legendas_abs.append((off + ini, off + fim, quem, [(off + x, off + y, p, d) for x, y, p, d in pal]))
        audios.append(a)
        frames.append(nf)
        marcas_c.append(marcas)
        off += nf / FPS
    total = off
    base.log(f"   duracao total: {total:.1f}s")

    if args.so_audio:
        mix = D.Mix(total + 1)
        pos = 0.0
        for a, nf in zip(audios, frames):
            mix.add(a, pos)
            pos += nf / FPS
        mix.salvar(work / "som.wav", total)
        antigo = base.probe_duration(work / "final.mp4")
        if abs(antigo - total) > 0.4:
            raise SystemExit(f"duracao mudou ({antigo:.1f}s -> {total:.1f}s): precisa renderizar de novo")
        base.run(["ffmpeg", "-y", "-v", "error", "-i", "final.mp4", "-i", "som.wav", "-map", "0:v", "-map", "1:a",
                  "-c:v", "copy", "-af", "loudnorm=I=-15:TP=-1.5", "-c:a", "aac", "-b:a", "192k", "-shortest",
                  "-movflags", "+faststart", "final_novo.mp4"], cwd=work)
        (work / "final.mp4").unlink()
        (work / "final_novo.mp4").rename(work / "final.mp4")
        print(f"VIDEO_FILE={work / 'final.mp4'}")
        return

    if args.previa:
        so = {int(x) for x in args.cenas.split(",")} if args.cenas else None
        folhas = []
        for i, c in enumerate(plano["cenas"]):
            if so and (i + 1) not in so:
                continue
            pasta = work / f"previa_{i:02d}"
            if pasta.exists():
                shutil.rmtree(pasta)
            erro = G.blender_cena(c["codigo"], frames[i], pasta, seed=i + 1,
                                  extra={"amostra": args.amostras, "percentual": 40, "marcas": marcas_c[i]})
            if erro:
                base.log(f"   cena {i + 1}: ERRO -> {erro.strip()[-400:]}")
                continue
            arqs = sorted(pasta.glob("f_*.png"))[:args.amostras]
            ov = C.overlay(plano, i, marcas_c[i], frames[i])
            imgs = []
            for f in arqs:
                im = Image.open(f).convert("RGB")
                if ov:
                    im = im.resize((1080, 1920))
                    im = (ov(im, int(f.stem.split("_")[1])) or im).resize((432, 768))
                imgs.append(im)
            folha = Image.new("RGB", (sum(im.width for im in imgs), imgs[0].height))
            x = 0
            for im in imgs:
                folha.paste(im, (x, 0))
                x += im.width
            folhas.append(folha)
            base.log(f"   cena {i + 1}: previa ok ({frames[i]} quadros)")
        if folhas:
            cols = 2 if args.amostras <= 3 else 1
            w, h = folhas[0].size
            lin = (len(folhas) + cols - 1) // cols
            tudo = Image.new("RGB", (w * cols, h * lin), (255, 255, 255))
            for k, f in enumerate(folhas):
                tudo.paste(f, ((k % cols) * w, (k // cols) * h))
            tudo.save(work / "previas.jpg", quality=85)
            print(f"PREVIAS={work / 'previas.jpg'}")
        return

    base.log("2/4 renderizando no Blender...")
    infos = []
    for i, c in enumerate(plano["cenas"]):
        t1 = time.time()
        pasta = work / f"cena_{i:02d}"
        if pasta.exists():
            shutil.rmtree(pasta)
        erro = G.blender_cena(c["codigo"], frames[i], pasta, seed=i + 1, extra={"marcas": marcas_c[i]})
        if erro:
            raise SystemExit(f"cena {i + 1} falhou: {erro[-800:]}")
        base.log(f"   cena {i + 1}/{n}: {frames[i]} quadros em {time.time() - t1:.0f}s")
        infos.append({"pasta": pasta, "frames": frames[i], "numero": "", "hud": c.get("hud", ""),
                      "overlay": C.overlay(plano, i, marcas_c[i], frames[i])})

    base.log("3/4 placar, tela de escolha e legendas...")
    serie = {"rotulo": plano["rotulo"], "pergunta": plano["pergunta"], "a": plano["opcao_a"], "b": plano["opcao_b"],
             "card_frames": frames[-1] - marcas_c[-1]["card"]}
    mc = marcas_c[-1]
    if "card_b" in mc:
        serie["atrasos"] = (0, 6, mc["card_b"] - mc["card"], mc["card_fim"] - mc["card"])
    G.compor(infos, sum(frames), work / "visual.mp4", plano["titulo"], serie)
    escrever_ass(legendas_abs, work / "legendas.ass")
    (work / "fonts").mkdir(exist_ok=True)
    shutil.copy(base.FONT_FILE, work / "fonts" / base.FONT_FILE.name)
    mix = D.Mix(total + 1)
    pos = 0.0
    for a, nf in zip(audios, frames):
        mix.add(a, pos)
        pos += nf / FPS
    mix.salvar(work / "som.wav", total)

    base.log("4/4 juntando tudo...")
    base.run(["ffmpeg", "-y", "-v", "error", "-i", "visual.mp4", "-i", "som.wav", "-filter_complex",
              "[0:v]subtitles=legendas.ass:fontsdir=fonts[v];[1:a]loudnorm=I=-15:TP=-1.5[a]", "-map", "[v]", "-map", "[a]",
              "-t", f"{total:.2f}", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
              "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "final.mp4"], cwd=work)
    (work / "publicar.txt").write_text(f"TITULO:\n{plano['titulo']}\n\nLEGENDA DO POST (copie e cole):\n"
                                       f"{plano['legenda_post']}\n", encoding="utf-8")
    for p in work.glob("cena_*/f_*.png"):
        p.unlink()
    (work / "visual.mp4").unlink(missing_ok=True)
    base.log(f"PRONTO em {(time.time() - t0) / 60:.1f} min: {work / 'final.mp4'}")
    print(f"VIDEO_FILE={work / 'final.mp4'}")


if __name__ == "__main__":
    main()
