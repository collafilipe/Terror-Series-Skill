"""
Roda dentro do Blender:  blender -b --factory-startup -P render_cena.py -- cena.json
cena.json = {"codigo": "...", "frames": 150, "saida": "pasta", "so_testar": false, "amostra": 0}
Executa o codigo da cena (usando a biblioteca mundo3d como M), renderiza os
quadros em PNG e grava rotulos.json com a posicao 2D das etiquetas.
"""
import json
import math
import os
import random
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mundo3d as M  # noqa: E402
import palacio as P  # noqa: E402

cfg = json.load(open(sys.argv[sys.argv.index("--") + 1], encoding="utf-8"))
F = int(cfg["frames"])
saida = cfg["saida"]
os.makedirs(saida, exist_ok=True)

try:
    M.nova_cena(frames=F)
    M._rng.seed(cfg.get("seed", 1))
    M.LIMPAR = True
    ns = {"M": M, "P": P, "F": F, "T": cfg.get("marcas", {}), "math": math, "random": random.Random(cfg.get("seed", 1))}
    exec(compile(cfg["codigo"], "cena", "exec"), ns)
    sc = M.bpy.context.scene
    if sc.camera is None:
        M.cam_aerea((0, 0, 0), 60, 40, 1, F)
    if not any(o.name.startswith("Chao") or o.name.startswith("Grama") for o in M.bpy.data.objects):
        M.chao()
    M.suavizar_tudo()
    esc = M.limpar_frente_camera() if M.LIMPAR else []
    if esc:
        print("ESCONDIDOS_PERTO_DA_CAMERA:", esc)
except Exception:  # noqa: BLE001
    print("ERRO_CENA_INICIO")
    print(traceback.format_exc(limit=6))
    print("ERRO_CENA_FIM")
    sys.stdout.flush()
    os._exit(3)

if cfg.get("so_testar"):
    print("TESTE_OK")
    sys.stdout.flush()
    os._exit(0)

amostra = int(cfg.get("amostra") or 0)
if amostra:
    sc.frame_step = max(1, F // amostra)
if cfg.get("percentual"):  # previa rapida para a revisao visual
    sc.render.resolution_percentage = int(cfg["percentual"])
    try:
        sc.eevee.taa_render_samples = 8
    except AttributeError:
        pass
rot = M.projetar_rotulos()
json.dump(rot, open(os.path.join(saida, "rotulos.json"), "w", encoding="utf-8"))
M.renderizar(saida)
print("RENDER_OK")
sys.stdout.flush()
os._exit(0)
