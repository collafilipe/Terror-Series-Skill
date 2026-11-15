"""
Cenarios de O RELOJOEIRO (Palacio das Aguas). Usado no codigo das cenas como P (junto com M = mundo3d).
Medidas em metros, chao em z=0, camera padrao olhando para +Y. Bonecos em pe: rosto em z ~1.45.

  P.gabinete(raios=[quadros])            mesa, estante, janela com chuva, poltrona de costas e a mao caida com o relogio
                                         (P.RELOGIO = centro do mostrador, virado para -Y)
  P.corredor(alerta=f, grade=(f0, f1))   corredor de marmore de y=-6 a 16; porta do gabinete no fundo (y=16)
  P.sala_cameras(f_pulo)                 parede de monitores em y=3; no quadro f_pulo todas pulam de 02:10 para 02:17
                                         (P.MONITOR = centro de um monitor bom para close)
  P.salao(raios=[...])                   salao com lustre; P.suspeitos(F, some=('br_medica', f)) poe os seis em arco
  P.portaria()                           balcao com o livro de entradas (P.LIVRO, P.LINHA = ultima assinatura)
  P.patio(f_abre, raios=[...])           portao blindado, patio com chuva e a fachada do palacio ao fundo
  P.apagao(f0, f1)                       todas as luzes apagam entre f0 e f1
"""
import math
import os
import random

import bmesh
import bpy

import mundo3d as M

RELOGIO = (0.66, 2.15, 0.585)
MONITOR = (-0.75, 2.9, 1.75)
LIVRO = (0.0, 1.4, 1.1)
LINHA = (-0.05, 1.25, 1.1)
SUSPEITOS = [("br_primeira_dama", -3.125), ("br_medica", -1.875), ("br_secretario", -0.625),
             ("br_copeira", 0.625), ("br_cabo", 1.875), ("br_coronel", 3.125)]
Y_SUSPEITOS = 5.0
MADEIRA, MADEIRA_ESC, OURO = "#5a3c26", "#33211a", "#c9a24a"


# ------------------------------------------------------------------ pecas comuns
def _inicio(interior=True):
    M.LIMPAR = False
    if interior:
        M.ambiente("interior")


def _piso(arquivo, x0, x1, y0, y1, lado=2.0, pai=None, z=0.012, rug=0.35):
    """Piso com textura repetida (cada repeticao mede `lado` metros)."""
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in ((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z))]
    face = bm.faces.new(vs)
    uv = bm.loops.layers.uv.new()
    u1, v1 = (x1 - x0) / lado, (y1 - y0) / lado
    for loop, c in zip(face.loops, ((0, 0), (u1, 0), (u1, v1), (0, v1))):
        loop[uv].uv = c
    m = bpy.data.materials.new("Piso")
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Roughness"].default_value = rug
    tex = m.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(os.path.join(M.TEXTURAS, arquivo), check_existing=True)
    tex.interpolation = "Closest"
    m.node_tree.links.new(tex.outputs["Color"], p.inputs["Base Color"])
    return M._malha("Piso", bm, "#ffffff", pai, (0, 0, 0), (0, 0, 0), material=m)


def _sala(g, x0, x1, y0, y1, h, parede, rodape=MADEIRA_ESC, chao="#3a2a20", teto="#2c2622", lambri=None):
    cx, cy, w, d = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0
    M.caixa((w + 1, d + 1, 0.2), (cx, cy, -0.1), chao, g, nome="Chao_sala")
    for x in (x0 - 0.15, x1 + 0.15):
        M.caixa((0.3, d, h), (x, cy, h / 2), parede, g)
        M.caixa((0.36, d, 0.22), (x, cy, 0.11), rodape, g)
        if lambri:
            M.caixa((0.34, d, 1.0), (x, cy, 0.5), lambri, g)
    M.caixa((w + 0.6, 0.3, h), (cx, y1 + 0.15, h / 2), parede, g)
    M.caixa((w + 0.6, 0.36, 0.22), (cx, y1 + 0.13, 0.11), rodape, g)
    if lambri:
        M.caixa((w + 0.6, 0.34, 1.0), (cx, y1 + 0.14, 0.5), lambri, g)
    if teto:
        M.caixa((w + 0.8, d + 3, 0.2), (cx, cy - 1, h + 0.1), teto, g)


def _janela(g, x, y, z, larg=2.0, alt=2.5, cortina="#5c1a22", emissao=0.9):
    M.quadro_imagem("janela_chuva.png", (x, y - 0.02, z), larg, alt, rot=(90, 0, 0), emissao=emissao, pai=g)
    for dx in (-larg / 2 - 0.22, larg / 2 + 0.22):
        M.caixa((0.5, 0.16, alt + 0.5), (x + dx, y - 0.1, z), cortina, g)
    M.caixa((larg + 1.1, 0.2, 0.16), (x, y - 0.1, z + alt / 2 + 0.3), OURO, g)


def _estante(g, x0, x1, y, h=2.8, seed=1):
    r = random.Random(seed)
    w = x1 - x0
    M.caixa((w, 0.45, h), ((x0 + x1) / 2, y - 0.22, h / 2), MADEIRA_ESC, g)
    cores = ["#7a1f26", "#1f3d5c", "#2f5a3a", "#8a6a2a", "#3a2a4a", "#6a3a22", "#22323a", "#93302a"]
    n = int(h / 0.52)
    for k in range(n):
        z0 = 0.16 + k * 0.52
        M.caixa((w - 0.1, 0.06, 0.04), ((x0 + x1) / 2, y - 0.47, z0 - 0.02), MADEIRA, g)
        x = x0 + 0.1
        while x < x1 - 0.2:
            lw, lh = r.uniform(0.07, 0.13), r.uniform(0.3, 0.42)
            if r.random() < 0.9:
                M.caixa((lw - 0.01, 0.2, lh), (x + lw / 2, y - 0.5, z0 + lh / 2), r.choice(cores), g)
            x += lw


def relampago(quadros, pos, energia=4000):
    """Clarao azulado de raio nos quadros dados (a luz se chama Raio e nao entra no apagao)."""
    ld = bpy.data.lights.new("Raio", "POINT")
    ld.color = M.hexrgb("#cfe0ff")
    ld.shadow_soft_size = 1.0
    ob = M._link(bpy.data.objects.new("Raio", ld))
    ob.location = pos
    ld.energy = 0
    ld.keyframe_insert("energy", frame=0)
    for f in quadros:
        for df, e in ((-1, 0), (0, 1), (2, 0.15), (4, 0.8), (6, 0.3), (11, 0)):
            ld.energy = energia * e
            ld.keyframe_insert("energy", frame=max(1, int(f) + df))
    return ob


def apagao(f0, f1, resto=0.0):
    """A luz cai em f0 e volta em f1 (raios continuam funcionando)."""
    alvos = [(l, "energy", l.energy) for l in bpy.data.lights if not l.name.startswith("Raio")]
    bg = next((nd for nd in bpy.context.scene.world.node_tree.nodes if nd.type == "BACKGROUND"), None)
    if bg is not None:
        alvos.append((bg.inputs[1], "default_value", bg.inputs[1].default_value))
    for obj, prop, base in alvos:
        for f, v in ((max(0, f0 - 1), base), (f0, base * resto), (f1 - 1, base * resto), (f1, base)):
            setattr(obj, prop, v)
            obj.keyframe_insert(prop, frame=int(f))
    for d in [l for l in bpy.data.lights if not l.name.startswith("Raio")] + [bpy.context.scene.world.node_tree]:
        ad = getattr(d, "animation_data", None)
        if ad and ad.action:
            for fc in getattr(ad.action, "fcurves", []):
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"


# ------------------------------------------------------------------ primeira pessoa
OLHOS = 1.52


def pov(keys, alvo_keys, lente=22, andando=()):
    """Camera em PRIMEIRA PESSOA (os olhos do protagonista; ele nao aparece).
    keys=[(quadro, (x, y))] por onde ele anda (altura dos olhos automatica; passe (x, y, z) para abaixar/agachar);
    alvo_keys=[(quadro, (x, y, z))] para onde ele olha. andando=[(f0, f1), ...]: trechos com balanco de passo."""
    ck = [(f, (p[0], p[1], p[2] if len(p) > 2 else OLHOS)) for f, p in keys]
    cam = M.camera(ck, alvo_keys, lente=lente)
    for f0, f1 in andando:
        f0, f1 = int(f0), int(f1)
        cam.delta_location = (0, 0, 0)
        cam.keyframe_insert("delta_location", frame=max(1, f0 - 1))
        for k, f in enumerate(range(f0, f1 + 1, 8)):
            cam.delta_location = (0.02 * (1 if k % 2 else -1), 0, 0.035 if k % 2 else -0.012)
            cam.keyframe_insert("delta_location", frame=f)
        cam.delta_location = (0, 0, 0)
        cam.keyframe_insert("delta_location", frame=f1 + 8)
    return cam


def maos_com_livro(x, y, z=1.12, aberto=True):
    """As maos do protagonista segurando o livro da portaria, na parte de baixo da tela (camera em (x, y-0.45))."""
    g = M.grupo("Maos", (x, y, z))
    M.caixa((0.5, 0.36, 0.035), (0, 0, 0), "#3a2416", g, rot=(math.radians(38), 0, 0))
    M.quadro_imagem("livro.png", (0, -0.012, 0.022), 0.3, 0.4, rot=(38, 0, 0), emissao=0.08, pai=g)
    for lado in (-1, 1):
        M.caixa((0.1, 0.13, 0.1), (lado * 0.27, -0.1, -0.07), "#c98f6a", g)                 # mao
        M.caixa((0.13, 0.5, 0.13), (lado * 0.3, -0.38, -0.2), "#b2966e", g, rot=(math.radians(25), 0, 0))   # manga do sobretudo
    return g


# ------------------------------------------------------------------ gabinete
def gabinete(raios=()):
    """Gabinete do presidente: x -4..4, y -3..5. Poltrona de costas para a camera em (0, 2.3); a mao caida com o
    relogio fica do lado direito dela. Mesa encostada perto da janela (y 3.2..4.2)."""
    _inicio()
    g = M.grupo("Gabinete")
    _sala(g, -4, 4, -3, 5, 3.4, "#2f4a44", lambri=MADEIRA)
    _piso("marmore.png", -4, 4, -3, 5, 4.0, g)
    M.caixa((8.6, 0.3, 3.4), (0, -3.15, 1.7), "#2f4a44", g)                 # parede da frente (atras da camera)
    M.caixa((8.6, 0.34, 1.0), (0, -3.14, 0.5), MADEIRA, g)
    M.caixa((1.3, 0.1, 2.5), (-2.2, -2.96, 1.25), MADEIRA_ESC, g)           # porta
    M.caixa((4.6, 4.2, 0.03), (0, 2.2, 0.03), "#6e1f24", g)                 # tapete
    M.caixa((4.2, 3.8, 0.035), (0, 2.2, 0.035), "#8a2a30", g)
    _janela(g, 0, 5, 1.95, 2.2, 2.5)
    _estante(g, -3.8, -1.75, 5, seed=4)
    _estante(g, 1.75, 3.8, 5, seed=9)
    # mesa
    M.caixa((2.6, 1.0, 0.74), (0, 3.7, 0.37), MADEIRA, g)
    M.caixa((2.8, 1.15, 0.08), (0, 3.7, 0.78), MADEIRA_ESC, g)
    M.caixa((0.5, 0.36, 0.02), (0.5, 3.6, 0.83), "#efe9d8", g, rot=(0, 0, 0.2))     # papeis
    M.caixa((0.3, 0.2, 0.09), (0.95, 3.75, 0.86), "#1b1b1f", g)                     # telefone
    M.cilindro(0.09, 0.03, (-0.9, 3.7, 0.82), OURO, 12, pai=g)                      # abajur
    M.cilindro(0.02, 0.4, (-0.9, 3.7, 0.84), OURO, 8, pai=g)
    M.cilindro(0.2, 0.2, (-0.9, 3.7, 1.22), "#2f6a4a", 12, raio_topo=0.11, pai=g, material=M.mat("#3f8a5a", emissao=1.2))
    M._luz_ponto((-0.9, 3.4, 1.15), 70, "#ffd9a0", g)
    # poltrona de costas para a camera (esconde o corpo)
    couro = "#4a1418"
    M.caixa((0.86, 0.8, 0.14), (0, 2.3, 0.5), couro, g)
    M.caixa((0.8, 0.16, 1.4), (0, 1.9, 1.08), couro, g)
    for dx in (-0.42, 0.42):
        M.caixa((0.12, 0.74, 0.34), (dx, 2.3, 0.72), couro, g)
    M.cilindro(0.3, 0.06, (0, 2.3, 0.0), "#222226", 10, pai=g)
    M.cilindro(0.05, 0.42, (0, 2.3, 0.04), "#222226", 8, pai=g)
    M.caixa((0.5, 0.36, 0.62), (0, 2.38, 0.86), "#1c2440", g)                       # paleto (so um vulto)
    # o braco caido, com o relogio
    x, y = RELOGIO[0], RELOGIO[1] + 0.1
    M.caixa((0.17, 0.17, 0.46), (x, y, 0.86), "#1c2440", g)
    M.caixa((0.18, 0.18, 0.05), (x, y, 0.645), "#f2efe6", g)
    M.caixa((0.185, 0.185, 0.09), (x, y, RELOGIO[2]), "#3a2416", g)
    M.caixa((0.14, 0.15, 0.2), (x, y, 0.435), "#c98f6a", g)
    M.quadro_imagem("relogio_440.png", (x, y - 0.096, RELOGIO[2]), 0.17, 0.17, rot=(90, 0, 0), emissao=0.25, pai=g)
    # luz
    M._luz_ponto((0, 1.0, 3.0), 110, "#ffd9a0", g)
    M._luz_ponto((0.6, 0.2, 1.4), 30, "#dfe8ff", g)
    if raios:
        relampago(raios, (0.3, 4.3, 2.3), 2600)
    return g


# ------------------------------------------------------------------ corredor
def corredor(alerta=None, grade=None, porta=True):
    """Corredor de marmore: x -1.9..1.9, y -6..16; porta dupla do gabinete no fundo.
    alerta=f: luzes vermelhas piscando a partir de f. grade=(f0, f1): grade de aco desce em y=11."""
    _inicio()
    g = M.grupo("Corredor")
    _sala(g, -1.9, 1.9, -8, 16, 3.6, "#cfc6b0", chao="#2a2a2e", teto="#b9b29f", lambri=MADEIRA)
    _piso("marmore.png", -1.9, 1.9, -8, 16, 1.9, g)
    M.caixa((1.3, 24, 0.03), (0, 4, 0.03), "#7a1f26", g)                    # passadeira vermelha
    brancas = []
    for k, y in enumerate(range(-6, 16, 4)):
        for lado in (-1, 1):
            M.caixa((0.3, 0.5, 3.6), (lado * 1.82, y + 2, 1.8), "#e2dccb", g)        # pilastra
            M.caixa((0.06, 0.2, 0.36), (lado * 1.72, y, 2.25), OURO, g)              # arandela
            M.esfera(0.11, (lado * 1.66, y, 2.5), "#fff0c8", pai=g, material=M.mat("#fff0c8", emissao=5))
            if (k + (lado > 0)) % 2 == 0:
                brancas.append(M._luz_ponto((lado * 1.4, y, 2.5), 95, "#ffe2b0", g))
    for y in (-3, 5, 9):                                                           # quadros
        for lado in (-1, 1):
            M.caixa((0.05, 1.2, 0.9), (lado * 1.73, y + 2, 1.9), OURO, g)
            M.caixa((0.06, 1.0, 0.7), (lado * 1.72, y + 2, 1.9), "#2e3a34" if lado < 0 else "#3a2e2a", g)
    if porta:
        M.caixa((2.3, 0.12, 2.9), (0, 15.94, 1.45), OURO, g)
        for dx in (-0.53, 0.53):
            M.caixa((1.02, 0.1, 2.7), (dx, 15.88, 1.35), MADEIRA_ESC, g)
            M.caixa((0.7, 0.04, 0.9), (dx, 15.82, 1.95), MADEIRA, g)
            M.caixa((0.7, 0.04, 0.9), (dx, 15.82, 0.75), MADEIRA, g)
            M.esfera(0.06, (dx * 0.2, 15.78, 1.25), OURO, pai=g, material=M.mat(OURO, rug=0.3, metal=0.8))
        M._luz_ponto((0, 14.6, 2.9), 120, "#ffe2b0", g)
    M._luz_ponto((0, -4.5, 2.6), 120, "#e8ecff", g)
    if alerta is not None:
        f0 = int(alerta)
        verm = []
        for y in (0, 6, 12):
            M.caixa((0.5, 0.2, 0.14), (0, y, 3.42), "#ff2b2b", g, material=M.mat("#ff2b2b", emissao=6))
            verm.append(M._luz_ponto((0, y, 3.0), 0, "#ff2a2a", g))
        for l in brancas:
            e = l.data.energy
            for f, v in ((f0 - 1, e), (f0, e * 0.22)):
                l.data.energy = v
                l.data.keyframe_insert("energy", frame=max(0, f))
        fim = bpy.context.scene.frame_end
        for l in verm:
            l.data.keyframe_insert("energy", frame=max(0, f0 - 1))
            for k, f in enumerate(range(f0, fim + 1, 9)):
                l.data.energy = 420 if k % 2 == 0 else 60
                l.data.keyframe_insert("energy", frame=f)
    if grade:
        f0, f1 = grade
        gr = M.grupo("Grade", (0, 11, 5.6), pai=g)
        for k in range(9):
            M.caixa((0.09, 0.09, 3.6), (-1.7 + k * 0.425, 0, 0), "#5c6068", gr, material=M.mat("#5c6068", rug=0.4, metal=0.7))
        for z in (-1.7, -0.6, 0.6, 1.7):
            M.caixa((3.8, 0.12, 0.12), (0, 0, z), "#484c54", gr, material=M.mat("#484c54", rug=0.4, metal=0.7))
        M.mover(gr, [(max(1, f0), (0, 11, 5.6)), (f1, (0, 11, 1.8))])
    return g


# ------------------------------------------------------------------ sala das cameras
def sala_cameras(f_pulo=None):
    """Sala de seguranca: x -3.2..3.2, y -3..3. Parede de 12 monitores em y=3."""
    _inicio()
    g = M.grupo("Cameras")
    _sala(g, -3.2, 3.2, -3, 3, 3.0, "#23272e", rodape="#15171c", chao="#1c1e24", teto="#15171c")
    M.caixa((6.2, 0.1, 2.9), (0, 2.96, 1.75), "#0e0f13", g)
    n = 0
    for lin in range(3):
        for col in range(4):
            x, z = -2.25 + col * 1.5, 2.65 - lin * 0.9
            M.caixa((1.42, 0.08, 0.84), (x, 2.93, z), "#1b1c22", g)
            k = (n * 3 + lin) % 4
            a = M.quadro_imagem(f"cam{k}_0210.png", (x, 2.885, z), 1.32, 0.76, emissao=1.5, pai=g)
            if f_pulo:
                b = M.quadro_imagem(f"cam{k}_0217.png", (x, 2.884, z), 1.32, 0.76, emissao=1.7, pai=g)
                r = M.quadro_imagem("cam_ruido.png", (x, 2.88, z), 1.32, 0.76, emissao=2.2, pai=g)
                M._escala_keys(a, [(f_pulo - 5, 1), (f_pulo - 4, 0.0001)])
                M._escala_keys(r, [(f_pulo - 5, 0.0001), (f_pulo - 4, 1), (f_pulo, 1), (f_pulo + 1, 0.0001)])
                M._escala_keys(b, [(f_pulo, 0.0001), (f_pulo + 1, 1)])
            n += 1
    # mesa de controle
    M.caixa((5.4, 0.9, 0.72), (0, 1.9, 0.36), "#2b2e36", g)
    M.caixa((5.6, 1.0, 0.06), (0, 1.9, 0.75), "#3a3e48", g)
    r = random.Random(5)
    for k in range(34):
        cor = r.choice(["#35ff5a", "#ff3a2a", "#ffd23a", "#3aa0ff", "#8a8f99"])
        M.caixa((0.07, 0.07, 0.03), (-2.5 + (k % 17) * 0.31, 1.75 + (k // 17) * 0.25, 0.795), cor, g,
                material=M.mat(cor, emissao=3))
    M._luz_ponto((0, 1.2, 1.9), 70, "#bcd4ff", g)
    M._luz_ponto((0, -1.5, 2.4), 45, "#9fb4e8", g)
    return g


# ------------------------------------------------------------------ salao
def salao(raios=()):
    """Salao: x -6.5..6.5, y -4..8, pe-direito 5. Os suspeitos ficam em arco em y=5 (ver P.suspeitos)."""
    _inicio()
    g = M.grupo("Salao")
    _sala(g, -6.5, 6.5, -4, 8, 5.0, "#6a4a52", lambri=MADEIRA, chao="#3a2a20", teto="#3a3030")
    _piso("marmore.png", -6.5, 6.5, -4, 8, 3.0, g)
    M.caixa((10, 6.5, 0.03), (0, 3.2, 0.03), "#6e1f24", g)
    M.caixa((9.4, 5.9, 0.035), (0, 3.2, 0.035), "#8a2a30", g)
    for x in (-4.2, 0, 4.2):
        _janela(g, x, 8, 2.6, 1.9, 3.2)
    # lustre
    M.cilindro(0.03, 1.1, (0, 3.0, 3.9), OURO, 6, pai=g)
    M.cilindro(0.75, 0.1, (0, 3.0, 3.8), OURO, 14, pai=g)
    for k in range(8):
        a = k * math.pi / 4
        M.esfera(0.1, (math.cos(a) * 0.7, 3.0 + math.sin(a) * 0.7, 3.98), "#fff0c8", pai=g, material=M.mat("#fff0c8", emissao=7))
    M._luz_ponto((0, 3.0, 3.5), 520, "#ffe2b0", g)
    M._luz_ponto((0, -1.5, 2.6), 170, "#ffe9c8", g)
    # sofas e relogio de parede
    for lado in (-1, 1):
        M.caixa((0.9, 2.6, 0.45), (lado * 5.7, 5.2, 0.3), "#3d2a4a", g)
        M.caixa((0.25, 2.6, 0.9), (lado * 6.1, 5.2, 0.75), "#3d2a4a", g)
    M.caixa((0.6, 0.4, 2.3), (2.1, 7.75, 1.15), MADEIRA_ESC, g)
    M.cilindro(0.24, 0.05, (2.1, 7.53, 1.85), "#f2efe6", 16, pai=g, rot=(math.pi / 2, 0, 0))
    M.caixa((0.03, 0.02, 0.18), (2.1, 7.46, 1.92), "#111111", g)
    M.caixa((0.14, 0.02, 0.03), (2.16, 7.46, 1.85), "#111111", g)
    if raios:
        relampago(raios, (0, 6.8, 3.2), 9000)
    return g


def suspeitos(F, some=None, olhar=0):
    """Os seis suspeitos em pe, de frente para a camera. some=(tipo, quadro): esse some no quadro dado.
    Devolve {tipo: boneco}."""
    d = {}
    for tipo, x in SUSPEITOS:
        b = M.Boneco(tipo, (x, Y_SUSPEITOS - abs(x) * 0.12), olhar=olhar + x * -4)
        b.parado(1, F, "parado")
        if some and some[0] == tipo:
            f = int(some[1])
            b.root.location.z = 0
            b.root.keyframe_insert("location", frame=f - 1)
            b.root.location.z = -30
            b.root.keyframe_insert("location", frame=f)
            for fc in getattr(b.root.animation_data.action, "fcurves", []):
                if fc.data_path == "location":
                    for kp in fc.keyframe_points:
                        kp.interpolation = "CONSTANT"
            # o cracha dela fica caido no tapete
            cr = M.caixa((0.24, 0.34, 0.02), (x + 0.1, Y_SUSPEITOS - abs(x) * 0.12 - 0.15, 0.06), "#f2efe6", rot=(0, 0, 0.5))
            M.caixa((0.16, 0.1, 0.022), (x + 0.1, Y_SUSPEITOS - abs(x) * 0.12 - 0.15, 0.062), "#2a6fdb", rot=(0, 0, 0.5))
            M._escala_keys(cr, [(f - 1, 0.0001), (f, 1)])
        d[tipo] = b
    return d


# ------------------------------------------------------------------ portaria
def portaria():
    """Portaria do palacio: x -4..4, y -3..4.5. Balcao em y 1.0..1.8; o livro de entradas fica em P.LIVRO
    (a ultima linha, com a assinatura, em P.LINHA). Quem chega fica em (0, 0.45) olhando para +Y."""
    _inicio()
    g = M.grupo("Portaria")
    _sala(g, -4, 4, -3, 4.5, 3.2, "#b9b29f", lambri=MADEIRA, chao="#2a2a2e", teto="#8f8a7c")
    _piso("marmore.png", -4, 4, -3, 4.5, 2.6, g)
    M.caixa((5.4, 0.8, 1.0), (0, 1.4, 0.5), MADEIRA, g)
    M.caixa((5.6, 0.95, 0.07), (0, 1.4, 1.035), MADEIRA_ESC, g)
    M.caixa((0.7, 0.9, 0.03), (LIVRO[0], LIVRO[1], 1.085), "#3a2416", g)
    M.quadro_imagem("livro.png", (LIVRO[0], LIVRO[1], LIVRO[2] + 0.004), 0.62, 0.82, rot=(0, 0, 0), emissao=0.1, pai=g)
    M.cilindro(0.012, 0.16, (0.45, 1.3, 1.08), "#1a2a6a", 6, pai=g, rot=(math.pi / 2, 0, 0.5))      # caneta
    # abajur de balcao iluminando o livro
    M.cilindro(0.08, 0.03, (-0.75, 1.55, 1.07), OURO, 10, pai=g)
    M.cilindro(0.015, 0.42, (-0.75, 1.55, 1.09), OURO, 6, pai=g)
    M.caixa((0.5, 0.14, 0.08), (-0.55, 1.5, 1.52), "#2f6a4a", g, material=M.mat("#3f8a5a", emissao=1.0))
    M._luz_ponto((-0.3, 1.4, 1.42), 14, "#ffe2b0", g)
    # quadro de chaves e relogio na parede do fundo
    M.caixa((1.8, 0.06, 1.1), (-1.8, 4.44, 1.9), MADEIRA_ESC, g)
    for i in range(6):
        for j in range(3):
            M.caixa((0.05, 0.03, 0.14), (-2.5 + i * 0.28, 4.39, 2.25 - j * 0.33), OURO, g)
    M.cilindro(0.32, 0.05, (1.6, 4.42, 2.3), "#f2efe6", 18, pai=g, rot=(math.pi / 2, 0, 0))
    M.caixa((0.03, 0.02, 0.22), (1.6, 4.36, 2.38), "#111111", g)
    M.caixa((0.18, 0.02, 0.03), (1.67, 4.36, 2.3), "#111111", g)
    _janela(g, 3.0, 4.5, 1.9, 1.3, 1.7, emissao=0.7)
    M._luz_ponto((0, 0.5, 2.9), 170, "#ffe9c8", g)
    M._luz_ponto((0, -2.2, 2.4), 80, "#e8ecff", g)
    return g


# ------------------------------------------------------------------ patio (externo, chuva)
def chuva3d(area=(-7, 7, -14, 12), n=240, altura=9.0, seed=2):
    """Riscos de chuva caindo em loop dentro de area=(x0, x1, y0, y1). Ficam fora do contorno preto."""
    r = random.Random(seed)
    sc = bpy.context.scene
    col = bpy.data.collections.new("Chuva")
    sc.collection.children.link(col)
    m = M.mat("#b8c8ea", emissao=0.9)
    for _ in range(n):
        x, y = r.uniform(area[0], area[1]), r.uniform(area[2], area[3])
        ob = M.caixa((0.022, 0.022, r.uniform(0.5, 0.9)), (x, y, altura), "#b8c8ea", nome="Gota", material=m)
        col.objects.link(ob)
        sc.collection.objects.unlink(ob)
        per, fase = r.choice([13, 15, 17]), r.randrange(0, 17)
        ob.keyframe_insert("location", frame=1 - fase)
        ob.location.z = -0.5
        ob.location.x = x - 0.5
        ob.keyframe_insert("location", frame=1 - fase + per)
        for fc in getattr(ob.animation_data.action, "fcurves", []):
            fc.modifiers.new("CYCLES")
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
    for ls in bpy.context.view_layer.freestyle_settings.linesets:
        ls.select_by_collection = True
        ls.collection = col
        ls.collection_negation = "EXCLUSIVE"


def patio(f_abre=30, raios=()):
    """Entrada do palacio a noite: muro e portao blindado em y=0 (abre em f_abre), patio ate a fachada em y=26."""
    _inicio(interior=False)
    M.ceu("#05070f", 0.5, "#151b30")
    M.chao("#23262d")
    M.luz_sol(0.55, "#8ea6ff", 42, 20)
    bpy.data.objects["Fill"].data.energy = 0.3
    M.contorno()
    g = M.grupo("Patio")
    M.caixa((6.4, 44, 0.04), (0, 6, 0.02), "#3b3f47", g)                      # caminho
    for lado in (-1, 1):                                                      # muro
        M.caixa((30, 0.7, 4.2), (lado * 18.2, 0, 2.1), "#4a4d55", g)
        M.caixa((30, 0.9, 0.3), (lado * 18.2, 0, 4.35), "#33363d", g)
        M.caixa((0.9, 0.9, 5.0), (lado * 3.5, 0, 2.5), "#33363d", g)
        M.esfera(0.2, (lado * 3.5, -0.3, 4.4), "#ffd9a0", pai=g, material=M.mat("#ffd9a0", emissao=6))
        M._luz_ponto((lado * 3.2, -1.2, 4.2), 500, "#ffd9a0", g)
        folha = M.grupo("Folha", (lado * 1.52, 0, 0), pai=g)                  # portao blindado, corre para o lado
        M.caixa((3.04, 0.25, 3.9), (0, 0, 1.95), "#5c6068", folha, material=M.mat("#5c6068", rug=0.45, metal=0.6))
        for z in (0.6, 1.5, 2.4, 3.3):
            M.caixa((3.04, 0.3, 0.12), (0, 0, z), "#3d4047", folha)
        M.mover(folha, [(1, (lado * 1.52, 0, 0)), (max(2, f_abre), (lado * 1.52, 0, 0)), (f_abre + 55, (lado * 4.75, 0, 0))])
    M.caixa((2.2, 2.2, 2.8), (6.0, -2.4, 1.4), "#4a4d55", g)                  # guarita
    M.caixa((1.4, 0.06, 0.9), (6.0, -3.52, 1.7), "#ffe2a0", g, material=M.mat("#ffe2a0", emissao=3))
    # fachada do palacio
    M.caixa((46, 6, 13), (0, 30, 6.5), "#cfc6b0", g)
    M.caixa((48, 7, 0.8), (0, 30, 13.2), "#b9b29f", g)
    M.caixa((16, 3, 0.5), (0, 26.2, 0.25), "#b9b29f", g)
    M.caixa((17, 3.6, 1.2), (0, 26.4, 10.6), "#b9b29f", g)
    for x in (-7, -4.2, -1.5, 1.5, 4.2, 7):
        M.cilindro(0.5, 9.6, (x, 25.6, 0.5), "#e8e2d2", 12, pai=g)
    M.caixa((2.6, 0.2, 4.4), (0, 26.95, 2.7), MADEIRA_ESC, g)
    jan = M.mat("#ffd98a", emissao=2.4)
    apag = M.mat("#1a2238", emissao=0.0)
    r = random.Random(6)
    for z in (3.2, 8.0):
        for x in range(-20, 21, 4):
            if abs(x) < 3 and z < 5:
                continue
            M.caixa((1.7, 0.1, 2.6), (x, 26.95, z), "#ffd98a", g, material=jan if r.random() < 0.7 else apag)
    for lado in (-1, 1):
        for y in (8, 17):
            M.cilindro(0.09, 4.2, (lado * 4.3, y, 0), "#22242a", 8, pai=g)
            M.esfera(0.24, (lado * 4.3, y, 4.3), "#ffe2b0", pai=g, material=M.mat("#ffe2b0", emissao=6))
            M._luz_ponto((lado * 4.0, y, 4.0), 700, "#ffd9a0", g)
    M._luz_ponto((0, 22, 6), 2500, "#ffe2b0", g)
    M._luz_ponto((0, -6, 3.5), 260, "#cfe0ff", g)
    chuva3d()
    if raios:
        relampago(raios, (-6, 12, 14), 60000)
    return g
