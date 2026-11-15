"""
Gerador de Shorts de historia/curiosidades.

Uso:
    .venv\\Scripts\\python.exe estudio\\historia_shorts.py "Por que o Brasil fala portugues?"

Etapas: roteiro em cenas (Claude Code) -> uma imagem por cena (Wikimedia/Pixabay)
-> narracao por cena (Edge TTS) -> zoom lento em cada imagem -> legenda em
caixa alta com palavra-chave amarela -> musica de fundo -> MP4 vertical.
"""

import argparse
import asyncio
import json
import random
import re
import shutil
import subprocess
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import config  # noqa: E402
from app.services import llm  # noqa: E402
import edge_tts  # noqa: E402
from PIL import Image, ImageEnhance, ImageFilter, ImageOps  # noqa: E402

W, H, FPS = 1080, 1920, 30
UA = "HistoriaShorts/0.1 (ferramenta pessoal de video)"
VOICE = "pt-BR-AntonioNeural"
PITCH = "+0Hz"
COR_DESTAQUE = "&H0000D7FF&"  # cor da palavra-chave na legenda (ASS, ordem BGR): amarelo
# tratamento da narracao: graves mais cheios, presenca, compressao e volume padrao do YouTube (-14 LUFS)
MASTER_VOZ = ("highpass=f=70,equalizer=f=140:t=q:w=1:g=3,equalizer=f=3200:t=q:w=1.2:g=2,"
              "acompressor=threshold=-20dB:ratio=3:attack=5:release=120:makeup=3,loudnorm=I=-14:TP=-1.5:LRA=7")
VOZES = {"antonio": "pt-BR-AntonioNeural", "thalita": "pt-BR-ThalitaMultilingualNeural",
         "andrew": "en-US-AndrewMultilingualNeural", "brian": "en-US-BrianMultilingualNeural",
         "francisca": "pt-BR-FranciscaNeural"}
FONT_FILE = ROOT / "resource" / "fonts" / "BeVietnamPro-Bold.ttf"
FONT_NAME = "Be Vietnam Pro"
SONGS_DIR = ROOT / "resource" / "songs"
OUT_DIR = ROOT / "estudio" / "videos"

PLAN_PROMPT = """Voce e roteirista de um canal brasileiro de Shorts de historia e curiosidades.
Tema do video: {tema}

Escreva um roteiro narrado em portugues do Brasil dividido em {n} cenas. Regras:
- A cena 1 e um gancho forte: uma pergunta ou afirmacao surpreendente que prenda nos 2 primeiros segundos.
- Frases curtas, ritmo rapido, tom de quem conta um segredo. Nada de "ola", "neste video" ou "voce sabia".
- Use apenas fatos corretos e verificaveis, com datas, nomes e numeros reais.
- A ultima cena termina com uma frase de impacto ou uma pergunta que gere comentarios.
- Total entre 120 e 160 palavras. Cada cena tem 1 ou 2 frases curtas (8 a 22 palavras).
- Em cada cena, marque UMA palavra-chave (ou numero) entre asteriscos, por exemplo: *1494*.
- Para cada cena escolha UMA imagem que mostre exatamente o que a frase diz e escreva uma busca curta em ingles para encontra-la:
  - "fonte": "wikimedia" para pessoas, lugares, eventos, pinturas, mapas antigos ou objetos historicos reais e especificos. A busca deve usar nomes proprios (ex: "Treaty of Tordesillas map", "Pedro Alvares Cabral painting").
  - "fonte": "pixabay" para conceitos genericos (ex: "old sailing ship ocean", "gold coins", "tropical forest river").
- Na busca, nomeie a coisa em si (pessoa, obra, mapa, lugar). Evite palavras vagas como "document", "concept", "illustration", "history".
- Nao repita a mesma busca em duas cenas.
Responda SOMENTE com JSON valido, sem markdown, neste formato:
{{"titulo": "titulo chamativo do video", "descricao": "descricao curta para o YouTube com 3 hashtags", "cenas": [{{"texto": "frase da cena com *destaque*", "busca": "english search", "fonte": "wikimedia"}}]}}
"""


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()[:50] or "video"


def norm(word):
    word = unicodedata.normalize("NFKD", word).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", word.lower())


def run(cmd, cwd=None):
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise RuntimeError(f"comando falhou: {' '.join(map(str, cmd[:4]))}...\n{proc.stderr[-1500:]}")
    return proc.stdout


def probe_duration(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)])
    return float(out.strip())


# ---------------------------------------------------------------- roteiro
def plan_script(tema, n_cenas):
    prompt = PLAN_PROMPT.format(tema=tema, n=n_cenas)
    for tentativa in range(3):
        raw = llm._generate_response(prompt)
        raw = llm._strip_code_fence(raw or "").strip()
        match = re.search(r"\{.*\}", raw, re.S)
        try:
            plan = json.loads(match.group(0) if match else raw)
            cenas = [c for c in plan["cenas"] if c.get("texto", "").strip()]
            if len(cenas) >= 4:
                plan["cenas"] = cenas
                return plan
        except Exception as exc:  # noqa: BLE001
            log(f"roteiro invalido (tentativa {tentativa + 1}): {exc}")
    raise RuntimeError("o Claude Code nao devolveu um roteiro valido")


# ---------------------------------------------------------------- imagens
def http_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "wb") as f:
        shutil.copyfileobj(resp, f)
    Image.open(dest).verify()
    return dest


def search_wikimedia(query, used):
    params = {
        "action": "query", "format": "json", "generator": "search", "gsrnamespace": "6",
        "gsrsearch": f"{query} filetype:bitmap", "gsrlimit": "10",
        "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata", "iiurlwidth": "1600",
    }
    data = http_json("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params))
    pages = sorted(data.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
    for page in pages:
        info = (page.get("imageinfo") or [{}])[0]
        if info.get("mime") not in ("image/jpeg", "image/png") or info.get("width", 0) < 700:
            continue
        url = info.get("thumburl") or info.get("url")
        if url in used:
            continue
        meta = info.get("extmetadata", {})
        licenca = meta.get("LicenseShortName", {}).get("value", "?")
        autor = re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", "?")).strip()
        return url, f"Wikimedia Commons - {page.get('title')} - {autor} - {licenca} - {info.get('descriptionurl')}"
    return None


def search_pixabay(query, used):
    keys = config.app.get("pixabay_api_keys") or []
    if not keys:
        return None
    params = {"key": keys[0], "q": query[:100], "image_type": "all", "safesearch": "true", "per_page": "10"}
    data = http_json("https://pixabay.com/api/?" + urllib.parse.urlencode(params))
    for hit in data.get("hits", []):
        url = hit.get("largeImageURL")
        if url and url not in used:
            return url, f"Pixabay - {hit.get('user')} - {hit.get('pageURL')}"
    return None


def find_image(cena, idx, work, used):
    query = cena.get("busca", "").strip() or cena["texto"]
    fontes = [search_wikimedia, search_pixabay]
    if cena.get("fonte") == "pixabay":
        fontes.reverse()
    palavras = query.split()
    consultas = [query] + ([" ".join(palavras[:2])] if len(palavras) > 2 else [])
    for consulta in consultas:
        for fonte in fontes:
            try:
                achado = fonte(consulta, used)
                if not achado:
                    continue
                url, credito = achado
                ext = ".png" if url.lower().endswith(".png") else ".jpg"
                dest = download(url, work / f"img_{idx:02d}{ext}")
                used.add(url)
                return dest, credito
            except Exception as exc:  # noqa: BLE001
                log(f"  falha buscando '{consulta}' em {fonte.__name__}: {exc}")
    return None, None


def compose_frame(img_path, dest):
    """Imagem vertical 1080x1920: fundo desfocado + imagem inteira na parte de cima."""
    im = ImageOps.exif_transpose(Image.open(img_path)).convert("RGB")
    bg = ImageOps.fit(im, (W, H)).filter(ImageFilter.GaussianBlur(45))
    bg = ImageEnhance.Brightness(bg).enhance(0.4)
    ratio = im.width / im.height
    if ratio <= 0.8:
        fg = ImageOps.fit(im, (W, H))
        bg.paste(fg, (0, 0))
    else:
        fw = W
        fh = int(fw / ratio)
        if fh > 1250:
            fh = 1250
            fw = int(fh * ratio)
        fg = im.resize((fw, fh), Image.LANCZOS)
        y = max(180, 820 - fh // 2)
        bg.paste(fg, ((W - fw) // 2, y))
    bg.save(dest, quality=95)
    return dest


def fallback_frame(dest, idx):
    cores = [(25, 20, 35), (20, 30, 40), (40, 25, 20)]
    Image.new("RGB", (W, H), cores[idx % len(cores)]).save(dest)
    return dest


def scene_clip(frame, duration, idx, dest):
    frames = max(int(round(duration * FPS)), 1)
    if idx % 2 == 0:
        z = f"1+0.12*on/{frames}"
    else:
        z = f"1.12-0.12*on/{frames}"
    vf = (
        f"scale={W * 2}:{H * 2},zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        f":d={frames}:s={W}x{H}:fps={FPS},format=yuv420p"
    )
    run(["ffmpeg", "-y", "-v", "error", "-i", str(frame), "-vf", vf, "-frames:v", str(frames),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(dest)])
    return dest


# ---------------------------------------------------------------- narracao
async def _tts(text, out, rate):
    comm = edge_tts.Communicate(text, VOICE, rate=rate, pitch=PITCH, boundary="WordBoundary")
    words = []
    with open(out, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 1e7
                words.append((start, start + chunk["duration"] / 1e7, chunk["text"]))
    return words


def tts(text, out, rate):
    for tentativa in range(5):
        try:
            words = asyncio.run(_tts(text, out, rate))
            if words and out.stat().st_size > 1000:
                return words
        except Exception as exc:  # noqa: BLE001
            log(f"  voz falhou (tentativa {tentativa + 1}): {exc}")
        time.sleep(2)
    raise RuntimeError(f"nao foi possivel gerar a narracao de: {text[:60]}")


# ---------------------------------------------------------------- legendas
def ass_time(t):
    t = max(t, 0)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def build_ass(all_words, dest, y_pos=1360):
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{FONT_NAME},96,&H00FFFFFF,&H000000FF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,7,3,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    chunks, cur = [], []
    for i, w in enumerate(all_words):
        cur.append(w)
        nxt = all_words[i + 1] if i + 1 < len(all_words) else None
        quebra = (
            len(cur) >= 3
            or nxt is None
            or nxt["cena"] != w["cena"]
            or nxt["start"] - w["end"] > 0.3
            or sum(len(x["text"]) for x in cur) >= 14
        )
        if quebra:
            chunks.append(cur)
            cur = []
    lines = []
    for i, ch in enumerate(chunks):
        start = ch[0]["start"]
        end = chunks[i + 1][0]["start"] if i + 1 < len(chunks) else ch[-1]["end"] + 0.4
        end = min(end, ch[-1]["end"] + 0.6)
        parts = []
        for w in ch:
            txt = w["text"].upper()
            parts.append("{\\c" + COR_DESTAQUE + "}" + txt + r"{\c&H00FFFFFF&}" if w["destaque"] else txt)
        anim = rf"{{\pos({W // 2},{y_pos})\fscx70\fscy70\t(0,110,\fscx100\fscy100)}}"
        lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Default,,0,0,0,,{anim}{' '.join(parts)}")
    dest.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- principal
def main():
    ap = argparse.ArgumentParser(description="Gera um Short de historia/curiosidade.")
    ap.add_argument("tema", help="tema do video")
    ap.add_argument("--cenas", type=int, default=10, help="numero de cenas (padrao 10)")
    ap.add_argument("--velocidade", default="+10%", help="velocidade da voz, ex: +10%%")
    ap.add_argument("--musica", type=float, default=0.08, help="volume da musica 0-1 (0 desliga)")
    ap.add_argument("--roteiro", help="arquivo JSON de roteiro ja pronto (pula o Claude Code)")
    args = ap.parse_args()

    if args.roteiro:
        plan = json.loads(Path(args.roteiro).read_text(encoding="utf-8"))
    else:
        log("1/6 Claude Code escrevendo o roteiro em cenas...")
        plan = plan_script(args.tema, args.cenas)
    work = OUT_DIR / f"{time.strftime('%Y%m%d-%H%M%S')}-{slugify(plan.get('titulo') or args.tema)}"
    work.mkdir(parents=True, exist_ok=True)
    (work / "roteiro.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"   titulo: {plan.get('titulo')}  ({len(plan['cenas'])} cenas)")

    log("2/6 buscando uma imagem para cada cena...")
    used, creditos, frames = set(), [], []
    for i, cena in enumerate(plan["cenas"]):
        img, credito = find_image(cena, i, work, used)
        frame = work / f"frame_{i:02d}.jpg"
        if img:
            compose_frame(img, frame)
            creditos.append(f"Cena {i + 1}: {credito}")
            log(f"   cena {i + 1}: '{cena.get('busca')}' ok")
        else:
            fallback_frame(frame, i)
            creditos.append(f"Cena {i + 1}: sem imagem (fundo liso) - busca '{cena.get('busca')}'")
            log(f"   cena {i + 1}: nenhuma imagem para '{cena.get('busca')}'")
        frames.append(frame)

    log("3/6 gravando a narracao cena por cena...")
    all_words, audio_files, durations, offset = [], [], [], 0.0
    for i, cena in enumerate(plan["cenas"]):
        destaque = {norm(x) for d in re.findall(r"\*([^*]+)\*", cena["texto"]) for x in d.split()}
        fala = cena["texto"].replace("*", "")
        mp3 = work / f"voz_{i:02d}.mp3"
        words = tts(fala, mp3, args.velocidade)
        dur = probe_duration(mp3)
        for s, e, t in words:
            all_words.append({"start": offset + s, "end": offset + e, "text": t, "cena": i,
                              "destaque": norm(t) in destaque and norm(t) != ""})
        audio_files.append(mp3)
        durations.append(dur)
        offset += dur
    lista = work / "voz_lista.txt"
    lista.write_text("".join(f"file '{p.name}'\n" for p in audio_files), encoding="utf-8")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lista.name,
         "-c:a", "pcm_s16le", "-ar", "44100", "narracao.wav"], cwd=work)
    total = probe_duration(work / "narracao.wav")
    log(f"   narracao: {total:.1f}s")

    log("4/6 animando as imagens (zoom lento)...")
    clips = []
    for i, (frame, dur) in enumerate(zip(frames, durations)):
        clips.append(scene_clip(frame, dur, i, work / f"cena_{i:02d}.mp4"))
    (work / "cenas_lista.txt").write_text("".join(f"file '{c.name}'\n" for c in clips), encoding="utf-8")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", "cenas_lista.txt",
         "-c", "copy", "visual.mp4"], cwd=work)

    log("5/6 montando legendas...")
    build_ass(all_words, work / "legendas.ass")
    fonts = work / "fonts"
    fonts.mkdir(exist_ok=True)
    shutil.copy(FONT_FILE, fonts / FONT_FILE.name)

    log("6/6 juntando tudo...")
    final = work / "final.mp4"
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", "visual.mp4", "-i", "narracao.wav"]
    songs = sorted(SONGS_DIR.glob("*.mp3"))
    if args.musica > 0 and songs:
        cmd += ["-stream_loop", "-1", "-i", str(random.choice(songs))]
        fade = max(total - 2, 0)
        fc = (f"[0:v]subtitles=legendas.ass:fontsdir=fonts[v];"
              f"[2:a]volume={args.musica},afade=t=out:st={fade:.2f}:d=2[m];"
              f"[1:a][m]amix=inputs=2:duration=first:normalize=0[a]")
    else:
        fc = "[0:v]subtitles=legendas.ass:fontsdir=fonts[v];[1:a]anull[a]"
    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", f"{total:.2f}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", final.name]
    run(cmd, cwd=work)

    (work / "creditos.txt").write_text(
        "Creditos das imagens (cole na descricao do video quando a licenca pedir atribuicao, ex: CC BY / CC BY-SA):\n\n"
        + "\n".join(creditos) + "\n", encoding="utf-8")
    (work / "publicar.txt").write_text(
        f"TITULO:\n{plan.get('titulo', '')}\n\nDESCRICAO:\n{plan.get('descricao', '')}\n\n"
        "ROTEIRO:\n" + "\n".join(c["texto"].replace("*", "") for c in plan["cenas"]) + "\n",
        encoding="utf-8")
    for tmp in list(work.glob("cena_*.mp4")) + list(work.glob("voz_*.mp3")) + [work / "visual.mp4"]:
        tmp.unlink(missing_ok=True)
    log(f"PRONTO: {final}")
    print(f"VIDEO_FILE={final}")


if __name__ == "__main__":
    main()
