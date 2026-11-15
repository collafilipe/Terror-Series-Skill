"""
Vozes do ElevenLabs para as series (opcional). So e usado se existir o arquivo estudio/elevenlabs_key.txt
com a chave de API. As vozes de cada personagem ficam em estudio/vozes_elevenlabs.json.

  .venv\\Scripts\\python.exe estudio\\eleven.py listar      -> mostra as vozes da sua conta e o saldo de caracteres
  .venv\\Scripts\\python.exe estudio\\eleven.py testar      -> grava uma frase de teste com a voz do narrador
"""

import base64
import json
import sys
from pathlib import Path

import requests

AQUI = Path(__file__).resolve().parent
ARQ_CHAVE = AQUI / "elevenlabs_key.txt"
ARQ_VOZES = AQUI / "vozes_elevenlabs.json"
API = "https://api.elevenlabs.io/v1"
MODELO = "eleven_multilingual_v2"

# personagem (os mesmos nomes de drama.PERSONAGENS) -> voz. Preencha "voice_id" com ids do comando "listar".
PADRAO = {
    "narrador": {"voice_id": "", "stability": 0.45, "style": 0.35},
    "jovem": {"voice_id": "", "stability": 0.4, "style": 0.4},
    "idoso": {"voice_id": "", "stability": 0.5, "style": 0.3},
    "idoso_radio": {"voice_id": "", "stability": 0.5, "style": 0.3},
    "idosa": {"voice_id": "", "stability": 0.5, "style": 0.3},
    "mulher": {"voice_id": "", "stability": 0.45, "style": 0.3},
    "mulher_radio": {"voice_id": "", "stability": 0.45, "style": 0.3},
    "crianca": {"voice_id": "", "stability": 0.4, "style": 0.4},
    "crianca_interfone": {"voice_id": "", "stability": 0.4, "style": 0.4},
}


def chave():
    if not ARQ_CHAVE.exists():
        return None
    k = ARQ_CHAVE.read_text(encoding="utf-8").strip()
    return k or None


def vozes():
    if not ARQ_VOZES.exists():
        ARQ_VOZES.write_text(json.dumps(PADRAO, ensure_ascii=False, indent=2), encoding="utf-8")
    return json.loads(ARQ_VOZES.read_text(encoding="utf-8"))


def disponivel(personagem):
    """True se ha chave e uma voz configurada para o personagem."""
    if not chave():
        return False
    v = vozes().get(personagem.replace("narrador_andrew", "narrador").replace("narrador_brian", "narrador"), {})
    return bool(v.get("voice_id"))


def falar(personagem, texto, destino_mp3):
    """Gera o mp3 e devolve [(ini, fim, palavra)] a partir do alinhamento por caractere."""
    v = vozes()[personagem]
    r = requests.post(f"{API}/text-to-speech/{v['voice_id']}/with-timestamps",
                      headers={"xi-api-key": chave(), "Content-Type": "application/json"},
                      json={"text": texto, "model_id": MODELO,
                            "voice_settings": {"stability": v.get("stability", 0.45), "similarity_boost": 0.8,
                                               "style": v.get("style", 0.3), "use_speaker_boost": True}},
                      timeout=120)
    if r.status_code != 200:
        raise RuntimeError(f"ElevenLabs {r.status_code}: {r.text[:300]}")
    dados = r.json()
    Path(destino_mp3).write_bytes(base64.b64decode(dados["audio_base64"]))
    al = dados.get("alignment") or {}
    chars = al.get("characters", [])
    ini = al.get("character_start_times_seconds", [])
    fim = al.get("character_end_times_seconds", [])
    palavras, atual, a0, b0 = [], "", None, None
    for c, a, b in zip(chars, ini, fim):
        if c.isspace():
            if atual:
                palavras.append((a0, b0, atual))
            atual, a0 = "", None
        else:
            if a0 is None:
                a0 = a
            atual += c
            b0 = b
    if atual:
        palavras.append((a0, b0, atual))
    return palavras


def _listar():
    k = chave()
    if not k:
        raise SystemExit(f"Falta a chave. Cole a sua chave de API no arquivo {ARQ_CHAVE}")
    h = {"xi-api-key": k}
    u = requests.get(f"{API}/user/subscription", headers=h, timeout=60)
    if u.status_code == 200:
        s = u.json()
        print(f"Plano: {s.get('tier')} | caracteres usados: {s.get('character_count')} de {s.get('character_limit')}")
    else:
        print(f"Nao consegui ler o plano ({u.status_code}): {u.text[:200]}")
    r = requests.get(f"{API}/voices", headers=h, timeout=60)
    if r.status_code != 200:
        raise SystemExit(f"Erro {r.status_code}: {r.text[:300]}")
    for v in r.json().get("voices", []):
        rot = v.get("labels") or {}
        print(f"{v['voice_id']}  {v['name']:<28} {rot.get('gender', '')} {rot.get('age', '')} {rot.get('accent', '')} "
              f"{rot.get('description', '')} [{v.get('category', '')}]")
    vozes()
    print(f"\nEscolha as vozes e preencha os voice_id em: {ARQ_VOZES}")


def _testar():
    if not disponivel("narrador"):
        raise SystemExit("Preencha a chave e o voice_id do narrador primeiro (comando: listar).")
    saida = AQUI / "teste_elevenlabs.mp3"
    p = falar("narrador", "Três e sete. O interfone toca. Não tem número no botão. Mas você sabe qual é.", saida)
    print(f"ok: {saida} ({len(p)} palavras)")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "listar"
    _testar() if cmd == "testar" else _listar()
