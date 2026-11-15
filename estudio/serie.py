"""
Series interativas "E SE..." (terror/suspense em capitulos, o publico escolhe A ou B nos comentarios).

Uso:
  .venv\\Scripts\\python.exe estudio\\serie.py nova "Nome da serie" "E se ... ? (premissa)"
  .venv\\Scripts\\python.exe estudio\\serie.py capitulo <serie>                  (capitulo 1)
  .venv\\Scripts\\python.exe estudio\\serie.py capitulo <serie> --escolha B      (proximos: o que o publico votou)
  .venv\\Scripts\\python.exe estudio\\serie.py listar

Cada serie fica em estudio/series/<nome>/ com serie.json (premissa, resumos, escolhas) e uma pasta por capitulo.
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERIES = ROOT / "estudio" / "series"
PY = ROOT / ".venv" / "Scripts" / "python.exe"
sys.path.insert(0, str(ROOT / "estudio"))
from historia_shorts import slugify  # noqa: E402


def carregar(slug):
    arq = SERIES / slug / "serie.json"
    if not arq.exists():
        disponiveis = ", ".join(p.name for p in SERIES.glob("*") if (p / "serie.json").exists()) or "nenhuma"
        raise SystemExit(f"Serie '{slug}' nao existe. Series: {disponiveis}")
    return json.loads(arq.read_text(encoding="utf-8")), arq


def salvar(dados, arq):
    arq.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_nova(nome, premissa):
    SERIES.mkdir(parents=True, exist_ok=True)
    slug = slugify(nome)
    pasta = SERIES / slug
    if (pasta / "serie.json").exists():
        raise SystemExit(f"Ja existe uma serie '{slug}'.")
    numero = len([p for p in SERIES.glob("*") if (p / "serie.json").exists()]) + 1
    pasta.mkdir(parents=True, exist_ok=True)
    salvar({"nome": nome, "numero": numero, "premissa": premissa, "criada": time.strftime("%Y-%m-%d"),
            "capitulos": []}, pasta / "serie.json")
    print(f"Serie criada: E SE #{numero} - {nome}  (pasta: {pasta})")
    print(f"Proximo passo: serie.py capitulo {slug}")


def contexto_do_capitulo(dados, n, escolha, extra):
    caps = dados["capitulos"]
    linhas = [f'SERIE: "E SE #{dados["numero"]}: {dados["nome"]}"',
              f"PREMISSA: {dados['premissa']}",
              f"ESTE E O CAPITULO {n}."]
    if caps:
        prot = caps[0].get("protagonista")
        if prot:
            linhas.append(f"PROTAGONISTA (mantenha o mesmo tipo de boneco e aparencia): {prot}")
        linhas.append("CAPITULOS ANTERIORES (respeite tudo isso):")
        for c in caps:
            esc = c.get("escolha")
            txt_esc = f" O publico escolheu {esc} ({c.get(esc.lower(), '')})." if esc else ""
            linhas.append(f'- Cap {c["num"]} "{c["titulo"]}": {c["resumo"]} Dilema: {c["pergunta"]} '
                          f'A) {c["a"]} B) {c["b"]}.{txt_esc}')
        ultimo = caps[-1]
        linhas.append(f"O PUBLICO ESCOLHEU NO CAPITULO ANTERIOR: {escolha} - \"{ultimo[escolha.lower()]}\". "
                      "Este capitulo comeca mostrando a consequencia dessa escolha.")
    else:
        linhas.append("E o primeiro capitulo: apresente a premissa e o protagonista e termine no primeiro dilema.")
    if extra:
        linhas.append(f"PEDIDO DO AUTOR PARA ESTE CAPITULO: {extra}")
    return "\n".join(linhas)


def cmd_capitulo(slug, escolha, extra, sem_revisao):
    dados, arq = carregar(slug)
    caps = dados["capitulos"]
    n = len(caps) + 1
    if caps:
        if not escolha or escolha.upper() not in ("A", "B"):
            u = caps[-1]
            raise SystemExit(f"Diga o que o publico votou no capitulo {u['num']}: --escolha A ({u['a']}) "
                             f"ou --escolha B ({u['b']})")
        escolha = escolha.upper()
        caps[-1]["escolha"] = escolha
        salvar(dados, arq)
    pasta = SERIES / slug / f"cap_{n:02d}"
    pasta.mkdir(parents=True, exist_ok=True)
    ctx = pasta / "contexto.txt"
    ctx.write_text(contexto_do_capitulo(dados, n, escolha, extra), encoding="utf-8")
    rotulo = f"E SE #{dados['numero']} · CAPITULO {n}"
    cmd = [str(PY), str(ROOT / "estudio" / "gerar3d.py"), dados["nome"], "--contexto", str(ctx),
           "--serie-rotulo", rotulo, "--capitulo", str(n), "--saida", str(pasta), "--cenas", "8"]
    if sem_revisao:
        cmd.append("--sem-revisao")
    print(f"Gerando {rotulo} ... (uns 20-25 minutos)")
    p = subprocess.run(cmd, cwd=str(ROOT))
    if p.returncode != 0 or not (pasta / "final.mp4").exists():
        raise SystemExit("Falhou ao gerar o capitulo.")
    plano = json.loads((pasta / "plano.json").read_text(encoding="utf-8"))
    caps.append({"num": n, "titulo": plano.get("titulo", ""), "resumo": plano.get("resumo", ""),
                 "pergunta": plano.get("pergunta", ""), "a": plano.get("opcao_a", ""), "b": plano.get("opcao_b", ""),
                 "protagonista": plano.get("protagonista", ""), "escolha": None, "video": str(pasta / "final.mp4")})
    salvar(dados, arq)
    print("\n================ CAPITULO PRONTO ================")
    print(f"Video: {pasta / 'final.mp4'}")
    print(f"Dilema: {plano.get('pergunta')}   A) {plano.get('opcao_a')}   B) {plano.get('opcao_b')}")
    print(f"Legenda pronta para o post: {pasta / 'publicar.txt'}")
    print(f"Depois da votacao: serie.py capitulo {slug} --escolha A  (ou B)")


def cmd_listar():
    for p in sorted(SERIES.glob("*")):
        arq = p / "serie.json"
        if not arq.exists():
            continue
        d = json.loads(arq.read_text(encoding="utf-8"))
        caps = d["capitulos"]
        status = ""
        if caps:
            u = caps[-1]
            status = f" | ultimo: cap {u['num']} ({u['pergunta']} A) {u['a']} B) {u['b']})"
        print(f"{p.name}: E SE #{d['numero']} - {d['nome']} | {len(caps)} capitulo(s){status}")


def main():
    ap = argparse.ArgumentParser(description="Series interativas E SE...")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("nova")
    a.add_argument("nome")
    a.add_argument("premissa")
    b = sub.add_parser("capitulo")
    b.add_argument("serie")
    b.add_argument("--escolha", help="A ou B: o que o publico votou no capitulo anterior")
    b.add_argument("--extra", default="", help="pedido opcional para este capitulo")
    b.add_argument("--sem-revisao", action="store_true")
    sub.add_parser("listar")
    args = ap.parse_args()
    if args.cmd == "nova":
        cmd_nova(args.nome, args.premissa)
    elif args.cmd == "capitulo":
        cmd_capitulo(args.serie, args.escolha, args.extra, args.sem_revisao)
    else:
        cmd_listar()


if __name__ == "__main__":
    main()
