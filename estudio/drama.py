"""
Audio de "radionovela" para as series: vozes por personagem (Edge TTS + filtros) e sons de ambiente/efeitos
gerados por codigo (grilos, chuva, zumbido, interfone, radio, elevador, coracao, impacto).
"""

import asyncio
import subprocess
import wave
from pathlib import Path

import edge_tts
import numpy as np

SR = 44100
_rng = np.random.default_rng(11)

# voz, velocidade, tom, filtro ffmpeg (None = limpa)
RADIO = "highpass=f=450,lowpass=f=2800,acompressor=threshold=-24dB:ratio=6:makeup=6,volume=1.3"
INTERFONE = "highpass=f=650,lowpass=f=2300,acrusher=bits=9:mix=0.35,volume=1.4"
PERSONAGENS = {
    "narrador": ("pt-BR-AntonioNeural", "+4%", "+0Hz", None),
    "narrador_andrew": ("en-US-AndrewMultilingualNeural", "+6%", "+0Hz", None),
    "narrador_brian": ("en-US-BrianMultilingualNeural", "+6%", "+0Hz", None),
    "jovem": ("en-US-BrianMultilingualNeural", "+8%", "+6Hz", None),
    "idoso_radio": ("en-US-AndrewMultilingualNeural", "-6%", "-6Hz", RADIO),
    "idoso": ("en-US-AndrewMultilingualNeural", "-6%", "-6Hz", None),
    "idosa": ("pt-BR-FranciscaNeural", "-12%", "-12Hz", None),
    "mulher": ("pt-BR-ThalitaMultilingualNeural", "+0%", "+0Hz", None),
    "mulher_radio": ("pt-BR-ThalitaMultilingualNeural", "+0%", "+0Hz", RADIO),
    "crianca_interfone": ("pt-BR-ThalitaMultilingualNeural", "-6%", "+38Hz", INTERFONE),
    "crianca": ("pt-BR-ThalitaMultilingualNeural", "-6%", "+38Hz", None),
    # O Relojoeiro
    "detetive": ("pt-BR-AntonioNeural", "-4%", "-4Hz", None),
    "coronel": ("en-US-AndrewMultilingualNeural", "-4%", "-8Hz", None),
    "primeira_dama": ("pt-BR-FranciscaNeural", "-4%", "-4Hz", None),
}


# ------------------------------------------------------------------ voz
async def _tts(texto, voz, rate, pitch, destino):
    comm = edge_tts.Communicate(texto, voz, rate=rate, pitch=pitch, boundary="WordBoundary")
    palavras = []
    with open(destino, "wb") as f:
        async for ch in comm.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                ini = ch["offset"] / 1e7
                palavras.append((ini, ini + ch["duration"] / 1e7, ch["text"]))
    return palavras


def ler_wav(path):
    with wave.open(str(path)) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768


def falar(personagem, texto, pasta, nome):
    """Devolve (audio numpy, [(ini, fim, palavra)]) ja sem silencio nas pontas e com o filtro do personagem."""
    voz, rate, pitch, filtro = PERSONAGENS[personagem]
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    mp3 = pasta / f"{nome}.mp3"
    palavras = None
    # cache: a mesma fala com a mesma voz nunca e gerada (nem cobrada) duas vezes
    import hashlib
    import json as _json
    try:
        import eleven
        origem = "11:" + eleven.vozes()[personagem]["voice_id"] if eleven.disponivel(personagem) else "edge:" + voz + rate + pitch
    except Exception:  # noqa: BLE001
        origem = "edge:" + voz + rate + pitch
    chave_cache = hashlib.sha1(f"{origem}|{filtro}|{texto}".encode("utf-8")).hexdigest()[:20]
    cdir = Path(__file__).resolve().parent / "cache_vozes"
    cdir.mkdir(exist_ok=True)
    cwav, cjson = cdir / f"{chave_cache}.wav", cdir / f"{chave_cache}.json"
    if cwav.exists() and cjson.exists():
        return ler_wav(cwav), [tuple(x) for x in _json.loads(cjson.read_text(encoding="utf-8"))]
    try:  # ElevenLabs, se a chave e a voz do personagem estiverem configuradas
        import eleven
        if eleven.disponivel(personagem):
            palavras = eleven.falar(personagem, texto, mp3)
    except Exception as exc:  # noqa: BLE001
        print(f"[aviso] ElevenLabs falhou para '{personagem}' ({exc}); usando a voz gratuita")
        palavras = None
    for _ in range(5 if not palavras else 0):
        try:
            palavras = asyncio.run(_tts(texto, voz, rate, pitch, mp3))
            if palavras and mp3.stat().st_size > 800:
                break
        except Exception:  # noqa: BLE001
            pass
        import time
        time.sleep(2)
    if not palavras:
        raise RuntimeError(f"voz falhou: {texto[:50]}")
    ini = max(0.0, palavras[0][0] - 0.03)
    fim = palavras[-1][1] + 0.12
    af = "loudnorm=I=-16:TP=-1.5" + ("," + filtro if filtro else "")
    wav = pasta / f"{nome}.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{ini:.3f}", "-to", f"{fim:.3f}", "-i", str(mp3), "-af", af,
                    "-ar", str(SR), "-ac", "1", str(wav)], check=True)
    resultado = [(a - ini, b - ini, t) for a, b, t in palavras]
    import shutil as _sh
    _sh.copy(wav, cwav)
    cjson.write_text(_json.dumps(resultado, ensure_ascii=False), encoding="utf-8")
    return ler_wav(wav), resultado


# ------------------------------------------------------------------ sons de ambiente
def _t(dur):
    return np.arange(int(dur * SR)) / SR


def _passa_baixa(x, n):
    return np.convolve(x, np.ones(n) / n, mode="same")


def grilos(dur):
    t = _t(dur)
    out = np.zeros(len(t))
    for f, per, fase in ((4350, 0.42, 0.0), (4900, 0.55, 0.2), (5300, 0.71, 0.4)):
        tt = (t + fase) % per
        pulso = np.zeros(len(t))
        for k in range(3):
            pulso += np.exp(-((tt - 0.03 - k * 0.045) ** 2) / (2 * 0.008 ** 2))
        out += np.sin(2 * np.pi * f * t) * pulso
    return out * 0.05


def chuva(dur):
    n = int(dur * SR)
    r = _rng.normal(0, 1, n)
    r = r - _passa_baixa(r, 12)
    env = 0.75 + 0.25 * np.sin(2 * np.pi * 0.13 * _t(dur) + 1)
    return r * env * 0.035


def zumbido(dur):
    t = _t(dur)
    z = np.sin(2 * np.pi * 120 * t) * 0.5 + np.sin(2 * np.pi * 240 * t) * 0.25 + np.sin(2 * np.pi * 360 * t) * 0.12
    z += np.sin(2 * np.pi * 60 * t) * 0.4
    return z * 0.022 * (0.9 + 0.1 * np.sin(2 * np.pi * 0.4 * t))


def ronco_grave(dur, cresce=True):
    n = int(dur * SR)
    r = _passa_baixa(_rng.normal(0, 1, n), 500) * 8
    t = _t(dur)
    r += np.sin(2 * np.pi * 43 * t) * 0.6
    env = (t / dur) ** 1.5 if cresce else np.ones(n)
    return r * env * 0.16


def coracao(dur, bpm_ini=70, bpm_fim=115):
    n = int(dur * SR)
    out = np.zeros(n)
    L = int(0.22 * SR)
    tb = np.arange(L) / SR
    th = np.sin(2 * np.pi * 50 * tb) * np.exp(-tb * 20)
    s = 0.0
    while s < dur:
        for off, amp in ((0, 1.0), (0.2, 0.65)):
            i = int((s + off) * SR)
            j = min(n, i + L)
            if i < n:
                out[i:j] += th[: j - i] * amp
        bpm = bpm_ini + (bpm_fim - bpm_ini) * s / dur
        s += 60 / bpm
    return out * 0.5


def interfone(toques=3):
    out = []
    for _ in range(toques):
        t = _t(0.9)
        tom = np.sign(np.sin(2 * np.pi * 25 * t))  # trinado
        s = (np.sin(2 * np.pi * 1420 * t) * (tom > 0) + np.sin(2 * np.pi * 1760 * t) * (tom <= 0)) * 0.16
        out += [s, np.zeros(int(0.7 * SR))]
    return np.concatenate(out)


def chiado_radio(dur=0.5, bip=True):
    n = int(dur * SR)
    r = _rng.normal(0, 1, n)
    r = (r - _passa_baixa(r, 6)) * 0.09 * np.hanning(n)
    if bip:
        t = _t(0.12)
        r = np.concatenate([r, np.sin(2 * np.pi * 1050 * t) * 0.12 * np.hanning(len(t))])
    return r


def plim_elevador():
    t = _t(1.2)
    return (np.sin(2 * np.pi * 988 * t) * np.exp(-t * 4) * (t < 0.5)
            + np.sin(2 * np.pi * 784 * np.clip(t - 0.35, 0, None)) * np.exp(-np.clip(t - 0.35, 0, None) * 4) * (t >= 0.35)) * 0.14


def porta_arrastando(dur=1.4):
    n = int(dur * SR)
    r = _passa_baixa(_rng.normal(0, 1, n), 40) * 3
    t = _t(dur)
    return (r + np.sin(2 * np.pi * (90 + 30 * t) * t) * 0.3) * np.hanning(n) * 0.12


def impacto(dur=1.8):
    t = _t(dur)
    b = np.sin(2 * np.pi * np.cumsum(np.linspace(75, 30, len(t))) / SR) * np.exp(-t * 2.4)
    b += _passa_baixa(_rng.normal(0, 1, len(t)), 90) * np.exp(-t * 4) * 2.5
    return b * 0.6


def passos(n_passos=4, intervalo=0.55):
    out = np.zeros(int((n_passos * intervalo + 0.3) * SR))
    L = int(0.09 * SR)
    tp = np.arange(L) / SR
    for k in range(n_passos):
        p = (_passa_baixa(_rng.normal(0, 1, L), 25) * 4 + np.sin(2 * np.pi * 140 * tp)) * np.exp(-tp * 45)
        i = int(k * intervalo * SR)
        out[i:i + L] += p * 0.25
    return out


def tique(dur):
    n = int(dur * SR)
    out = np.zeros(n)
    L = int(0.012 * SR)
    c = np.sin(2 * np.pi * 2600 * np.arange(L) / SR) * np.hanning(L) * 0.05
    for s in np.arange(0, dur, 1.0):
        i = int(s * SR)
        if i + L < n:
            out[i:i + L] += c
    return out


def campainha():
    """Campainha de onibus: dois toques eletronicos."""
    t = _t(0.9)
    a = np.sin(2 * np.pi * 1318 * t) * np.exp(-t * 6) * (t < 0.42)
    t2 = np.clip(t - 0.42, 0, None)
    b = np.sin(2 * np.pi * 1047 * t2) * np.exp(-t2 * 5) * (t >= 0.42)
    return (a + b) * 0.2


def freio_ar(dur=1.1):
    n = int(dur * SR)
    r = _rng.normal(0, 1, n)
    r = r - _passa_baixa(r, 8)
    t = _t(dur)
    return r * np.exp(-t * 3.2) * 0.16


def motor(dur):
    """Ronco continuo de motor de onibus."""
    t = _t(dur)
    r = _passa_baixa(_rng.normal(0, 1, len(t)), 300) * 5
    m = np.sin(2 * np.pi * 48 * t) * 0.7 + np.sin(2 * np.pi * 96 * t) * 0.3 + np.sin(2 * np.pi * 31 * t) * 0.3
    return (m * (0.85 + 0.15 * np.sin(2 * np.pi * 0.5 * t)) + r) * 0.12


def chuva_forte(dur):
    """Chuva pesada batendo em janela, com rajadas de vento."""
    n = int(dur * SR)
    t = _t(dur)
    r = _rng.normal(0, 1, n)
    agudo = r - _passa_baixa(r, 10)
    grave = _passa_baixa(_rng.normal(0, 1, n), 160) * 5
    rajada = 0.7 + 0.3 * np.sin(2 * np.pi * 0.09 * t + 0.7) * np.sin(2 * np.pi * 0.23 * t)
    return (agudo * 0.05 + grave * 0.035) * rajada


def trovao(dur=3.2):
    """Estalo curto seguido de um ronco grave que rola e some."""
    n = int(dur * SR)
    t = _t(dur)
    ronco = _passa_baixa(_rng.normal(0, 1, n), 420) * 14
    ronco *= (0.55 + 0.45 * np.sin(2 * np.pi * 2.3 * t + 1) * np.sin(2 * np.pi * 0.9 * t)) * np.exp(-t * 1.1)
    estalo = _rng.normal(0, 1, n)
    estalo = (estalo - _passa_baixa(estalo, 30)) * np.exp(-t * 16) * 0.5
    sub = np.sin(2 * np.pi * 38 * t) * np.exp(-t * 1.6) * 0.5
    return (ronco + estalo + sub) * 0.5 * np.minimum(1, t / 0.01)


def pagina(dur=0.55):
    """Folha de papel virando."""
    n = int(dur * SR)
    t = _t(dur)
    r = _rng.normal(0, 1, n)
    r = r - _passa_baixa(r, 5)
    env = np.exp(-((t - 0.16) ** 2) / (2 * 0.07 ** 2)) + 0.6 * np.exp(-((t - 0.4) ** 2) / (2 * 0.04 ** 2))
    return r * env * 0.1


def lapis(dur=1.3):
    """Lapis riscando o papel: tracos curtos e irregulares."""
    n = int(dur * SR)
    t = _t(dur)
    r = _rng.normal(0, 1, n)
    r = _passa_baixa(r - _passa_baixa(r, 4), 2)
    env = np.zeros(n)
    s = 0.02
    rr = np.random.default_rng(5)
    while s < dur - 0.12:
        L = rr.uniform(0.07, 0.16)
        i, j = int(s * SR), int(min(dur, s + L) * SR)
        env[i:j] = np.hanning(j - i) * rr.uniform(0.6, 1.0)
        s += L + rr.uniform(0.02, 0.09)
    return r * env * 0.16


def luz_cai():
    """Estalo eletrico da luz caindo, com o zumbido morrendo."""
    t = _t(0.9)
    cl = _rng.normal(0, 1, len(t)) * np.exp(-t * 60) * 0.5
    z = np.sin(2 * np.pi * np.cumsum(np.linspace(120, 35, len(t))) / SR) * np.exp(-t * 5) * 0.35
    return cl + z


def alarme(toques=2):
    """Alarme curto de alerta (dois tons graves)."""
    out = []
    for _ in range(toques):
        t = _t(0.42)
        out += [(np.sin(2 * np.pi * 620 * t) + 0.5 * np.sin(2 * np.pi * 930 * t)) * np.hanning(len(t)) * 0.11,
                np.zeros(int(0.2 * SR))]
    return np.concatenate(out)


def portao(dur=2.2):
    """Portao pesado de metal correndo e batendo no fim."""
    n = int(dur * SR)
    t = _t(dur)
    r = _passa_baixa(_rng.normal(0, 1, n), 60) * 4 * (0.7 + 0.3 * np.sin(2 * np.pi * 9 * t))
    motor = np.sin(2 * np.pi * 96 * t) * 0.35 + np.sin(2 * np.pi * 191 * t) * 0.18          # motor eletrico
    rang = np.sin(2 * np.pi * np.cumsum(520 + 90 * np.sin(2 * np.pi * 1.7 * t)) / SR) * 0.07 * (0.5 + 0.5 * np.sin(2 * np.pi * 3.1 * t))
    corpo = (r + np.sin(2 * np.pi * 62 * t) * 0.5 + motor + rang) * np.minimum(1, t / 0.2) * (t < dur - 0.35) * 0.1
    tb = np.clip(t - (dur - 0.35), 0, None)
    batida = (np.sin(2 * np.pi * 70 * tb) + 0.4 * np.sin(2 * np.pi * 310 * tb)) * np.exp(-tb * 14) * (t >= dur - 0.35) * 0.4
    return corpo + batida


def tique_para(n_tiques=4):
    """Som-assinatura: o tique de um relogio que para de repente."""
    out = np.zeros(int((n_tiques * 0.5 + 0.2) * SR))
    L = int(0.02 * SR)
    for k in range(n_tiques):
        f = 2400 if k % 2 == 0 else 1900
        c = np.sin(2 * np.pi * f * np.arange(L) / SR) * np.hanning(L) * 0.22
        i = int(k * 0.5 * SR)
        out[i:i + L] += c
    return out


def passos_marmore(n_passos=4, intervalo=0.5):
    """Passos de sapato em piso duro, com um pouco de eco."""
    out = np.zeros(int((n_passos * intervalo + 0.5) * SR))
    L = int(0.07 * SR)
    tp = np.arange(L) / SR
    for k in range(n_passos):
        p = (_rng.normal(0, 1, L) * 0.6 + np.sin(2 * np.pi * 900 * tp) + np.sin(2 * np.pi * 210 * tp)) * np.exp(-tp * 70)
        i = int(k * intervalo * SR)
        out[i:i + L] += p * 0.16
        j = i + int(0.11 * SR)
        out[j:j + L] += p * 0.05
    return out


def vento(dur):
    """Vento assobiando baixo, em ondas."""
    n = int(dur * SR)
    t = _t(dur)
    r = _passa_baixa(_rng.normal(0, 1, n), 70) * 6
    onda = 0.5 + 0.5 * np.sin(2 * np.pi * 0.11 * t + 2) * np.sin(2 * np.pi * 0.04 * t + 0.5)
    assobio = np.sin(2 * np.pi * (410 + 60 * np.sin(2 * np.pi * 0.13 * t)) * t) * 0.012 * onda
    return r * 0.05 * onda + assobio


def trovoada(dur):
    """Trovoes distantes espalhados pela cena (bem abafados)."""
    n = int(dur * SR)
    out = np.zeros(n)
    rr = np.random.default_rng(int(dur * 100) % 97)
    s = rr.uniform(2.5, 5.0)
    while s < dur - 2.5:
        tr = _passa_baixa(trovao(2.8), 30) * rr.uniform(0.5, 0.9)
        i = int(s * SR)
        j = min(n, i + len(tr))
        out[i:j] += tr[: j - i]
        s += rr.uniform(8, 14)
    return out


def passos_agua(n_passos=8, intervalo=0.52):
    """Passos em chao molhado: batida abafada + respingo."""
    out = np.zeros(int((n_passos * intervalo + 0.5) * SR))
    L = int(0.2 * SR)
    tp = np.arange(L) / SR
    for k in range(n_passos):
        r = _rng.normal(0, 1, L)
        resp = (r - _passa_baixa(r, 7)) * np.exp(-tp * 22) * 0.5
        bat = (_passa_baixa(_rng.normal(0, 1, L), 30) * 4 + np.sin(2 * np.pi * 110 * tp)) * np.exp(-tp * 40)
        i = int(k * intervalo * SR)
        out[i:i + L] += (resp + bat) * 0.2
    return out


def passos_chegando(dur=12.0, intervalo=0.62):
    """Passos em marmore vindo de longe: comecam baixos e com eco, terminam perto."""
    out = np.zeros(int((dur + 0.5) * SR))
    L = int(0.07 * SR)
    tp = np.arange(L) / SR
    s = 0.0
    while s < dur:
        k = s / dur
        p = (_rng.normal(0, 1, L) * 0.6 + np.sin(2 * np.pi * 900 * tp) + np.sin(2 * np.pi * 210 * tp)) * np.exp(-tp * 70)
        i = int(s * SR)
        out[i:i + L] += p * (0.05 + 0.2 * k)
        j = i + int(0.13 * SR)
        out[j:j + L] += p * 0.05 * (1 - 0.6 * k)
        s += intervalo
    return out


def macaneta():
    """Macaneta forcada duas vezes: porta trancada."""
    out = np.zeros(int(1.1 * SR))
    L = int(0.09 * SR)
    tp = np.arange(L) / SR
    for s, amp in ((0.0, 1.0), (0.14, 0.7), (0.5, 1.0), (0.64, 0.8)):
        c = (np.sin(2 * np.pi * 1700 * tp) * 0.5 + np.sin(2 * np.pi * 520 * tp) + _rng.normal(0, 1, L) * 0.4) * np.exp(-tp * 60)
        i = int(s * SR)
        out[i:i + L] += c * 0.16 * amp
    return out


def rangido(dur=1.4):
    """Porta de madeira rangendo."""
    t = _t(dur)
    f = 180 + 120 * np.sin(2 * np.pi * 0.7 * t) + 40 * np.sin(2 * np.pi * 9 * t)
    s = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.5 + np.sin(2 * np.pi * np.cumsum(f * 2.01) / SR) * 0.5
    return _passa_baixa(s, 6) * np.hanning(len(t)) * 0.06


def bipes(dur):
    """Bipes baixos e espacados de equipamento de seguranca."""
    n = int(dur * SR)
    out = np.zeros(n)
    L = int(0.07 * SR)
    c = np.sin(2 * np.pi * 1480 * np.arange(L) / SR) * np.hanning(L) * 0.05
    for s in np.arange(0.8, dur, 2.3):
        i = int(s * SR)
        if i + L < n:
            out[i:i + L] += c
    return out


def tensao(dur):
    """Tom grave e continuo de suspense, crescendo devagar (nao e musica: um unico zumbido)."""
    t = _t(dur)
    z = np.sin(2 * np.pi * 55 * t) * 0.6 + np.sin(2 * np.pi * 55.7 * t) * 0.6 + np.sin(2 * np.pi * 110.4 * t) * 0.2
    return z * (0.35 + 0.65 * t / max(dur, 0.1)) * 0.09


# ------------------------------------------------------------------ mixagem
class Mix:
    def __init__(self, dur):
        self.buf = np.zeros(int(dur * SR) + SR, dtype=np.float64)

    def add(self, sinal, ini, vol=1.0, fade=0.0):
        s = np.asarray(sinal, dtype=np.float64).copy()
        if fade > 0 and len(s) > 2 * int(fade * SR):
            f = int(fade * SR)
            s[:f] *= np.linspace(0, 1, f)
            s[-f:] *= np.linspace(1, 0, f)
        i = int(ini * SR)
        j = min(len(self.buf), i + len(s))
        if i < len(self.buf):
            self.buf[i:j] += s[: j - i] * vol

    def salvar(self, destino, dur=None):
        x = self.buf if dur is None else self.buf[: int(dur * SR)]
        pico = np.abs(x).max()
        if pico > 0.97:
            x = x / pico * 0.97
        with wave.open(str(destino), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes((x * 32767).astype(np.int16).tobytes())
