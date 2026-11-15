"""
Biblioteca 3D low-poly para o Blender (roda DENTRO do Blender).

Convencoes: metros; chao em z=0; X para a direita; Y para o fundo (a camera
padrao fica em -Y olhando para +Y). Boneco tem ~1,9 m. Quadros a 30 fps.
Todas as pecas devolvem um "grupo" (objeto vazio) que pode ser animado com
surgir(), sumir(), mover(), girar() e etiquetado com rotulo().
"""

import glob
import math
import os
import random

import bmesh
import bpy
from mathutils import Vector

FPS = 30
ROTULOS = []      # (alvo, texto, f0, f1, dz)
_mats = {}
_rng = random.Random(1)


# ================================================================== base
def hexrgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c)


def mat(cor, rug=0.85, emissao=0.0, metal=0.0):
    key = (cor, rug, emissao, metal)
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new(f"m{len(_mats)}")
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    rgb = hexrgb(cor)
    p.inputs["Base Color"].default_value = (*rgb, 1)
    p.inputs["Roughness"].default_value = rug
    p.inputs["Metallic"].default_value = metal
    for nome_spec in ("Specular IOR Level", "Specular"):
        if nome_spec in p.inputs:
            p.inputs[nome_spec].default_value = 0.15 if rug > 0.5 else 0.5
            break
    if emissao:
        p.inputs["Emission Color"].default_value = (*rgb, 1)
        p.inputs["Emission Strength"].default_value = emissao
    _mats[key] = m
    return m


def _link(ob):
    bpy.context.scene.collection.objects.link(ob)
    return ob


def grupo(nome="Grupo", pos=(0, 0, 0), rot=0.0, pai=None):
    """Objeto vazio que agrupa pecas. pos=(x,y) ou (x,y,z); rot em graus (em volta de Z)."""
    ob = _link(bpy.data.objects.new(nome, None))
    ob.location = (pos[0], pos[1], pos[2] if len(pos) > 2 else 0)
    ob.rotation_euler = (0, 0, math.radians(rot))
    if pai:
        ob.parent = pai
    return ob


def _malha(nome, bm, cor, pai, pos, rot, material=None):
    me = bpy.data.meshes.new(nome)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material or mat(cor))
    ob = _link(bpy.data.objects.new(nome, me))
    ob.location = pos
    ob.rotation_euler = rot
    if pai:
        ob.parent = pai
    return ob


def caixa(dims, pos=(0, 0, 0), cor="#888888", pai=None, offset=(0, 0, 0), rot=(0, 0, 0), nome="Caixa", material=None):
    """Caixa com tamanho dims=(x,y,z). pos e o centro (mais offset para mudar o pivo)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * dims[0] + offset[0], v.co.y * dims[1] + offset[1], v.co.z * dims[2] + offset[2]))
    return _malha(nome, bm, cor, pai, pos, rot, material)


def cilindro(raio, altura, pos=(0, 0, 0), cor="#888888", lados=10, raio_topo=None, pai=None, rot=(0, 0, 0), material=None):
    """Cilindro/cone com a base em pos (cresce para cima)."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=lados, radius1=raio,
                          radius2=raio if raio_topo is None else raio_topo, depth=altura)
    for v in bm.verts:
        v.co.z += altura / 2
    return _malha("Cil", bm, cor, pai, pos, rot, material)


def esfera(raio, pos=(0, 0, 0), cor="#888888", sub=1, pai=None, material=None):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=raio)
    return _malha("Esf", bm, cor, pai, pos, (0, 0, 0), material)


# ================================================================== cena
def nova_cena(frames=150, largura=1080, altura=1920):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _mats.clear()
    ROTULOS.clear()
    sc = bpy.context.scene
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            sc.render.engine = eng
            break
        except TypeError:
            continue
    sc.render.resolution_x, sc.render.resolution_y = largura, altura
    sc.render.resolution_percentage = 100
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, frames
    for attr, val in (("taa_render_samples", 24), ("use_gtao", True), ("use_shadows", True)):
        try:
            setattr(sc.eevee, attr, val)
        except AttributeError:
            pass
    sc.view_settings.view_transform = "Standard"
    w = bpy.data.worlds.new("Mundo")
    sc.world = w
    w.use_nodes = True
    sol = bpy.data.lights.new("Sol", "SUN")
    sol.angle = math.radians(3)
    o = _link(bpy.data.objects.new("Sol", sol))
    o.rotation_euler = (math.radians(50), math.radians(10), math.radians(35))
    ceu("#5fa8e8", 1.0)
    sol.energy = 3.2
    # luz de preenchimento (sem sombra) para as sombras nao ficarem pretas
    fill = bpy.data.lights.new("Fill", "SUN")
    fill.energy = 0.9
    fill.color = hexrgb("#cfe0ff")
    try:
        fill.use_shadow = False
    except AttributeError:
        pass
    fo = _link(bpy.data.objects.new("Fill", fill))
    fo.rotation_euler = (math.radians(60), 0, math.radians(215))
    return sc


def ceu(cor="#87c8f5", forca=1.0, horizonte=None):
    """Ceu em degrade: 'cor' no alto, 'horizonte' (mais claro) perto do chao."""
    w = bpy.context.scene.world
    nt = w.node_tree
    for n in list(nt.nodes):
        if n.type not in ("OUTPUT_WORLD",):
            nt.nodes.remove(n)
    out = [n for n in nt.nodes if n.type == "OUTPUT_WORLD"][0]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -0.05
    mr.inputs["From Max"].default_value = 0.55
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    topo = hexrgb(cor)
    hz = hexrgb(horizonte) if horizonte else tuple(min(1.0, c * 0.45 + 0.55) for c in topo)
    ramp.color_ramp.elements[0].color = (*hz, 1)
    ramp.color_ramp.elements[1].color = (*topo, 1)
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs[1].default_value = forca
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs[0], out.inputs[0])


def mat_ruido(cor1, cor2, escala=0.08, rug=0.95):
    """Material com variacao de cor (chao de grama/terra/areia mais natural)."""
    key = ("ruido", cor1, cor2, escala)
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new(f"r{len(_mats)}")
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    p.inputs["Roughness"].default_value = rug
    for nome_spec in ("Specular IOR Level", "Specular"):
        if nome_spec in p.inputs:
            p.inputs[nome_spec].default_value = 0.1
            break
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = escala
    nz.inputs["Detail"].default_value = 3
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[1].position = 0.65
    ramp.color_ramp.elements[0].color = (*hexrgb(cor1), 1)
    ramp.color_ramp.elements[1].color = (*hexrgb(cor2), 1)
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], p.inputs["Base Color"])
    _mats[key] = m
    return m


def _clarear(cor, f=0.88):
    c = [int(cor.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{max(0, min(255, int(v * f))):02x}" for v in c)


def luz_sol(energia=3.2, cor="#ffffff", inclinacao=50, direcao=35):
    s = bpy.data.objects["Sol"]
    s.data.energy = energia
    s.data.color = hexrgb(cor)
    s.rotation_euler = (math.radians(inclinacao), math.radians(10), math.radians(direcao))


def chao(cor="#78c25a", tam=4000):
    return caixa((tam, tam, 0.2), (0, 0, -0.1), cor, nome="Chao", material=mat_ruido(cor, _clarear(cor, 0.84), 0.06))


def ambiente(tipo="campo", decoracao=True):
    """campo | deserto | neve | cidade | praia | noite | subsolo | vazio"""
    r = _rng
    if tipo == "deserto":
        ceu("#6fb0e8", 1.0, "#f6dfb0"); chao("#e2bf7d"); luz_sol(3.6, "#fff1d6")
        if decoracao:
            for _ in range(40):
                a, d = r.uniform(0, 6.28), r.uniform(45, 160)
                cacto(math.cos(a) * d, math.sin(a) * d)
    elif tipo == "neve":
        ceu("#8fb6d8", 1.0, "#eef5fa"); chao("#f4f8fb"); luz_sol(2.6, "#eaf3ff")
        if decoracao:
            for _ in range(70):
                a, d = r.uniform(0, 6.28), r.uniform(40, 150)
                pinheiro(math.cos(a) * d, math.sin(a) * d, r.uniform(0.8, 1.5), neve=True)
    elif tipo == "cidade":
        ceu("#5d9fdc", 1.0, "#d6e8f5"); chao("#8c8f94"); luz_sol(3.0)
        if decoracao:
            kpred = [f"building-{c}" for c in "abcdefghijklmn"] + [f"building-skyscraper-{c}" for c in "abcde"]
            kpred = [n for n in kpred if tem_modelo(n)]
            for _ in range(55):
                a, d = r.uniform(0, 6.28), r.uniform(45, 150)
                x, y = math.cos(a) * d, math.sin(a) * d
                if kpred:
                    modelo(r.choice(kpred), x, y, r.choice([0, 90, 180, 270]), r.uniform(0.9, 1.3))
                else:
                    predio(x, y, r.uniform(8, 16), r.uniform(8, 16), r.uniform(10, 45))
    elif tipo == "cidade_noite":
        ceu("#0a1028", 1.3, "#2b3868"); chao("#3a3e4a"); luz_sol(1.1, "#8ea6ff", 35)
        if decoracao:
            kpred = [f"building-{c}" for c in "abcdefghijklmn"] + [f"building-skyscraper-{c}" for c in "abcde"]
            kpred = [n for n in kpred if tem_modelo(n)]
            for _ in range(55):
                a, d = r.uniform(0, 6.28), r.uniform(45, 150)
                x, y = math.cos(a) * d, math.sin(a) * d
                if kpred:
                    modelo(r.choice(kpred), x, y, r.choice([0, 90, 180, 270]), r.uniform(0.9, 1.3))
                else:
                    predio(x, y, r.uniform(8, 16), r.uniform(8, 16), r.uniform(10, 45))
            # postes acesos com luz quente de verdade perto do centro
            for px, py in ((-12, -8), (12, -8), (-12, 14), (12, 14)):
                poste(px, py, 0 if px < 0 else 180, ligado=True)
                ld = bpy.data.lights.new("PosteLuz", "POINT")
                ld.energy = 900
                ld.color = hexrgb("#ffc27a")
                lo = _link(bpy.data.objects.new("PosteLuz", ld))
                lo.location = (px + (1.3 if px < 0 else -1.3), py, 5.6)
    elif tipo == "praia":
        ceu("#3f9ee8", 1.0, "#d8f0fb"); chao("#ecd59b"); luz_sol(3.4)
        caixa((4000, 2000, 0.1), (0, 1000 + 30, 0.02), "#2f8fd8", material=mat("#2f8fd8", rug=0.15), nome="Mar")
    elif tipo == "noite":
        ceu("#1d2b5c", 1.5, "#5a6fae"); chao("#3f6b3a"); luz_sol(2.0, "#a9bcff", 45)
        if decoracao:
            floresta(50, 150, 60)
    elif tipo == "subsolo":
        ceu("#5fa8e8"); luz_sol(3.0, inclinacao=40, direcao=10)
        caixa((4000, 2000, 0.4), (0, 1000, -0.2), "#78c25a", nome="Grama")
        for z0, z1, cor in ((-0.4, -3, "#8a5a32"), (-3, -7, "#714626"), (-7, -14, "#5b371d"), (-14, -30, "#4a4a4a")):
            caixa((4000, 2000, z0 - z1), (0, 1000, (z0 + z1) / 2), cor, nome="Camada")
        for _ in range(60):
            esfera(r.uniform(0.2, 0.6), (r.uniform(-60, 60), -0.05, r.uniform(-25, -1)), "#9b9b9b", sub=0)
    elif tipo == "interior":
        ceu("#04050a", 0.25, "#0a0c14"); luz_sol(0.0)
        bpy.data.objects["Fill"].data.energy = 0.12
        contorno()
    elif tipo == "vazio":
        ceu("#5fa8e8"); chao("#78c25a")
    else:  # campo
        ceu("#5fa8e8"); chao("#78c25a"); luz_sol(3.2)
        if decoracao:
            floresta(40, 140, 70)


# ================================================================== natureza
ARVORES_K = ["tree_default", "tree_oak", "tree_fat", "tree_detailed", "tree_tall", "tree_cone"]


def arvore(x, y, s=1.0):
    opcoes = [n for n in ARVORES_K if tem_modelo(n)]
    if opcoes:
        return modelo(_rng.choice(opcoes), x, y, _rng.uniform(0, 360), s)
    g = grupo("Arvore", (x, y))
    cilindro(0.18 * s, 1.2 * s, (0, 0, 0), "#7a4a24", 6, pai=g)
    esfera(1.0 * s, (0, 0, 1.9 * s), _rng.choice(["#3f9e4a", "#4caf50", "#378a3f"]), pai=g)
    return g


def pinheiro(x, y, s=1.0, neve=False):
    g = grupo("Pinheiro", (x, y))
    cilindro(0.15 * s, 0.8 * s, (0, 0, 0), "#6b4325", 6, pai=g)
    for i, (r0, h) in enumerate(((1.2, 1.6), (0.9, 1.4), (0.6, 1.2))):
        cilindro(r0 * s, h * s, (0, 0, (0.7 + i * 0.9) * s), "#e9f1f5" if neve and i == 2 else "#2e6b3a", 7, raio_topo=0.0, pai=g)
    return g


def cacto(x, y, s=1.0):
    g = grupo("Cacto", (x, y))
    cilindro(0.3 * s, 2.4 * s, (0, 0, 0), "#4f8f3a", 8, pai=g)
    cilindro(0.2 * s, 0.9 * s, (0.5 * s, 0, 1.0 * s), "#4f8f3a", 8, pai=g)
    return g


def floresta(raio_min=35, raio_max=120, n=60, tipo="arvore"):
    for _ in range(n):
        a, d = _rng.uniform(0, 6.28), _rng.uniform(raio_min, raio_max)
        (pinheiro if tipo == "pinheiro" else arvore)(math.cos(a) * d, math.sin(a) * d, _rng.uniform(0.8, 1.5))


def montanha(x, y, raio=30, altura=25, neve=True):
    g = grupo("Montanha", (x, y))
    cilindro(raio, altura, (0, 0, 0), "#7b7d80", 7, raio_topo=0.0, pai=g)
    if neve:
        cilindro(raio * 0.32, altura * 0.32, (0, 0, altura * 0.68), "#f4f8fb", 7, raio_topo=0.0, pai=g)
    return g


def rio(x, y, comp=200, largura=12, rot=0):
    g = grupo("Rio", (x, y), rot)
    caixa((comp, largura, 0.1), (0, 0, 0.03), "#2f8fd8", pai=g, material=mat("#2f8fd8", rug=0.15))
    return g


def lago(x, y, raio=15):
    g = grupo("Lago", (x, y))
    cilindro(raio, 0.08, (0, 0, 0.0), "#2f8fd8", 16, pai=g, material=mat("#2f8fd8", rug=0.15))
    return g


# ================================================================== construcoes
def cerca_reta(x, y, comp=20, rot=0, altura=2.6):
    g = grupo("Cerca", (x, y), rot)
    n = max(1, int(comp / 2.5))
    for i in range(n + 1):
        caixa((0.12, 0.12, altura), (-comp / 2 + comp * i / n, 0, altura / 2), "#5b5f66", g)
    for h in (0.3, 1.0, 1.7, 2.4):
        caixa((comp, 0.04, 0.04), (0, 0, h), "#8a8f96", g)
    for i in range(int(comp / 0.5)):
        caixa((0.02, 0.02, altura - 0.2), (-comp / 2 + i * 0.5, 0, altura / 2), "#9aa0a6", g)
    return g


def arame_farpado(x, y, comp=20, rot=0, z=2.7):
    g = grupo("Arame", (x, y, z), rot)
    n = int(comp / 0.6)
    for i in range(n):
        cilindro(0.28, 0.05, (-comp / 2 + i * 0.6, 0, 0), "#b0b4b8", 8, pai=g, rot=(0, math.pi / 2, 0))
    return g


def cerca_quadrada(x, y, lado=36, altura=2.6, farpado=False):
    g = grupo("CercaQ", (x, y))
    h = lado / 2
    for (cx, cy, r) in ((0, -h, 0), (h, 0, 90), (0, h, 0), (-h, 0, 90)):
        c = cerca_reta(cx, cy, lado, r, altura)
        c.parent = g
        if farpado:
            a = arame_farpado(cx, cy, lado, r, altura + 0.1)
            a.parent = g
    return g


def muro_reto(x, y, comp=20, rot=0, altura=5.0, esp=0.8, cor="#bdbdbd"):
    g = grupo("Muro", (x, y), rot)
    caixa((comp, esp, altura), (0, 0, altura / 2), cor, g)
    caixa((comp, esp + 0.2, 0.25), (0, 0, altura + 0.12), "#a6a6a6", g)
    return g


def muro_quadrado(x, y, lado=46, altura=5.0, cor="#bdbdbd"):
    g = grupo("MuroQ", (x, y))
    h = lado / 2
    for (cx, cy, r) in ((0, -h, 0), (h, 0, 90), (0, h, 0), (-h, 0, 90)):
        m = muro_reto(cx, cy, lado + 0.8, r, altura, cor=cor)
        m.parent = g
    return g


def guarita(x, y, altura=7.0, holofote=True):
    g = grupo("Guarita", (x, y))
    for dx in (-1.1, 1.1):
        for dy in (-1.1, 1.1):
            caixa((0.25, 0.25, altura), (dx, dy, altura / 2), "#6d6f73", g)
    caixa((3.2, 3.2, 0.3), (0, 0, altura), "#7c7f84", g)
    caixa((2.8, 2.8, 1.8), (0, 0, altura + 1.05), "#d9d9d9", g)
    for dx, dy, w, d in ((0, -1.41, 2.2, 0.05), (0, 1.41, 2.2, 0.05), (-1.41, 0, 0.05, 2.2), (1.41, 0, 0.05, 2.2)):
        caixa((w, d, 0.8), (dx, dy, altura + 1.3), "#2b3440", g)
    caixa((3.6, 3.6, 0.3), (0, 0, altura + 2.1), "#3c4148", g)
    if holofote:
        cilindro(0.3, 0.5, (1.5, -1.5, altura + 2.3), "#fff3a0", 8, pai=g, material=mat("#fff3a0", emissao=4.0))
    return g


def portao(x, y, largura=6, rot=0, altura=4):
    g = grupo("Portao", (x, y), rot)
    for dx in (-largura / 2 - 0.4, largura / 2 + 0.4):
        caixa((0.8, 0.8, altura + 1), (dx, 0, (altura + 1) / 2), "#6d6f73", g)
    for i in range(int(largura / 0.4)):
        caixa((0.08, 0.08, altura), (-largura / 2 + 0.2 + i * 0.4, 0, altura / 2), "#3c4148", g)
    caixa((largura, 0.12, 0.15), (0, 0, altura - 0.2), "#3c4148", g)
    return g


def predio(x, y, w=12, d=10, h=20, cor=None, rot=0):
    cor = cor or _rng.choice(["#c9c2b8", "#b8c4cc", "#d8cfc0", "#a9b3bd", "#c7b8a6"])
    g = grupo("Predio", (x, y), rot)
    caixa((w, d, h), (0, 0, h / 2), cor, g)
    for zz in range(1, int(h / 3)):
        for xx in range(int(w / 2.4)):
            caixa((1.0, 0.05, 1.3), (-w / 2 + 1.4 + xx * 2.4, -d / 2 - 0.03, zz * 3), "#3b4a5c", g)
    return g


def casa(x, y, cor="#f2d8a7", telhado="#c0392b", rot=0, s=1.0):
    g = grupo("Casa", (x, y), rot)
    caixa((6 * s, 5 * s, 3.2 * s), (0, 0, 1.6 * s), cor, g)
    tel = caixa((6.6 * s, 3.8 * s, 3.8 * s), (0, 0, 3.2 * s), telhado, g, rot=(math.radians(45), 0, 0))
    tel.scale = (1, 1, 0.55)
    caixa((1.2 * s, 0.1, 2 * s), (0, -2.5 * s, 1 * s), "#6b4325", g)
    for dx in (-1.9, 1.9):
        caixa((1.1 * s, 0.1, 1 * s), (dx * s, -2.5 * s, 1.9 * s), "#6fa9d6", g)
    return g


def cela(x, y, rot=0):
    """Cela vista de frente: grade na frente (-Y), cama e privada dentro."""
    g = grupo("Cela", (x, y), rot)
    caixa((5, 0.3, 3.2), (0, 2.5, 1.6), "#9e9e9e", g)
    caixa((0.3, 5, 3.2), (-2.5, 0, 1.6), "#a8a8a8", g)
    caixa((0.3, 5, 3.2), (2.5, 0, 1.6), "#a8a8a8", g)
    caixa((5.3, 5.3, 0.3), (0, 0, 3.35), "#8e8e8e", g)
    caixa((5, 5, 0.1), (0, 0, 0.05), "#7d7d7d", g)
    caixa((2.2, 1.0, 0.5), (-1.2, 1.7, 0.4), "#e8e8e8", g)
    caixa((0.6, 0.6, 0.6), (1.8, 1.9, 0.3), "#f0f0f0", g)
    for i in range(13):
        cilindro(0.04, 3.2, (-2.4 + i * 0.4, -2.5, 0), "#4a4f57", 6, pai=g)
    caixa((5, 0.1, 0.12), (0, -2.5, 1.6), "#4a4f57", g)
    return g


def ponte(x, y, comp=30, rot=0, largura=6):
    g = grupo("Ponte", (x, y), rot)
    caixa((comp, largura, 0.6), (0, 0, 2.2), "#9a9a9a", g)
    for dx in (-comp / 3, comp / 3):
        caixa((1.2, largura, 2.2), (dx, 0, 1.1), "#8a8a8a", g)
    for dy in (-largura / 2, largura / 2):
        caixa((comp, 0.2, 0.9), (0, dy, 2.9), "#6d6f73", g)
    return g


def torre(x, y, altura=30, cor="#d9534f"):
    g = grupo("Torre", (x, y))
    for dx in (-1.5, 1.5):
        for dy in (-1.5, 1.5):
            cilindro(0.12, altura, (dx, dy, 0), cor, 6, pai=g, raio_topo=0.05)
    for z in range(3, int(altura), 4):
        caixa((3, 0.1, 0.1), (0, -1.5, z), cor, g)
        caixa((0.1, 3, 0.1), (1.5, 0, z), cor, g)
    esfera(0.5, (0, 0, altura), "#ff3b30", pai=g, material=mat("#ff3b30", emissao=5))
    return g


def bunker(x, y, rot=0):
    g = grupo("Bunker", (x, y), rot)
    caixa((10, 8, 3), (0, 0, 1.0), "#8b8f7a", g)
    caixa((3, 0.2, 2), (0, -4, 1), "#3c4148", g)
    caixa((10.6, 8.6, 0.6), (0, 0, 2.6), "#7a7e6a", g)
    return g


def piramide(x, y, lado=30):
    g = grupo("Piramide", (x, y))
    cilindro(lado * 0.7, lado * 0.65, (0, 0, 0), "#d9b26f", 4, raio_topo=0.0, pai=g, rot=(0, 0, math.radians(45)))
    return g


def fosso(x, y, comp=40, largura=5, rot=0):
    g = grupo("Fosso", (x, y), rot)
    caixa((comp, largura, 0.12), (0, 0, 0.02), "#1d3b2a", g, material=mat("#2c5d77", rug=0.2))
    return g


def minas(x, y, area=20, n=25):
    g = grupo("Minas", (x, y))
    for _ in range(n):
        cilindro(0.3, 0.12, (_rng.uniform(-area / 2, area / 2), _rng.uniform(-area / 2, area / 2), 0), "#4a4a3a", 8, pai=g)
    return g


def holofote(x, y, z, alvo=(0, 0, 0), energia=4000, cor="#fff3c4"):
    """Luz de holofote (bom com ambiente noite)."""
    ld = bpy.data.lights.new("Spot", "SPOT")
    ld.energy = energia
    ld.color = hexrgb(cor)
    ld.spot_size = math.radians(25)
    ob = _link(bpy.data.objects.new("Spot", ld))
    ob.location = (x, y, z)
    d = Vector(alvo) - Vector((x, y, z))
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return ob


def tunel(x0, x1, z=-4, altura=1.8):
    """Tunel em CORTE (use com ambiente('subsolo')): aparece na parede de terra da frente."""
    g = grupo("Tunel", ((x0 + x1) / 2, -0.06, z))
    comp = abs(x1 - x0)
    caixa((comp, 0.1, altura), (0, 0, 0), "#2a1a0e", g)
    for i in range(int(comp / 3) + 1):
        xx = -comp / 2 + i * 3
        caixa((0.2, 0.15, altura), (xx, -0.05, 0), "#a0703a", g)
        caixa((0.9, 0.15, 0.2), (xx, -0.05, altura / 2 - 0.1), "#a0703a", g)
    return g


def poco(x, z_fundo=-4, largura=1.4):
    """Poco vertical em corte, da superficie ate z_fundo (ambiente subsolo)."""
    g = grupo("Poco", (x, -0.06, z_fundo / 2))
    caixa((largura, 0.1, abs(z_fundo)), (0, 0, 0), "#2a1a0e", g)
    return g


# ================================================================== veiculos
def carro(x, y, cor="#d9534f", rot=0):
    g = grupo("Carro", (x, y), rot)
    caixa((4.2, 2.0, 0.9), (0, 0, 0.75), cor, g)
    caixa((2.4, 1.8, 0.8), (-0.2, 0, 1.55), cor, g)
    caixa((2.3, 1.85, 0.6), (-0.2, 0, 1.55), "#2b3440", g)
    for dx in (-1.3, 1.3):
        for dy in (-1.0, 1.0):
            cilindro(0.45, 0.35, (dx, dy - 0.17 * (1 if dy > 0 else -1), 0.45), "#1e1e1e", 10, pai=g, rot=(math.pi / 2, 0, 0))
    return g


def caminhao(x, y, cor="#3b6ea5", rot=0):
    g = grupo("Caminhao", (x, y), rot)
    caixa((6, 2.4, 2.8), (-1.2, 0, 1.9), "#e5e5e5", g)
    caixa((2.2, 2.4, 2.2), (2.9, 0, 1.6), cor, g)
    caixa((0.1, 2.0, 0.9), (4.0, 0, 2.0), "#2b3440", g)
    for dx in (-3, -0.5, 2.9):
        for dy in (-1.2, 1.2):
            cilindro(0.55, 0.4, (dx, dy - 0.2 * (1 if dy > 0 else -1), 0.55), "#1e1e1e", 10, pai=g, rot=(math.pi / 2, 0, 0))
    return g


def helicoptero(x, y, z=20, cor="#4b5d2a", f0=1, f1=300):
    g = grupo("Heli", (x, y, z))
    caixa((5, 2.2, 2.2), (0, 0, 0), cor, g)
    caixa((5, 0.5, 0.6), (-4.5, 0, 0.5), cor, g)
    caixa((1.2, 2.1, 1.4), (2.2, 0, 0.2), "#2b3440", g)
    for dy in (-1, 1):
        caixa((4, 0.15, 0.15), (0, dy, -1.4), "#333333", g)
    rotor = grupo("Rotor", (0, 0, 1.4), pai=g)
    caixa((11, 0.4, 0.08), (0, 0, 0), "#222222", rotor)
    caixa((0.4, 11, 0.08), (0, 0, 0), "#222222", rotor)
    girar(rotor, f0, f1, 360 * (f1 - f0) / 6)
    return g


def barco(x, y, cor="#c0392b", rot=0):
    g = grupo("Barco", (x, y), rot)
    caixa((7, 2.6, 1.2), (0, 0, 0.6), cor, g)
    caixa((2.5, 2, 1.5), (-1, 0, 1.9), "#f0f0f0", g)
    return g


def foguete(x, y):
    g = grupo("Foguete", (x, y))
    cilindro(1.5, 14, (0, 0, 0), "#eeeeee", 12, pai=g)
    cilindro(1.5, 4, (0, 0, 14), "#d9534f", 12, raio_topo=0.0, pai=g)
    return g


# ================================================================== bandeira
_PAISES = {
    "brasil": ("h", ["#009c3b"]), "portugal": ("v", ["#006600", "#ff0000", "#ff0000"]),
    "eua": ("h", ["#b22234", "#ffffff"] * 3 + ["#b22234"]), "russia": ("h", ["#ffffff", "#0039a6", "#d52b1e"]),
    "alemanha": ("h", ["#000000", "#dd0000", "#ffce00"]), "franca": ("v", ["#0055a4", "#ffffff", "#ef4135"]),
    "italia": ("v", ["#009246", "#ffffff", "#ce2b37"]), "japao": ("h", ["#ffffff"]),
    "china": ("h", ["#de2910"]), "coreia_norte": ("h", ["#024fa2", "#ffffff", "#ed1c27", "#ed1c27", "#ffffff", "#024fa2"]),
    "coreia_sul": ("h", ["#ffffff"]), "argentina": ("h", ["#74acdf", "#ffffff", "#74acdf"]),
    "espanha": ("h", ["#aa151b", "#f1bf00", "#f1bf00", "#aa151b"]), "mexico": ("v", ["#006847", "#ffffff", "#ce1126"]),
    "reino_unido": ("h", ["#012169"]), "ucrania": ("h", ["#0057b7", "#ffd700"]), "israel": ("h", ["#ffffff"]),
    "branca": ("h", ["#ffffff"]), "vermelha": ("h", ["#d62828"]),
}


def bandeira(x, y, pais="brasil", altura=6, rot=0):
    g = grupo("Bandeira", (x, y), rot)
    cilindro(0.08, altura, (0, 0, 0), "#d0d0d0", 6, pai=g)
    W, Hh = 3.0, 2.0
    modo, faixas = _PAISES.get(pais, _PAISES["vermelha"])
    n = len(faixas)
    for i, cor in enumerate(faixas):
        if modo == "h":
            caixa((W, 0.05, Hh / n), (W / 2 + 0.08, 0, altura - 0.2 - Hh / n * (i + 0.5)), cor, g)
        else:
            caixa((W / n, 0.05, Hh), (0.08 + W / n * (i + 0.5), 0, altura - 0.2 - Hh / 2), cor, g)
    cx, cz = W / 2 + 0.08, altura - 0.2 - Hh / 2
    if pais == "brasil":
        caixa((1.6, 0.06, 1.6), (cx, -0.01, cz), "#ffdf00", g, rot=(0, math.radians(45), 0)).scale = (1.0, 1, 0.62)
        cilindro(0.42, 0.08, (cx, -0.05, cz), "#002776", 14, pai=g, rot=(math.pi / 2, 0, 0))
    elif pais in ("japao", "coreia_sul"):
        cilindro(0.55, 0.08, (cx, -0.05, cz), "#bc002d", 16, pai=g, rot=(math.pi / 2, 0, 0))
    elif pais == "coreia_norte":
        cilindro(0.38, 0.08, (cx - 0.6, -0.05, cz), "#ffffff", 14, pai=g, rot=(math.pi / 2, 0, 0))
    elif pais == "eua":
        caixa((1.3, 0.07, 1.08), (0.08 + 0.65, -0.01, altura - 0.2 - 0.54), "#3c3b6e", g)
    elif pais == "china":
        caixa((0.4, 0.07, 0.4), (0.7, -0.01, altura - 0.7), "#ffde00", g, rot=(0, math.radians(45), 0))
    elif pais == "reino_unido":
        caixa((W, 0.07, 0.35), (cx, -0.01, cz), "#c8102e", g)
        caixa((0.35, 0.07, Hh), (cx, -0.01, cz), "#c8102e", g)
    elif pais == "israel":
        for dz in (-0.7, 0.7):
            caixa((W, 0.07, 0.22), (cx, -0.01, cz + dz), "#0038b8", g)
    return g


# ================================================================== efeitos
def explosao(x, y, f, raio=8, nuclear=False, z=0, cor="#ff8c1a"):
    """Explosao/nuvem que comeca no quadro f. cor muda (ex: '#d61f2b' para tinta vermelha). nuclear=True faz o cogumelo."""
    g = grupo("Explosao", (x, y, z))
    escuro = _clarear(cor, 0.6)
    for i in range(9):  # varias bolas formam uma nuvem com volume
        a = i * 0.7
        dx, dy, dz = math.cos(a) * 0.45, math.sin(a) * 0.45, 0.25 + (i % 3) * 0.2
        c = cor if i % 2 == 0 else escuro
        b = esfera(1, (dx * raio, dy * raio, dz * raio), c, sub=2, pai=g, material=mat(c, emissao=1.5 if i % 2 == 0 else 0.3))
        s = raio * _rng.uniform(0.35, 0.55)
        _escala_keys(b, [(f - 1, 0.01), (f, 0.05), (f + 6 + i, s), (f + 45, s * 1.15)])
    bola = esfera(1, (0, 0, raio * 0.3), "#fff2a0", sub=2, pai=g, material=mat("#fff2a0", emissao=10))
    _escala_keys(bola, [(f - 1, 0.01), (f, raio * 0.5), (f + 5, raio * 0.3), (f + 12, 0.01)])
    luz = bpy.data.lights.new("Boom", "POINT")
    luz.color = hexrgb("#ffb14a")
    lo = _link(bpy.data.objects.new("Boom", luz))
    lo.parent = g
    lo.location = (0, 0, raio)
    for ff, e in ((f - 1, 0), (f + 2, 2_000_000 if nuclear else 300_000), (f + 40, 0)):
        luz.energy = e
        luz.keyframe_insert("energy", frame=ff)
    if nuclear:
        haste = cilindro(raio * 0.25, raio * 2.5, (0, 0, 0), "#9a8c80", 10, pai=g)
        _escala_keys(haste, [(f - 1, 0.01), (f + 10, 0.01), (f + 60, 1.0)], so_z=True)
        cogumelo = esfera(raio * 0.9, (0, 0, raio * 2.6), "#b0a090", sub=2, pai=g)
        cogumelo.scale = (1.3, 1.3, 0.6)
        _escala_keys(cogumelo, [(f - 1, 0.01), (f + 15, 0.01), (f + 70, 1.0)], base=(1.3, 1.3, 0.6))
        onda = cilindro(1, 0.4, (0, 0, 0.2), "#ffffff", 32, pai=g, material=mat("#ffffff", emissao=2))
        _escala_keys(onda, [(f - 1, 0.01), (f, 0.5), (f + 45, raio * 6)], so_xy=True)
    return g


def _mat_fumaca(cor="#f2f2f2"):
    key = ("fumaca", cor)
    if key in _mats:
        return _mats[key]
    m = mat(cor, rug=1.0, emissao=0.6)
    m = m.copy()
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Alpha"].default_value = 0.3
    for attr, val in (("blend_method", "BLEND"), ("surface_render_method", "BLENDED")):
        try:
            setattr(m, attr, val)
        except (AttributeError, TypeError):
            pass
    _mats[key] = m
    return m


def fumaca(x, y, f0, f1, z=0, n=14, cor="#e9e9e9"):
    """Coluna de fumaca fina subindo alto e se desfazendo (bolinhas semitransparentes)."""
    g = grupo("Fumaca", (x, y, z))
    m = _mat_fumaca(cor)
    ciclo = 60
    for i in range(n):
        b = esfera(1.0, (0, 0, 0), cor, sub=2, pai=g, material=m)
        ini = f0 + (i * ciclo) // n
        while ini < f1:
            b.location = (_rng.uniform(-0.2, 0.2), _rng.uniform(-0.2, 0.2), 1.3)
            b.keyframe_insert("location", frame=ini)
            _escala_keys(b, [(ini, 0.15)])
            b.location = (_rng.uniform(-1.2, 1.2), _rng.uniform(-1.2, 1.2), _rng.uniform(9, 13))
            b.keyframe_insert("location", frame=ini + ciclo)
            _escala_keys(b, [(ini + int(ciclo * 0.5), 0.75), (ini + ciclo, 0.01)])
            ini += ciclo
    return g


def fogo(x, y, f0=1, f1=300, escala=1.0, z=0, com_lenha=True):
    """Fogueira com chamas tremulando e luz quente."""
    g = grupo("Fogo", (x, y, z))
    g.scale = (escala,) * 3
    if com_lenha:
        for a in range(0, 180, 45):
            caixa((1.4, 0.18, 0.18), (0, 0, 0.12), "#6b4325", g, rot=(0, 0, math.radians(a)))
        for a in range(0, 360, 40):
            esfera(0.16, (math.cos(math.radians(a)) * 0.75, math.sin(math.radians(a)) * 0.75, 0.08), "#8a8a8a", sub=0, pai=g)
    chamas = []
    for i, (cor, r, h, dx) in enumerate((("#ff4d00", 0.45, 1.3, 0), ("#ff8c1a", 0.32, 1.0, 0.15),
                                         ("#ffd23f", 0.2, 0.7, -0.1))):
        c = cilindro(r, h, (dx, 0, 0.15), cor, 7, raio_topo=0.0, pai=g, material=mat(cor, emissao=8))
        chamas.append(c)
    for i, c in enumerate(chamas):
        for f in range(f0, f1 + 1, 4):
            s = 1 + 0.18 * math.sin(f * 0.9 + i * 2)
            c.scale = (1 + 0.06 * math.sin(f * 1.3 + i), 1, s)
            c.keyframe_insert("scale", frame=f)
    luz = bpy.data.lights.new("FogoLuz", "POINT")
    luz.color = hexrgb("#ff9a3c")
    luz.energy = 400 * escala
    lo = _link(bpy.data.objects.new("FogoLuz", luz))
    lo.parent = g
    lo.location = (0, 0, 1.2)
    return g


# ================================================================== animacao
def _escala_keys(ob, keys, base=(1, 1, 1), so_z=False, so_xy=False):
    for f, s in keys:
        if so_z:
            ob.scale = (base[0], base[1], base[2] * s)
        elif so_xy:
            ob.scale = (base[0] * s, base[1] * s, base[2])
        else:
            ob.scale = (base[0] * s, base[1] * s, base[2] * s)
        ob.keyframe_insert("scale", frame=max(0, f))


def surgir(ob, f, dur=14, modo="crescer"):
    """Faz o grupo aparecer no quadro f. modo: crescer (sobe do chao) | pop | cair (do ceu)."""
    base = tuple(ob.scale)
    if modo == "cair":
        z = ob.location.z
        ob.location.z = z + 40
        ob.keyframe_insert("location", frame=max(0, f - 1))
        ob.keyframe_insert("location", frame=max(0, f))
        ob.location.z = z
        ob.keyframe_insert("location", frame=f + dur)
        _escala_keys(ob, [(f - 2, 0.0001), (f, 1)], base)
        return ob
    if modo == "pop":
        _escala_keys(ob, [(f - 1, 0.0001), (f, 0.05), (f + int(dur * 0.7), 1.12), (f + dur, 1)], base)
    else:
        _escala_keys(ob, [(f - 1, 0.0001), (f, 0.02), (f + int(dur * 0.75), 1.06), (f + dur, 1)], base, so_z=True)
    return ob


def sumir(ob, f, dur=10):
    base = tuple(ob.scale)
    _escala_keys(ob, [(f, 1), (f + dur, 0.0001)], base)
    return ob


def mover(ob, keys):
    """keys = [(quadro, (x, y, z)), ...]"""
    for f, p in keys:
        ob.location = p
        ob.keyframe_insert("location", frame=f)
    return ob


def girar(ob, f0, f1, graus):
    z0 = ob.rotation_euler.z
    ob.keyframe_insert("rotation_euler", frame=f0)
    ob.rotation_euler.z = z0 + math.radians(graus)
    ob.keyframe_insert("rotation_euler", frame=f1)
    ad = ob.animation_data
    if ad and ad.action:
        for fc in getattr(ad.action, "fcurves", []):
            if fc.data_path == "rotation_euler":
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"
    ob["linear"] = True
    return ob


def rotulo(alvo, texto, f0=1, f1=None, dz=None):
    """Etiqueta amarela em 2D que acompanha o alvo (grupo/boneco ou (x,y,z)). dz = altura acima."""
    ROTULOS.append((alvo, texto.upper(), f0, f1, dz))


# ================================================================== bonecos
TIPOS_BONECO = {
    "preso": dict(roupa="#ff7a1a", calca="#ff7a1a", pele="#f2c299", sapato="#3a2a20"),
    "guarda": dict(roupa="#26344d", calca="#1b2233", pele="#e8b48c", sapato="#111111", bone="#1b2233"),
    "policial": dict(roupa="#2d4a8a", calca="#1b2233", pele="#e8b48c", sapato="#111111", bone="#1b2233"),
    "soldado": dict(roupa="#4b5d2a", calca="#3d4b22", pele="#e8b48c", sapato="#222222", capacete="#4b5d2a"),
    "civil": dict(roupa="#3b82f6", calca="#2d3748", pele="#f2c299", sapato="#3a2a20", cabelo="#4a2d1a"),
    "mulher": dict(roupa="#e0457b", calca="#2d3748", pele="#f2c299", sapato="#3a2a20", cabelo_longo="#5a3420"),
    "cientista": dict(roupa="#f4f4f4", calca="#4a4f57", pele="#f2c299", sapato="#222222", cabelo="#cfcfcf"),
    "trabalhador": dict(roupa="#f08a24", calca="#2d4a8a", pele="#e8b48c", sapato="#3a2a20", capacete="#ffcc00"),
    "medico": dict(roupa="#9fd8cf", calca="#9fd8cf", pele="#f2c299", sapato="#ffffff", cabelo="#4a2d1a"),
    "ladrao": dict(roupa="#222222", calca="#222222", pele="#e8b48c", sapato="#111111", touca="#222222"),
    "turista": dict(roupa="#f7d046", calca="#c49a6c", pele="#f2c299", sapato="#ffffff", bone="#d9534f"),
    "astronauta": dict(roupa="#f0f0f0", calca="#f0f0f0", pele="#f0f0f0", sapato="#bbbbbb", capacete="#f0f0f0"),
    "rei": dict(roupa="#6a2c91", calca="#4b1f66", pele="#f2c299", sapato="#3a2a20", coroa="#ffc400"),
    "crianca": dict(roupa="#2bb673", calca="#2d3748", pele="#f2c299", sapato="#3a2a20", cabelo="#4a2d1a", escala=0.7),
}


EMOCOES = ("neutro", "feliz", "bravo", "assustado", "triste", "surpreso", "malicioso")


def _rosto(cab, emocao, tipo):
    """Olhos com pupila e brilho, sobrancelhas e boca conforme a emocao. Rosto no plano y=-0.29."""
    y = -0.295
    grande = emocao in ("assustado", "surpreso")
    for ex in (-0.13, 0.13):
        caixa((0.15 if grande else 0.13, 0.02, 0.19 if grande else 0.15), (ex, y, 0.34), "#ffffff", cab)
        caixa((0.06 if grande else 0.08, 0.02, 0.07 if grande else 0.1), (ex + 0.01, y - 0.008, 0.33), "#15151a", cab)
        caixa((0.025, 0.02, 0.025), (ex + 0.03, y - 0.014, 0.36), "#ffffff", cab)
        # sobrancelha: inclinacao conforme a emocao (lado interno = perto do nariz)
        lado = 1 if ex < 0 else -1
        incl = {"bravo": 0.45, "malicioso": 0.3, "triste": -0.4, "assustado": -0.25, "surpreso": 0.0}.get(emocao, 0.08)
        zb = 0.47 + (0.05 if grande else 0.0)
        caixa((0.17, 0.02, 0.045), (ex, y - 0.004, zb), "#2a1a10", cab, rot=(0, incl * lado, 0))
    if emocao == "feliz":
        caixa((0.24, 0.02, 0.09), (0, y, 0.15), "#6b1f1f", cab)
        caixa((0.2, 0.02, 0.035), (0, y - 0.005, 0.175), "#ffffff", cab)
    elif emocao in ("assustado", "surpreso"):
        caixa((0.12, 0.02, 0.15), (0, y, 0.13), "#3a0f0f", cab)
    elif emocao == "bravo":
        caixa((0.22, 0.02, 0.05), (0, y, 0.14), "#3a0f0f", cab)
        caixa((0.18, 0.02, 0.02), (0, y - 0.004, 0.15), "#ffffff", cab)
    elif emocao == "triste":
        caixa((0.18, 0.02, 0.035), (0, y, 0.15), "#5a2a1a", cab)
        for dx in (-0.1, 0.1):
            caixa((0.04, 0.02, 0.05), (dx, y, 0.12), "#5a2a1a", cab)
    elif emocao == "malicioso":
        caixa((0.2, 0.02, 0.035), (0.02, y, 0.15), "#5a2a1a", cab, rot=(0, -0.25, 0))
    else:
        caixa((0.16, 0.02, 0.035), (0, y, 0.15), "#5a2a1a", cab)


class Boneco:
    """Boneco quadradao. Frente = -Y local (olhando para a camera padrao)."""

    def __init__(self, tipo="civil", pos=(0, 0), olhar=0, escala=1.0, cor=None, emocao="neutro"):
        c = dict(TIPOS_BONECO.get(tipo, TIPOS_BONECO["civil"]))
        if cor:
            c["roupa"] = cor
        escala *= c.get("escala", 1.0)
        self.root = grupo(f"Boneco_{tipo}", (pos[0], pos[1], pos[2] if len(pos) > 2 else 0), olhar)
        self.root.scale = (escala,) * 3
        r = self.root
        self.perna_e = caixa((0.28, 0.3, 0.75), (-0.16, 0, 0.75), c["calca"], r, offset=(0, 0, -0.375))
        self.perna_d = caixa((0.28, 0.3, 0.75), (0.16, 0, 0.75), c["calca"], r, offset=(0, 0, -0.375))
        for p in (self.perna_e, self.perna_d):
            caixa((0.3, 0.38, 0.12), (0, -0.04, -0.7), c["sapato"], p)
        self.tronco = caixa((0.62, 0.34, 0.72), (0, 0, 1.11), c["roupa"], r)
        self.braco_e = caixa((0.22, 0.26, 0.68), (-0.43, 0, 1.43), c["roupa"], r, offset=(0, 0, -0.32))
        self.braco_d = caixa((0.22, 0.26, 0.68), (0.43, 0, 1.43), c["roupa"], r, offset=(0, 0, -0.32))
        for b in (self.braco_e, self.braco_d):
            caixa((0.2, 0.22, 0.16), (0, 0, -0.7), c["pele"], b)
        self.cabeca = caixa((0.6, 0.58, 0.6), (0, 0, 1.47), c["pele"], r, offset=(0, 0, 0.3))
        _rosto(self.cabeca, emocao, tipo)
        if tipo == "preso":
            caixa((0.3, 0.02, 0.12), (0.12, -0.175, 0.15), "#ffffff", self.tronco)
        if "bone" in c:
            caixa((0.6, 0.6, 0.16), (0, 0, 0.6), c["bone"], self.cabeca)
            caixa((0.5, 0.22, 0.05), (0, -0.36, 0.53), c["bone"], self.cabeca)
        if "capacete" in c:
            caixa((0.66, 0.66, 0.24), (0, 0, 0.62), c["capacete"], self.cabeca)
        if "cabelo" in c:
            caixa((0.6, 0.6, 0.12), (0, 0.02, 0.6), c["cabelo"], self.cabeca)
            caixa((0.6, 0.12, 0.4), (0, 0.26, 0.4), c["cabelo"], self.cabeca)
        if "cabelo_longo" in c:
            caixa((0.62, 0.62, 0.14), (0, 0.02, 0.6), c["cabelo_longo"], self.cabeca)
            caixa((0.62, 0.16, 0.85), (0, 0.27, 0.2), c["cabelo_longo"], self.cabeca)
        if "touca" in c:
            caixa((0.64, 0.62, 0.22), (0, 0, 0.6), c["touca"], self.cabeca)
        if "coroa" in c:
            for dx in (-0.2, 0, 0.2):
                caixa((0.14, 0.14, 0.2), (dx, -0.2, 0.68), c["coroa"], self.cabeca)
            caixa((0.6, 0.6, 0.1), (0, 0, 0.6), c["coroa"], self.cabeca)
        self.partes = [self.perna_e, self.perna_d, self.braco_e, self.braco_d, self.cabeca]

    def _key(self, f):
        for ob in self.partes:
            ob.keyframe_insert("rotation_euler", frame=f)
        self.root.keyframe_insert("location", frame=f)
        self.root.keyframe_insert("rotation_euler", frame=f)

    def _pose(self, acao, fase):
        s = math.sin(fase)
        pe = pd = be = bd = bex = bdx = 0.0
        if acao == "andar":
            pe, pd, be, bd = 0.6 * s, -0.6 * s, -0.55 * s, 0.55 * s
        elif acao == "correr":
            pe, pd, be, bd = 1.0 * s, -1.0 * s, -1.1 * s, 1.1 * s
        elif acao == "escalar":
            be, bd = math.pi * 0.9 + 0.3 * s, math.pi * 0.9 - 0.3 * s
            pe, pd = -0.7 * max(0, s), -0.7 * max(0, -s)
        elif acao == "cavar":
            be = bd = -0.6 - 0.9 * max(0, s)
        elif acao == "rastejar":
            pe, pd, be, bd = 0.3 * s, -0.3 * s, -1.6 + 0.4 * s, -1.6 - 0.4 * s
        elif acao == "comemorar":
            bex, bdx = -2.6 - 0.3 * s, 2.6 + 0.3 * s
        elif acao == "susto":
            bex, bdx = -2.3 + 0.1 * s, 2.3 - 0.1 * s
        elif acao == "apontar":
            bd = -1.5
        elif acao == "acenar":
            bdx = 2.5 + 0.4 * s
        else:  # parado
            be, bd = 0.05 * s, -0.05 * s
        self.perna_e.rotation_euler = (pe, 0, 0)
        self.perna_d.rotation_euler = (pd, 0, 0)
        self.braco_e.rotation_euler = (be, bex, 0)
        self.braco_d.rotation_euler = (bd, bdx, 0)
        self.cabeca.rotation_euler = (0, 0, 0.12 * math.sin(fase * 0.3))

    def caminho(self, pontos, f0, f1, acao="andar", z=0.0):
        """Vai pelos pontos [(x,y), ...] do quadro f0 ao f1. acao: andar|correr|rastejar."""
        pts = [Vector((p[0], p[1], 0)) for p in pontos]
        segs = [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)] or [(pts[0], pts[0])]
        total = sum((b - a).length for a, b in segs) or 0.001
        passo = {"andar": 2.2, "correr": 3.2, "rastejar": 2.5}.get(acao, 2.2)
        deitado = acao == "rastejar"
        for f in list(range(f0, f1 + 1, 2)) + [f1]:
            t = (f - f0) / max(1, f1 - f0)
            dist = t * total
            pos, direc = pts[0], Vector((0, -1, 0))
            for a, b in segs:
                L = (b - a).length
                if dist <= L or (a, b) == segs[-1]:
                    pos = a + (b - a) * (min(dist, L) / L if L else 0)
                    direc = (b - a).normalized() if L else direc
                    break
                dist -= L
            pulo = abs(math.sin(t * total * passo)) * (0.05 if acao == "andar" else 0.12 if acao == "correr" else 0)
            self.root.location = (pos.x, pos.y, z + pulo + (0.3 if deitado else 0))
            self.root.rotation_euler = (math.radians(-80) if deitado else 0, 0, math.atan2(direc.y, direc.x) + math.pi / 2)
            self._pose(acao, t * total * passo)
            self._key(f)
        return self

    def parado(self, f0, f1, acao="parado", olhar=None):
        """Fica no lugar fazendo: parado|comemorar|susto|apontar|acenar|cavar. olhar em graus (0 = camera)."""
        if olhar is not None:
            self.root.rotation_euler = (0, 0, math.radians(olhar))
        for f in list(range(f0, f1 + 1, 3)) + [f1]:
            self._pose(acao, f / FPS * 7)
            self._key(f)
        return self

    def escalar(self, f0, f1, altura=5.0, olhar=180):
        """Sobe reto ate 'altura' (ex: um muro na frente dele). olhar=180 = de costas para a camera."""
        x, y = self.root.location.x, self.root.location.y
        z0 = self.root.location.z
        self.root.rotation_euler = (0, 0, math.radians(olhar))
        for f in list(range(f0, f1 + 1, 2)) + [f1]:
            t = (f - f0) / max(1, f1 - f0)
            self.root.location = (x, y, z0 + altura * t)
            self._pose("escalar", t * 18)
            self._key(f)
        return self

    def pular_para(self, f0, f1, destino):
        """Pulo em arco ate destino (x, y, z)."""
        a = Vector(self.root.location)
        b = Vector(destino)
        for f in list(range(f0, f1 + 1, 2)) + [f1]:
            t = (f - f0) / max(1, f1 - f0)
            p = a.lerp(b, t)
            p.z += math.sin(math.pi * t) * min(1.2, 0.25 * (b - a).length + 0.4)
            self.root.location = p
            self._pose("comemorar", t * 5)
            self._key(f)
        return self


# ================================================================== modelos Kenney (CC0)
KENNEY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kenney")
KCHARS = os.path.join(KENNEY, "blocky-characters", "Models", "GLB format")
ESCALA_PACOTE = {"city-kit-commercial": 10.0, "city-kit-suburban": 7.5, "car-kit": 1.75, "nature-kit": 4.0,
                 "furniture-kit": 1.8, "city-kit-roads": 10.0, "survival-kit": 3.2, "blocky-characters": 0.7}
_kidx = None


def _indice():
    global _kidx
    if _kidx is None:
        _kidx = {}
        for f in glob.glob(os.path.join(KENNEY, "*", "**", "*.glb"), recursive=True):
            pacote = os.path.relpath(f, KENNEY).split(os.sep)[0]
            _kidx.setdefault(os.path.splitext(os.path.basename(f))[0], (f, pacote))
    return _kidx


def tem_modelo(nome):
    return nome in _indice()


def _importar(caminho):
    antes = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=caminho)
    novos = [o for o in bpy.data.objects if o not in antes]
    return novos, [o for o in novos if o.parent is None or o.parent not in novos]


def modelo(nome, x=0, y=0, rot=0, escala=1.0, z=0):
    """Modelo 3D pronto (Kenney). Centralizado em (x,y), apoiado no chao, em metros reais."""
    item = _indice().get(nome)
    if not item:
        raise ValueError(f"modelo '{nome}' nao existe")
    caminho, pacote = item
    novos, topo = _importar(caminho)
    g = grupo(f"Mod_{nome}", (x, y, z), rot)
    for o in topo:
        o.parent = g
    bpy.context.view_layer.update()
    mn, mx = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in novos:
        if o.type == "MESH":
            for c in o.bound_box:
                w = g.matrix_world.inverted() @ (o.matrix_world @ Vector(c))
                mn = Vector(map(min, mn, w))
                mx = Vector(map(max, mx, w))
    centro = Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
    for o in topo:
        o.location -= centro
    s = ESCALA_PACOTE.get(pacote, 1.0) * escala
    g.scale = (s, s, s)
    return g


KTIPOS = {  # tipo -> (letra do personagem, textura alternativa)
    "preso": ("b", "texture-preso.png"), "guarda": ("j", "texture-guarda.png"), "policial": ("j", None),
    "ladrao": ("r", None), "ninja": ("r", None), "soldado": ("m", None), "explorador": ("m", None),
    "cientista": ("i", None), "medico": ("i", None), "velho": ("i", None), "trabalhador": ("b", None),
    "civil": ("k", None), "homem": ("c", None), "turista": ("c", None), "mulher": ("e", None), "mulher2": ("f", None),
    "crianca": ("f", None), "pirata": ("p", None), "zumbi": ("l", None), "robo": ("g", None), "robo2": ("h", None),
    "presidente": ("q", None), "agente": ("q", None), "empresario": ("q", None), "monstro": ("o", None),
    "boneco_teste": ("d", None), "sobrevivente": ("a", None), "mendigo": ("a", None), "japonesa": ("n", None),
    "sem_rosto": ("c", "texture-semrosto.png"), "manequim": ("c", "texture-semrosto.png"),
    # elenco brasileiro pintado por fazer_skins.py (texture-br_<nome>.png)
    "br_voce": ("c", "texture-br_voce.png"), "br_senhora": ("c", "texture-br_senhora.png"),
    "br_motorista": ("c", "texture-br_motorista.png"), "br_homem": ("c", "texture-br_homem.png"),
    "br_trocado": ("c", "texture-br_trocado.png"), "br_torcedor": ("c", "texture-br_torcedor.png"),
    "br_moca": ("c", "texture-br_moca.png"), "br_idoso": ("c", "texture-br_idoso.png"),
    "br_porteiro": ("c", "texture-br_porteiro.png"), "br_jovem_mulher": ("c", "texture-br_jovem_mulher.png"),
    "br_detetive": ("c", "texture-br_detetive.png"), "br_coronel": ("c", "texture-br_coronel.png"),
    "br_primeira_dama": ("c", "texture-br_primeira_dama.png"), "br_medica": ("c", "texture-br_medica.png"),
    "br_secretario": ("c", "texture-br_secretario.png"), "br_copeira": ("c", "texture-br_copeira.png"),
    "br_cabo": ("c", "texture-br_cabo.png"), "br_presidente": ("c", "texture-br_presidente.png"),
}
KANIM = {"andar": "walk", "correr": "sprint", "parado": "static", "balancar": "idle", "comemorar": "emote-yes", "acenar": "emote-yes",
         "sim": "emote-yes", "nao": "emote-no", "susto": "emote-no", "apontar": "interact-right", "cavar": "pick-up",
         "pegar": "pick-up", "cair": "die", "morrer": "die", "sentar": "sit", "lutar": "attack-melee-right",
         "socar": "attack-melee-right", "chutar": "attack-kick-right", "dirigir": "drive", "segurar": "holding-right",
         "atirar": "holding-right-shoot", "escalar": "walk", "rastejar": "walk", "interagir": "interact-right"}
_UMA_VEZ = {"die", "sit", "pick-up"}
_GESTOS = {"emote-yes", "emote-no", "interact-right", "interact-left", "attack-melee-right", "attack-melee-left",
           "attack-kick-right", "attack-kick-left"}


class KBoneco:
    pass  # definida de verdade logo abaixo (precisa existir antes de Boneco.__new__ rodar)


def _boneco_new(cls, tipo="civil", *a, **k):
    if cls is Boneco and tipo in KTIPOS and os.path.isdir(KCHARS):
        return object.__new__(KBoneco)
    return object.__new__(cls)


Boneco.__new__ = _boneco_new


class KBoneco(Boneco):  # noqa: F811
    """Personagem Kenney animado, com a mesma interface do Boneco."""

    def __init__(self, tipo="civil", pos=(0, 0), olhar=0, escala=1.0, cor=None, emocao="neutro"):
        letra, textura = KTIPOS[tipo]
        novos, topo = _importar(os.path.join(KCHARS, f"character-{letra}.glb"))
        self.root = grupo(f"K_{tipo}", (pos[0], pos[1], pos[2] if len(pos) > 2 else 0), olhar)
        for o in topo:
            o.parent = self.root
        s = ESCALA_PACOTE["blocky-characters"] * escala * (0.7 if tipo == "crianca" else 1.0)
        self.root.scale = (s, s, s)
        self._kenney = True
        self.tipo = tipo
        self.partes = []
        self.anim_obj = [o for o in novos if o.animation_data]
        for o in self.anim_obj:
            o.animation_data.action = None
            for t in o.animation_data.nla_tracks:
                t.mute = True
        if textura:
            img = bpy.data.images.load(os.path.join(KCHARS, "Textures", textura), check_existing=True)
            for o in novos:
                for slot in getattr(o, "material_slots", []):
                    m = slot.material
                    if m and m.use_nodes:
                        for n in m.node_tree.nodes:
                            if n.type == "TEX_IMAGE":
                                n.image = img
        self._textura = textura
        self._novos = novos
        self._boca = None
        self._anim("parado", 1, 1)

    def falar(self, f0, f1, seed=0):
        """A boca abre e fecha entre os quadros f0 e f1 (use as marcas T['lK'] e T['lK_fim'] da fala).
        Precisa da skin com boca aberta: texture-br_<nome>_fala.png (feita por fazer_skins.py)."""
        if not self._textura:
            return self
        arq = os.path.join(KCHARS, "Textures", self._textura.replace(".png", "_fala.png"))
        if not os.path.exists(arq):
            return self
        if self._boca is None:
            self._boca = []
            img = bpy.data.images.load(arq, check_existing=True)
            vistos = set()
            for o in self._novos:
                for slot in getattr(o, "material_slots", []):
                    m = slot.material
                    if not m or not m.use_nodes or m.name in vistos:
                        continue
                    vistos.add(m.name)
                    nt = m.node_tree
                    tex = next((n for n in nt.nodes if n.type == "TEX_IMAGE"), None)
                    if tex is None:
                        continue
                    t2 = nt.nodes.new("ShaderNodeTexImage")
                    t2.image = img
                    t2.interpolation = tex.interpolation
                    for lk in list(tex.inputs["Vector"].links):
                        nt.links.new(lk.from_socket, t2.inputs["Vector"])
                    mix = nt.nodes.new("ShaderNodeMixRGB")
                    mix.inputs[0].default_value = 0.0
                    for lk in list(tex.outputs["Color"].links):
                        nt.links.new(mix.outputs[0], lk.to_socket)
                    nt.links.new(tex.outputs["Color"], mix.inputs[1])
                    nt.links.new(t2.outputs["Color"], mix.inputs[2])
                    self._boca.append((nt, mix))
        r = random.Random(int(f0) + seed)
        for nt, mix in self._boca:
            fac = mix.inputs[0]
            fac.default_value = 0.0
            fac.keyframe_insert("default_value", frame=max(0, int(f0) - 1))
            f, aberta = int(f0), True
            while f < int(f1):
                fac.default_value = 1.0 if aberta else 0.0
                fac.keyframe_insert("default_value", frame=f)
                f += r.choice([3, 3, 4, 5]) if aberta else r.choice([2, 3, 3, 4])
                aberta = not aberta
            fac.default_value = 0.0
            fac.keyframe_insert("default_value", frame=int(f1))
            ad = nt.animation_data
            if ad and ad.action:
                for fc in getattr(ad.action, "fcurves", []):
                    for kp in fc.keyframe_points:
                        kp.interpolation = "CONSTANT"
        return self

    def _anim(self, acao, f0, f1):
        nome = KANIM.get(acao, acao)
        if nome in _GESTOS:
            # gesto toca UMA vez e depois o boneco fica parado (em loop ele fica virando de um lado pro outro)
            L = 0
            for o in self.anim_obj:
                bt = next((t for t in o.animation_data.nla_tracks if t.name == nome and t.strips), None)
                if bt:
                    L = int(bt.strips[0].action_frame_end - bt.strips[0].action_frame_start)
                    break
            ini = int(f0) + 8
            fim = min(int(f1), ini + L)
            if ini > f0:
                self._tira("static", f0, ini - 1, True)
            self._tira(nome, ini, fim, False)
            if fim + 1 < f1:
                self._tira("static", fim + 1, f1, True)
            return
        self._tira(nome, f0, f1, nome not in _UMA_VEZ)

    def _tira(self, nome, f0, f1, repetir):
        for o in self.anim_obj:
            ad = o.animation_data
            base_t = next((t for t in ad.nla_tracks if t.name == nome and t.strips), None)
            if base_t is None:
                continue
            sb = base_t.strips[0]
            tr = ad.nla_tracks.new()
            st = tr.strips.new(nome, int(f0), sb.action)
            try:
                st.action_slot = sb.action_slot
            except (AttributeError, TypeError):
                pass
            st.action_frame_start, st.action_frame_end = sb.action_frame_start, sb.action_frame_end
            L = max(1.0, sb.action_frame_end - sb.action_frame_start)
            if not repetir:
                st.repeat = 1.0
                st.extrapolation = "HOLD_FORWARD"   # segura a pose final so para a frente
            else:
                st.repeat = max(0.2, (max(1, f1 - f0) + 1) / L)
                st.extrapolation = "NOTHING" if f1 > f0 else "HOLD_FORWARD"   # nao vaza para fora do intervalo

    def _pose(self, acao, fase):
        pass

    def _key(self, f):
        self.root.keyframe_insert("location", frame=f)
        self.root.keyframe_insert("rotation_euler", frame=f)

    def caminho(self, pontos, f0, f1, acao="andar", z=0.0):
        # personagem Kenney nunca deita/flutua: 'rastejar' vira andar devagar, sempre de pe no chao
        acao_mov = "andar" if acao not in ("andar", "correr") else acao
        Boneco.caminho(self, pontos, f0, f1, acao_mov, z)
        self._anim(acao_mov, f0, f1)
        return self

    def parado(self, f0, f1, acao="parado", olhar=None):
        if olhar is not None:
            self.root.rotation_euler = (0, 0, math.radians(olhar))
        self._key(f0)
        self._key(f1)
        self._anim(acao, f0, f1)
        # respiracao leve (a pose parada do modelo e totalmente dura)
        s0 = tuple(self.root.scale)
        fase = (hash(self.tipo) % 20) + (self.root.location.x * 7) % 15
        for f in range(int(f0), int(f1) + 1, 12):
            k = 1 + 0.012 * math.sin((f + fase) / 14.0)
            self.root.scale = (s0[0], s0[1], s0[2] * k)
            self.root.keyframe_insert("scale", frame=f)
        self.root.scale = s0
        return self

    def escalar(self, f0, f1, altura=5.0, olhar=180):
        Boneco.escalar(self, f0, f1, altura, olhar)
        self._anim("escalar", f0, f1)
        return self

    def pular_para(self, f0, f1, destino):
        Boneco.pular_para(self, f0, f1, destino)
        self._anim("correr", f0, f1)
        return self


def multidao(tipo, n, area, f0, f1, acao="andar", seed=0, z=0.0, olhar_para=None):
    """n bonecos dentro de area=(xmin, xmax, ymin, ymax). olhar_para=(x,y): parados encarando esse ponto."""
    r = random.Random(seed)
    xmin, xmax, ymin, ymax = area
    lista = []
    for i in range(n):
        p = [(r.uniform(xmin, xmax), r.uniform(ymin, ymax))]
        for _ in range(3):
            p.append((min(xmax, max(xmin, p[-1][0] + r.uniform(-6, 6))), min(ymax, max(ymin, p[-1][1] + r.uniform(-6, 6)))))
        b = Boneco(tipo, p[0])
        if acao in ("andar", "correr"):
            b.caminho(p, f0, f1, acao, z)
        else:
            b.root.location.z = z
            if olhar_para is not None:
                ang = math.degrees(math.atan2(olhar_para[1] - p[0][1], olhar_para[0] - p[0][0])) + 90
            else:
                ang = r.uniform(-40, 40)
            b.parado(f0, f1, acao, olhar=ang)
        lista.append(b)
    return lista


def fila(tipo, n, de, para, f0, f1, acao="andar", espaco=1.6):
    """n bonecos em fila indo de 'de' (x,y) para 'para' (x,y)."""
    a, b = Vector((*de, 0)), Vector((*para, 0))
    d = (b - a).normalized() if (b - a).length else Vector((1, 0, 0))
    lista = []
    for i in range(n):
        ini = a - d * espaco * i
        fim = b - d * espaco * i
        bo = Boneco(tipo, (ini.x, ini.y))
        bo.caminho([(ini.x, ini.y), (fim.x, fim.y)], f0, f1, acao)
        lista.append(bo)
    return lista


# ================================================================== camera
def _cam():
    sc = bpy.context.scene
    if sc.camera:
        return sc.camera, bpy.data.objects["AlvoCam"]
    cd = bpy.data.cameras.new("Cam")
    cd.lens = 30
    cd.clip_end = 3000
    cam = _link(bpy.data.objects.new("Cam", cd))
    sc.camera = cam
    alvo = grupo("AlvoCam")
    c = cam.constraints.new("TRACK_TO")
    c.target = alvo
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    return cam, alvo


def camera(keys, alvo_keys, lente=30):
    """Trajeto livre: keys=[(quadro,(x,y,z))], alvo_keys=[(quadro,(x,y,z))] para onde olha."""
    cam, alvo = _cam()
    cam.data.lens = lente
    for f, p in keys:
        cam.location = p
        cam.keyframe_insert("location", frame=f)
    for f, p in alvo_keys:
        alvo.location = p
        alvo.keyframe_insert("location", frame=f)
    return cam


def cam_aerea(alvo, distancia, altura, f0, f1, giro=25, aproximar=0.75, angulo_ini=-90, lente=30):
    """Orbita em volta do alvo (x,y,z), comecando na frente (-Y), girando 'giro' graus e se aproximando."""
    keys = []
    passos = 6
    for i in range(passos + 1):
        t = i / passos
        ang = math.radians(angulo_ini + giro * t)
        dist = distancia * (1 - (1 - aproximar) * t)
        h = altura * (1 - (1 - aproximar) * t)
        keys.append((int(f0 + (f1 - f0) * t), (alvo[0] + math.cos(ang) * dist, alvo[1] + math.sin(ang) * dist, alvo[2] + h)))
    return camera(keys, [(f0, alvo), (f1, alvo)], lente)


def cam_aproximar(alvo, de, para, f0, f1, lente=30):
    """Sai da posicao 'de' (x,y,z) e vai ate 'para' olhando sempre para o alvo."""
    return camera([(f0, de), (f1, para)], [(f0, alvo), (f1, alvo)], lente)


def cam_seguir(boneco, f0, f1, distancia=8, altura=4, lado=-1):
    """Camera que acompanha um boneco (de tras/lado)."""
    cam, alvo = _cam()
    sc = bpy.context.scene
    for f in range(f0, f1 + 1, 6):
        sc.frame_set(f)
        p = boneco.root.matrix_world.translation
        cam.location = (p.x + lado * distancia * 0.4, p.y - distancia, p.z + altura)
        cam.keyframe_insert("location", frame=f)
        alvo.location = (p.x, p.y, p.z + 1.2)
        alvo.keyframe_insert("location", frame=f)
    return cam


def cam_corte(x_centro, z_centro, f0, f1, largura=30, deslizar=8):
    """Camera de lado mostrando o corte do subsolo (ambiente subsolo)."""
    d = largura * 0.9
    return camera([(f0, (x_centro - deslizar / 2, -d, z_centro + 2)), (f1, (x_centro + deslizar / 2, -d * 0.85, z_centro + 1))],
                  [(f0, (x_centro - deslizar / 2, 0, z_centro)), (f1, (x_centro + deslizar / 2, 0, z_centro))], 32)


def _pos_alvo(alvo, f, dz=1.6):
    if isinstance(alvo, Boneco):
        bpy.context.scene.frame_set(f)
        p = alvo.root.matrix_world.translation
        return Vector((p.x, p.y, p.z + dz))
    if hasattr(alvo, "matrix_world"):
        bpy.context.scene.frame_set(f)
        p = alvo.matrix_world.translation
        return Vector((p.x, p.y, p.z + dz))
    return Vector(alvo)


def cam_perto(alvo, f0, f1, distancia=4.5, altura=1.7, angulo=-90, empurrar=0.75, lente=40):
    """CLOSE na altura dos olhos: alvo = boneco (segue o rosto) ou (x,y,z). angulo -90 = de frente.
    Vai se aproximando devagar (empurrar = fracao final da distancia)."""
    cam, alvo_obj = _cam()
    cam.data.lens = lente
    a = math.radians(angulo)
    for f in list(range(f0, f1 + 1, 6)) + [f1]:
        t = (f - f0) / max(1, f1 - f0)
        p = _pos_alvo(alvo, f)
        d = distancia * (1 - (1 - empurrar) * t)
        cam.location = (p.x + math.cos(a) * d, p.y + math.sin(a) * d, p.z - 1.6 + altura)
        cam.keyframe_insert("location", frame=f)
        alvo_obj.location = p
        alvo_obj.keyframe_insert("location", frame=f)
    return cam


def cam_baixa(alvo, f0, f1, distancia=6, angulo=-100, lente=28):
    """Camera baixa olhando para cima (deixa o alvo imponente). Gira um pouco."""
    cam, alvo_obj = _cam()
    cam.data.lens = lente
    for f in list(range(f0, f1 + 1, 6)) + [f1]:
        t = (f - f0) / max(1, f1 - f0)
        p = _pos_alvo(alvo, f, dz=2.0)
        a = math.radians(angulo + 20 * t)
        cam.location = (p.x + math.cos(a) * distancia, p.y + math.sin(a) * distancia, 0.5)
        cam.keyframe_insert("location", frame=f)
        alvo_obj.location = p
        alvo_obj.keyframe_insert("location", frame=f)
    return cam


def cam_ombro(boneco, alvo, f0, f1, lente=35):
    """Por cima do ombro do boneco, olhando para o alvo (outro boneco ou (x,y,z))."""
    cam, alvo_obj = _cam()
    cam.data.lens = lente
    for f in list(range(f0, f1 + 1, 6)) + [f1]:
        a = _pos_alvo(boneco, f)
        b = _pos_alvo(alvo, f)
        d = (b - a)
        d.z = 0
        d = d.normalized() if d.length else Vector((0, 1, 0))
        lado = Vector((d.y, -d.x, 0))
        cam.location = a - d * 4.2 + lado * 1.9 + Vector((0, 0, 0.9))
        cam.keyframe_insert("location", frame=f)
        alvo_obj.location = b
        alvo_obj.keyframe_insert("location", frame=f)
    return cam


def piscar_luzes(f0, f1, seed=3):
    """Luzes falhando (efeito de terror): sol, postes, holofotes e ceu piscam entre f0 e f1."""
    r = random.Random(seed)
    alvos = [(l, "energy", l.energy) for l in bpy.data.lights]
    bg = next((nd for nd in bpy.context.scene.world.node_tree.nodes if nd.type == "BACKGROUND"), None)
    if bg is not None:
        alvos.append((bg.inputs[1], "default_value", bg.inputs[1].default_value))
    for obj, prop, base in alvos:   # antes de comecar a piscar, luz normal
        setattr(obj, prop, base)
        obj.keyframe_insert(prop, frame=max(0, f0 - 1))
    f = f0
    while f <= f1:
        ligado = r.random() > 0.4
        nivel = 1.0 if ligado else r.uniform(0.02, 0.15)
        for obj, prop, base in alvos:
            setattr(obj, prop, base * nivel)
            obj.keyframe_insert(prop, frame=f)
        f += r.choice([2, 2, 3, 4, 6, 9, 14])
    for obj, prop, base in alvos:
        setattr(obj, prop, base)
        obj.keyframe_insert(prop, frame=f1 + 1)
    datas = list(bpy.data.lights) + [bpy.context.scene.world.node_tree]
    for d in datas:
        ad = getattr(d, "animation_data", None)
        if ad and ad.action:
            for fc in getattr(ad.action, "fcurves", []):
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"


def tremer_camera(f0, f1, forca=0.25):
    """Tremida de camera (explosao, susto, impacto)."""
    cam, _ = _cam()
    for f in range(f0, f1 + 1, 2):
        k = 1 - (f - f0) / max(1, f1 - f0)
        cam.delta_location = (_rng.uniform(-1, 1) * forca * k, _rng.uniform(-1, 1) * forca * k, _rng.uniform(-1, 1) * forca * k)
        cam.keyframe_insert("delta_location", frame=f)
    cam.delta_location = (0, 0, 0)
    cam.keyframe_insert("delta_location", frame=f1 + 1)


# ================================================================== pecas extras
def texto3d(texto, pos, tamanho=1.5, cor="#ffffff", rot=0, pai=None, extrusao=0.12, de_pe=True):
    """Texto 3D (letreiros, placas). de_pe=True fica em pe virado para -Y."""
    cu = bpy.data.curves.new("Txt", "FONT")
    cu.body = texto
    cu.size = tamanho
    cu.extrude = extrusao
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    ob = _link(bpy.data.objects.new("Txt", cu))
    ob.data.materials.append(mat(cor))
    ob.location = pos
    ob.rotation_euler = (math.radians(90) if de_pe else 0, 0, math.radians(rot))
    if pai:
        ob.parent = pai
    return ob


LIMPAR = True  # render_cena esconde objetos colados na camera; cenarios internos desligam isso
TEXTURAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "texturas")


def contorno(espessura=2.4):
    """Contorno preto estilo desenho (Freestyle)."""
    sc = bpy.context.scene
    sc.render.use_freestyle = True
    sc.render.line_thickness = espessura
    vl = bpy.context.view_layer
    vl.use_freestyle = True
    fs = vl.freestyle_settings
    if not fs.linesets:
        fs.linesets.new("Contorno")
    ls = fs.linesets[0]
    if ls.linestyle is None:
        ls.linestyle = bpy.data.linestyles.new("Preto")
    ls.linestyle.color = (0.02, 0.02, 0.03)
    ls.linestyle.thickness = espessura
    ls.select_silhouette = True
    ls.select_border = True
    ls.select_crease = True
    fs.crease_angle = math.radians(125)


def quadro_imagem(arquivo, pos, largura, altura, rot=(90, 0, 0), emissao=0.0, pai=None, nitido=False):
    """Plano com uma imagem. rot em graus: (90,0,0) = em pe virado para -Y; (0,0,0) = deitado; (90,0,90) = virado para +X."""
    caminho = arquivo if os.path.isabs(arquivo) else os.path.join(TEXTURAS, arquivo)
    bm = bmesh.new()
    vs = [bm.verts.new((sx * largura / 2, sy * altura / 2, 0)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    face = bm.faces.new(vs)
    uv = bm.loops.layers.uv.new()
    for loop, (u, v) in zip(face.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop[uv].uv = (u, v)
    m = bpy.data.materials.new("Img")
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    p.inputs["Roughness"].default_value = 0.9
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(caminho, check_existing=True)
    if nitido:
        tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], p.inputs["Base Color"])
    if emissao:
        nt.links.new(tex.outputs["Color"], p.inputs["Emission Color"])
        p.inputs["Emission Strength"].default_value = emissao
    return _malha("Quadro", bm, "#ffffff", pai, pos, tuple(math.radians(a) for a in rot), material=m)


def _luz_ponto(pos, energia, cor="#fff1d0", pai=None):
    ld = bpy.data.lights.new("Luz", "POINT")
    ld.energy = energia
    ld.color = hexrgb(cor)
    ld.shadow_soft_size = 0.4
    ob = _link(bpy.data.objects.new("Luz", ld))
    ob.location = pos
    if pai:
        ob.parent = pai
    return ob


def _texto_luminoso(texto, pos, tamanho, cor, pai):
    t = texto3d(texto, pos, tamanho, cor, pai=pai, extrusao=0.02)
    t.data.materials[0] = mat(cor, emissao=5)
    return t


def hall_predio(andar_social="1", andar_final=None, f_troca=None, porta_social=None, interfone_pisca=None,
                fone_caido=None, monitor="vazio", teto=True):
    """Hall de predio antigo (x de -6 a 6, y de -5 a 7, frente aberta para a camera em -Y).
    Balcao em x 0.5..4.5, y 0..0.9 (porteiro fica em (2.5, 1.4)); folha (1.3, 0.42), radio (2.1, 0.3),
    monitor (3.7, 0.5); elevador social em x=-2.5 e de servico em x=2.5 (parede do fundo, y=7);
    painel de interfone na parede esquerda (x=-6, y=1).
    porta_social=(f_abre, f_fecha): porta do elevador social abre e fecha (f_abre<=1 = ja aberta).
    andar_final + f_troca: o visor troca de numero. interfone_pisca=(f0, f1). fone_caido=f: fone cai e balanca.
    monitor: 'vazio' | 'porta' | 'crianca'."""
    global LIMPAR
    LIMPAR = False
    g = grupo("Hall")
    parede, rodape = "#b9b29f", "#5a4636"
    caixa((12, 12, 0.2), (0, 1, -0.1), "#2a2a2e", g, nome="Chao_hall")
    quadro_imagem("piso.png", (0, 1, 0.012), 12, 12, rot=(0, 0, 0), pai=g, nitido=True)
    # paredes laterais
    for x in (-6.15, 6.15):
        caixa((0.3, 12, 3.6), (x, 1, 1.8), parede, g)
        caixa((0.34, 12, 0.25), (x, 1, 0.125), rodape, g)
    # parede do fundo com dois vaos de elevador (x -3.6..-1.4 e 1.4..3.6)
    for x0, x1 in ((-6, -3.6), (-1.4, 1.4), (3.6, 6)):
        caixa((x1 - x0, 0.3, 3.6), ((x0 + x1) / 2, 7.15, 1.8), parede, g)
        caixa((x1 - x0, 0.34, 0.25), ((x0 + x1) / 2, 7.13, 0.125), rodape, g)
    for cx in (-2.5, 2.5):
        caixa((2.2, 0.3, 1.2), (cx, 7.15, 3.0), parede, g)           # verga
        caixa((2.5, 0.12, 0.14), (cx, 6.96, 2.45), "#6d6f73", g)      # moldura de cima
        for dx in (-1.17, 1.17):
            caixa((0.14, 0.12, 2.45), (cx + dx, 6.96, 1.22), "#6d6f73", g)
        # cabine atras da porta
        caixa((2.2, 2.0, 0.1), (cx, 8.1, 0.0), "#4a4a50", g)
        caixa((2.2, 0.1, 2.5), (cx, 9.05, 1.25), "#8d8a80", g)
        for dx in (-1.1, 1.1):
            caixa((0.1, 2.0, 2.5), (cx + dx, 8.1, 1.25), "#7d7a70", g)
        caixa((2.2, 2.0, 0.1), (cx, 8.1, 2.5), "#55555a", g)
        caixa((0.5, 0.06, 0.32), (cx, 6.93, 2.78), "#111114", g)      # visor
    # portas: servico fechada; social animavel
    for dx in (-0.55, 0.55):
        caixa((1.1, 0.08, 2.4), (2.5 + dx, 7.02, 1.2), "#9aa0a6", g, material=mat("#9aa0a6", rug=0.4, metal=0.6))
    folhas = []
    for dx in (-0.55, 0.55):
        f = caixa((1.1, 0.08, 2.4), (-2.5 + dx, 7.02, 1.2), "#9aa0a6", g, material=mat("#9aa0a6", rug=0.4, metal=0.6))
        folhas.append((f, dx))
    if porta_social:
        f_abre, f_fecha = porta_social
        for f, dx in folhas:
            fechada, aberta = -2.5 + dx, -2.5 + dx * 2.85
            if f_abre <= 1:
                f.location.x = aberta
                f.keyframe_insert("location", frame=1)
            else:
                for fr, x in ((1, fechada), (f_abre, fechada), (f_abre + 22, aberta)):
                    f.location.x = x
                    f.keyframe_insert("location", frame=fr)
            for fr, x in ((f_fecha, aberta), (f_fecha + 22, fechada)):
                f.location.x = x
                f.keyframe_insert("location", frame=fr)
        _luz_ponto((-2.5, 8.0, 2.2), 120, "#fff6dd", g)
    _texto_luminoso("T", (2.5, 6.89, 2.78), 0.26, "#ff3a2a", g)
    v1 = _texto_luminoso(andar_social, (-2.5, 6.89, 2.78), 0.26, "#ff3a2a", g)
    if andar_final and f_troca:
        v2 = _texto_luminoso(andar_final, (-2.5, 6.89, 2.78), 0.26, "#ff3a2a", g)
        _escala_keys(v1, [(f_troca - 1, 1), (f_troca, 0.0001)])
        _escala_keys(v2, [(f_troca - 1, 0.0001), (f_troca, 1)])
    # relogio de parede
    cilindro(0.38, 0.06, (0, 6.97, 2.7), "#f2efe6", 20, pai=g, rot=(math.pi / 2, 0, 0))
    caixa((0.03, 0.02, 0.26), (0, 6.9, 2.8), "#111111", g)
    caixa((0.2, 0.02, 0.03), (0.08, 6.9, 2.7), "#111111", g)
    # balcao
    caixa((4.0, 0.9, 1.0), (2.5, 0.45, 0.5), "#6b4a2f", g)
    caixa((4.2, 1.05, 0.07), (2.5, 0.45, 1.03), "#4d3420", g)
    quadro_imagem("folha.png", (1.3, 0.42, 1.072), 0.5, 0.7, rot=(0, 0, 0), pai=g)
    caixa((0.16, 0.09, 0.3), (2.1, 0.3, 1.22), "#1c1c20", g)                    # radio
    caixa((0.02, 0.02, 0.28), (2.15, 0.3, 1.5), "#1c1c20", g)
    esfera(0.025, (2.06, 0.25, 1.33), "#35ff5a", pai=g, material=mat("#35ff5a", emissao=8))
    caixa((0.95, 0.1, 0.68), (3.7, 0.56, 1.5), "#1b1b1f", g)                    # monitor
    caixa((0.12, 0.12, 0.16), (3.7, 0.58, 1.13), "#1b1b1f", g)
    quadro_imagem(f"cftv_{monitor}.png", (3.7, 0.505, 1.5), 0.86, 0.6, rot=(90, 0, 0), emissao=1.6, pai=g)
    _luz_ponto((3.7, 0.1, 1.5), 12, "#cfe0ff", g)
    # painel de interfone na parede esquerda
    caixa((0.08, 1.3, 1.5), (-5.96, 1.0, 1.55), "#3a3d44", g)
    especial = None
    for lin in range(6):
        for col in range(3):
            y, z = 1.35 - col * 0.3, 2.1 - lin * 0.2
            if lin == 3 and col == 1:
                especial = caixa((0.04, 0.12, 0.09), (-5.9, y, z), "#ff2b2b", g, material=mat("#ff2b2b", emissao=0.3))
            else:
                caixa((0.04, 0.12, 0.09), (-5.9, y, z), "#c9c4b4", g)
    if interfone_pisca and especial is not None:
        f0, f1 = interfone_pisca
        aceso = mat("#ff2b2b", emissao=14)
        luz = _luz_ponto((-5.5, 1.05, 1.5), 0, "#ff3030", g)
        for fr in range(f0, f1 + 1, 6):
            on = ((fr - f0) // 6) % 2 == 0
            luz.data.energy = 40 if on else 0
            luz.data.keyframe_insert("energy", frame=fr)
            especial.scale = (1, 1, 1) if on else (0.6, 0.8, 0.8)
            especial.keyframe_insert("scale", frame=fr)
        especial.data.materials[0] = aceso
        luz.data.keyframe_insert("energy", frame=f1 + 1)
    # fone: no gancho, ou caido balancando pelo fio
    if fone_caido is None:
        caixa((0.09, 0.12, 0.5), (-5.9, 0.15, 1.55), "#1c1c20", g)
    else:
        piv = grupo("Fone", (-5.9, 0.15, 1.75), pai=g)
        caixa((0.02, 0.02, 0.75), (0, 0, -0.37), "#101010", piv)
        caixa((0.09, 0.12, 0.5), (0, 0, -0.95), "#1c1c20", piv)
        f0 = max(1, fone_caido)
        for k in range(0, 40):
            fr = f0 + k * 7
            piv.rotation_euler = (math.radians(38 * math.exp(-k * 0.09) * math.cos(k * 1.1)), 0, 0)
            piv.keyframe_insert("rotation_euler", frame=fr)
        if fone_caido > 1:
            _escala_keys(piv, [(fone_caido - 1, 0.0001), (fone_caido, 1)])
            gancho = caixa((0.09, 0.12, 0.5), (-5.9, 0.15, 1.55), "#1c1c20", g)
            _escala_keys(gancho, [(fone_caido - 1, 1), (fone_caido, 0.0001)])
    # iluminacao: lampadas fluorescentes
    for x in (-2.8, 2.8):
        caixa((1.6, 0.14, 0.08), (x, 1.5, 3.5), "#f4f8ff", g, material=mat("#f4f8ff", emissao=6))
        _luz_ponto((x, 1.5, 3.2), 260, "#eaf2ff", g)
    _luz_ponto((0, 5.5, 3.0), 90, "#eaf2ff", g)
    _luz_ponto((0.5, -3.5, 2.6), 220, "#dfe8ff", g)   # preenche a frente do balcao
    if teto:
        caixa((12.6, 14.5, 0.2), (0, 2.0, 3.72), "#8f8a7c", g)
    return g


FILEIRAS_ONIBUS = (-4.6, -3.0, -1.4, 0.2, 1.8)


def assento(fileira, lado):
    """Posicao (x, y) de quem senta: fileira 0 (fundo) a 4 (frente); lado 'e' ou 'd'."""
    return (-0.8 if lado == "e" else 0.8, FILEIRAS_ONIBUS[fileira] + 0.05)


def onibus(painel="409", parar=None, partir=None, casa=False, celular=False):
    """Interior de onibus urbano a noite. Frente em +Y (motorista), fundo em -Y; x de -1.4 a 1.4; piso z=0; teto 2.45.
    Bancos em 5 fileiras (use M.assento(fileira, lado)); passageiros sentam com olhar=180 (virados para a frente).
    Motorista em (-0.7, 4.9). Porta na frente a direita (x=1.4, y de 3.6 a 4.8). Painel luminoso acima do para-brisa.
    painel: '409' | 'proxima' | 'rua'. parar=f: freia e para no quadro f. partir=f: volta a andar.
    casa=True: uma casa com luz acesa do lado direito (use com o onibus parado). celular=True: celular em close
    na frente do banco (1 d)."""
    global LIMPAR
    LIMPAR = False
    g = grupo("Onibus")
    corpo, banco, metal = "#d9d4c4", "#2f5fa8", "#e8c53a"
    caixa((2.9, 13.2, 0.1), (0, 0, -0.05), "#3a3c42", g, nome="Chao_onibus")
    caixa((0.7, 12.6, 0.012), (0, -0.1, 0.006), "#55585f", g)
    caixa((2.9, 13.2, 0.1), (0, 0, 2.5), "#cfcabb", g)                       # teto
    caixa((2.9, 0.1, 2.5), (0, -6.55, 1.25), corpo, g)                        # fundo
    caixa((2.9, 0.1, 1.0), (0, 6.55, 0.5), "#2b2d33", g)                      # painel do motorista
    caixa((2.9, 0.1, 0.5), (0, 6.55, 2.25), "#2b2d33", g)                     # faixa acima do para-brisa
    for sx in (-1, 1):
        x = sx * 1.42
        caixa((0.1, 13.2, 0.35), (x, 0, 2.3), corpo, g)                       # faixa de cima
        if sx == 1:   # lado direito tem o vao da porta (y 3.6..4.8)
            caixa((0.1, 10.1, 0.95), (x, -1.5, 0.475), corpo, g)
            caixa((0.1, 1.7, 0.95), (x, 5.7, 0.475), corpo, g)
        else:
            caixa((0.1, 13.2, 0.95), (x, 0, 0.475), corpo, g)
        for y in (-6.4, -4.8, -3.2, -1.6, 0.0, 1.6, 3.4, 5.0, 6.4):
            caixa((0.12, 0.14, 1.2), (x, y, 1.55), "#8f8a7c", g)              # colunas entre as janelas
    # bancos
    for y in FILEIRAS_ONIBUS:
        for x in (-0.8, 0.8):
            caixa((0.95, 0.5, 0.12), (x, y + 0.05, 0.5), banco, g)
            caixa((0.95, 0.1, 0.65), (x, y - 0.25, 0.85), banco, g)
            caixa((0.1, 0.1, 0.45), (x, y, 0.22), "#4a4d55", g)
            caixa((0.9, 0.04, 0.05), (x, y - 0.25, 1.2), metal, g)
    for y in (-3.8, -0.6, 2.6):
        for x in (-0.33, 0.33):
            cilindro(0.025, 2.45, (x, y, 0), metal, 8, pai=g)
    for x in (-0.33, 0.33):
        caixa((0.04, 11.5, 0.04), (x, -0.6, 2.2), metal, g)
    # motorista: banco, volante, divisoria, espelho
    caixa((0.7, 0.5, 0.12), (-0.7, 4.95, 0.5), "#22242a", g)
    caixa((0.7, 0.1, 0.8), (-0.7, 4.65, 0.95), "#22242a", g)
    cilindro(0.26, 0.04, (-0.7, 5.75, 1.05), "#111114", 16, pai=g, rot=(math.radians(60), 0, 0))
    caixa((0.05, 1.3, 1.3), (-0.2, 5.3, 0.65), "#6d7078", g)
    caixa((0.5, 0.04, 0.18), (0.1, 6.35, 1.95), "#9fb4c8", g, material=mat("#9fb4c8", rug=0.2, metal=0.9))
    quadro_imagem(f"painel_{painel}.png", (0, 6.48, 2.25), 2.2, 0.44, rot=(90, 0, 0), emissao=3.0, pai=g)
    # porta (duas folhas) na frente a direita
    for dy in (-0.3, 0.3):
        caixa((0.05, 0.56, 1.9), (1.42, 4.2 + dy, 0.95), "#7f858c", g)
    # luzes internas
    for y in (-4.5, -1.0, 2.5):
        caixa((0.16, 0.9, 0.04), (0, y, 2.43), "#e9fff0", g, material=mat("#e9fff0", emissao=2.5))
        _luz_ponto((0, y, 2.2), 70, "#dff5e6", g)
    _luz_ponto((0, 5.6, 2.0), 25, "#ffb060", g)
    if celular:
        x, y = assento(1, "d")
        caixa((0.36, 0.03, 0.66), (x, y + 0.75, 1.2), "#101014", g)
        quadro_imagem("celular_409.png", (x, y + 0.73, 1.2), 0.32, 0.59, rot=(90, 0, 0), emissao=2.2, pai=g)
        _luz_ponto((x, y + 0.4, 1.2), 6, "#bcd0ff", g)
    # lado de fora: estrada, postes e arvores passando para tras
    fora = grupo("Fora")
    caixa((60, 900, 0.1), (0, 0, -0.9), "#15161b", fora, nome="Chao_rua")
    for k in range(-25, 26):
        y = k * 16.0
        for sx in (-1, 1):
            cilindro(0.09, 5.5, (sx * 5.2, y + (4 if sx > 0 else 0), -0.85), "#2a2c33", 6, pai=fora)
            esfera(0.22, (sx * 4.6, y + (4 if sx > 0 else 0), 4.5), "#ffd9a0", sub=1, pai=fora,
                   material=mat("#ffd9a0", emissao=14))
        if k % 2 == 0:
            cilindro(1.6, 4.5, (-9.5, y + 7, -0.85), "#0f1a14", 6, raio_topo=0.0, pai=fora)
            cilindro(1.4, 4.0, (10.0, y + 11, -0.85), "#0f1a14", 6, raio_topo=0.0, pai=fora)
    v = 9.0 / FPS   # metros por quadro
    sc = bpy.context.scene
    fim = sc.frame_end
    if parar is None and partir is None and not casa:
        mover(fora, [(1, (0, 0, 0)), (fim, (0, -v * fim, 0))])
    elif parar is not None:
        y1 = -v * max(1, parar - 30)
        keys = [(1, (0, 0, 0)), (max(2, parar - 30), (0, y1, 0)), (parar, (0, y1 - v * 14, 0))]
        if partir is not None and partir > parar:
            keys += [(partir, (0, y1 - v * 14, 0)), (fim, (0, y1 - v * 14 - v * 0.6 * (fim - partir), 0))]
        else:
            keys += [(fim, (0, y1 - v * 14, 0))]
        mover(fora, keys)
    elif partir is not None:
        mover(fora, [(1, (0, 0, 0)), (partir, (0, 0, 0)), (fim, (0, -v * 0.6 * (fim - partir), 0))])
    fora["linear"] = True
    if casa:
        c = grupo("CasaFora", (7.5, 1.0, -0.85))
        caixa((5, 6, 3.4), (0, 0, 1.7), "#c9b79a", c)
        caixa((5.6, 6.6, 0.3), (0, 0, 3.55), "#6b3b2e", c)
        caixa((0.05, 1.1, 2.1), (-2.52, -1.4, 1.05), "#4a3020", c)                       # porta
        caixa((0.05, 1.5, 1.1), (-2.52, 1.2, 2.0), "#ffd27a", c, material=mat("#ffd27a", emissao=9))   # janela acesa
        _luz_ponto((-3.6, 0.0, 2.6), 320, "#ffcf8a", c)
    return g


def texto_chao(texto, x, y, tamanho=4.0, cor="#3a3a3a", rot=0):
    """Texto deitado no chao (ex: 'SOS' na areia, nome pintado no asfalto). Le-se de cima / da camera em -Y."""
    return texto3d(texto, (x, y, 0.06), tamanho, cor, rot, extrusao=0.15, de_pe=False)


def banco(x, y, rot=0, nome="BANCO"):
    g = grupo("Banco", (x, y), rot)
    caixa((16, 10, 0.8), (0, 0, 0.4), "#d8d2c4", g)
    caixa((14, 8, 7), (0, 1, 4.3), "#ece6d8", g)
    for i in range(6):
        cilindro(0.45, 6.2, (-6 + i * 2.4, -4.2, 0.8), "#f6f2ea", 12, pai=g)
    caixa((15, 3, 0.6), (0, -3.5, 7.3), "#e2dccd", g)
    tri = caixa((15, 3, 2.4), (0, -3.5, 8.3), "#e2dccd", g, rot=(math.radians(45), 0, 0))
    tri.scale = (1, 0.7, 0.7)
    caixa((3, 0.2, 4), (0, -3.0, 2.8), "#5b3a1e", g)
    texto3d(nome, (0, -5.05, 7.3), 1.0, "#2b2b2b", pai=g)
    return g


def cofre(x, y, rot=0, aberto=False):
    """Porta de cofre de banco (redonda)."""
    g = grupo("Cofre", (x, y), rot)
    caixa((7, 1, 7), (0, 0.5, 3.5), "#5f6670", g)
    porta = grupo("Porta", (0, -0.1, 3.5), pai=g)
    cilindro(2.8, 0.8, (0, 0, 0), "#9aa3ad", 24, pai=porta, rot=(math.pi / 2, 0, 0), material=mat("#9aa3ad", rug=0.35, metal=0.8))
    cilindro(0.5, 0.3, (0, -0.8, 0), "#c9a227", 12, pai=porta, rot=(math.pi / 2, 0, 0), material=mat("#c9a227", rug=0.3, metal=1))
    for a in range(0, 360, 60):
        caixa((0.12, 0.12, 1.4), (math.cos(math.radians(a)) * 0.7, -0.9, math.sin(math.radians(a)) * 0.7), "#c9a227", porta,
              rot=(0, -math.radians(a) + math.pi / 2, 0))
    if aberto:
        porta.rotation_euler.z = math.radians(-100)
    return g


def dinheiro(x, y, pilhas=6, z=0):
    """Pilhas de notas verdes."""
    g = grupo("Dinheiro", (x, y, z))
    for i in range(pilhas):
        dx, dy = (i % 3) * 0.75 - 0.75, (i // 3) * 0.42
        h = _rng.uniform(0.3, 0.7)
        caixa((0.7, 0.36, h), (dx, dy, h / 2), "#4f9a4a", g)
        caixa((0.72, 0.12, h + 0.01), (dx, dy, h / 2), "#e8e0b0", g)
    return g


def saco_dinheiro(x, y, z=0):
    g = grupo("Saco", (x, y, z))
    s = esfera(0.6, (0, 0, 0.55), "#b08a55", sub=2, pai=g)
    s.scale = (1, 1, 0.95)
    cilindro(0.18, 0.35, (0, 0, 1.05), "#9a7442", 8, pai=g)
    texto3d("$", (0, -0.6, 0.6), 0.6, "#2f6b2f", pai=g, extrusao=0.05)
    return g


def estrada(x, y, comp=200, rot=0, largura=10):
    g = grupo("Estrada", (x, y), rot)
    caixa((comp, largura, 0.06), (0, 0, 0.03), "#3a3d42", g)
    for i in range(int(comp / 6)):
        caixa((2.5, 0.25, 0.02), (-comp / 2 + i * 6, 0, 0.07), "#f2f2f2", g)
    return g


def poste(x, y, rot=0, ligado=False):
    g = grupo("Poste", (x, y), rot)
    cilindro(0.12, 6, (0, 0, 0), "#4a4f57", 6, pai=g)
    caixa((1.6, 0.25, 0.15), (0.7, 0, 6), "#4a4f57", g)
    caixa((0.6, 0.35, 0.15), (1.3, 0, 5.88), "#fff3c4", g, material=mat("#fff3c4", emissao=6 if ligado else 0.5))
    return g


def camera_seguranca(x, y, z=4, rot=0, varrer=None):
    """Camera de seguranca num suporte. varrer=(f0, f1) faz ela girar procurando."""
    g = grupo("CamSeg", (x, y, z), rot)
    caixa((0.15, 0.6, 0.15), (0, 0.3, 0), "#d0d0d0", g)
    corpo = grupo("Corpo", (0, 0, -0.1), pai=g)
    caixa((0.35, 0.8, 0.35), (0, -0.3, 0), "#f2f2f2", corpo)
    caixa((0.25, 0.05, 0.25), (0, -0.72, 0), "#15151a", corpo)
    esfera(0.06, (0.12, -0.74, 0.1), "#ff2b2b", pai=corpo, material=mat("#ff2b2b", emissao=8))
    if varrer:
        f0, f1 = varrer
        for f in range(f0, f1 + 1, 20):
            corpo.rotation_euler.z = math.radians(35 * math.sin((f - f0) / 20))
            corpo.keyframe_insert("rotation_euler", frame=f)
    return g


def carro_policia(x, y, rot=0, f0=1, f1=300):
    """Viatura com sirene piscando (vermelho/azul) entre f0 e f1."""
    g = carro(x, y, "#f2f2f2", rot)
    caixa((1.6, 2.05, 0.5), (0.2, 0, 0.75), "#1b2233", g)
    caixa((0.25, 0.05, 0.2), (-2.12, 0, 0.9), "#ffffff", g)
    luzes = []
    for dy, cor in ((-0.35, "#ff2020"), (0.35, "#2050ff")):
        l = caixa((0.5, 0.45, 0.25), (-0.2, dy, 2.08), cor, g, material=mat(cor, emissao=12))
        luzes.append(l)
    for i, l in enumerate(luzes):
        for f in range(f0, f1 + 1, 8):
            on = ((f - f0) // 8 + i) % 2 == 0
            l.scale = (1, 1, 1) if on else (0.6, 0.6, 0.6)
            l.keyframe_insert("scale", frame=f)
    return g


def celular(x, y, z=2, rot=0, tamanho=1.0, tela="#3aa0ff"):
    """Celular gigante (bom para explicar rastreamento, mensagens)."""
    g = grupo("Celular", (x, y, z), rot)
    caixa((1.0 * tamanho, 0.12 * tamanho, 2.0 * tamanho), (0, 0, 0), "#1b1b1f", g)
    caixa((0.86 * tamanho, 0.02, 1.7 * tamanho), (0, -0.07 * tamanho, 0.03 * tamanho), tela, g, material=mat(tela, emissao=2.5))
    return g


def monitor(x, y, z=0, rot=0, tela="#2a6fdb"):
    """Mesa com monitor (sala de controle, delegacia)."""
    g = grupo("Monitor", (x, y, z), rot)
    caixa((2.4, 1.2, 0.1), (0, 0, 1.0), "#8a6a4a", g)
    for dx in (-1.1, 1.1):
        caixa((0.1, 1.1, 1.0), (dx, 0, 0.5), "#6f5539", g)
    caixa((1.4, 0.08, 0.9), (0, 0.2, 1.65), "#1b1b1f", g)
    caixa((1.26, 0.02, 0.76), (0, 0.15, 1.65), tela, g, material=mat(tela, emissao=3))
    return g


def sinal(x, y, f0, f1, z=0.1, cor="#ff3b30", raio=12):
    """Ondas de sinal saindo de um ponto (GPS, radar, alarme)."""
    g = grupo("Sinal", (x, y, z))
    for k in range(3):
        anel = cilindro(1, 0.05, (0, 0, 0), cor, 32, pai=g, material=mat(cor, emissao=6))
        ini = f0 + k * 12
        for f in range(ini, f1 + 1, 36):
            _escala_keys(anel, [(f, 0.05), (f + 35, raio)], so_xy=True)
    return g


def mochila(x, y, z=0, cor="#2b2b2b"):
    g = grupo("Mochila", (x, y, z))
    caixa((0.7, 0.4, 0.9), (0, 0, 0.45), cor, g)
    caixa((0.55, 0.1, 0.4), (0, -0.25, 0.35), _clarear(cor, 1.4), g)
    return g


# ================================================================== final
_NAO_ESCONDER = ("Chao", "Grama", "Camada", "Mar", "Sol", "Fill", "Cam", "AlvoCam", "Rio", "Lago", "Estrada",
                 "K_", "Boneco_", "Explosao", "Sinal", "Spot", "Boom", "Txt", "Fogo")


def limpar_frente_camera(raio=3.2, passo=10):
    """Esconde objetos que ficam colados na camera em algum momento (arvore/predio tapando a tela)."""
    sc = bpy.context.scene
    cam = sc.camera
    if cam is None:
        return []
    raizes = [o for o in sc.objects if o.parent is None and not o.name.startswith(_NAO_ESCONDER)]
    escondidos = []
    for f in list(range(sc.frame_start, sc.frame_end + 1, passo)) + [sc.frame_end]:
        sc.frame_set(f)
        c = cam.matrix_world.translation
        for r in raizes:
            if r.hide_render:
                continue
            mn, mx = Vector((1e9,) * 3), Vector((-1e9,) * 3)
            for o in [r] + list(r.children_recursive):
                if o.type == "MESH":
                    for v in o.bound_box:
                        w = o.matrix_world @ Vector(v)
                        mn = Vector(map(min, mn, w))
                        mx = Vector(map(max, mx, w))
            if mn.x > mx.x or (mx.z - mn.z) < 0.5:  # sem malha ou objeto chato (piso)
                continue
            p = Vector((min(max(c.x, mn.x), mx.x), min(max(c.y, mn.y), mx.y), min(max(c.z, mn.z), mx.z)))
            if (p - c).length < raio:
                for o in [r] + list(r.children_recursive):
                    o.hide_render = True
                escondidos.append(r.name)
    return escondidos


def suavizar_tudo():
    for ob in bpy.data.objects:
        ad = ob.animation_data
        if not ad or not ad.action or ob.get("linear"):
            continue
        for fc in getattr(ad.action, "fcurves", []):
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"


def renderizar(pasta):
    sc = bpy.context.scene
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.filepath = pasta.rstrip("/\\") + "/f_"
    bpy.ops.render.render(animation=True)


def projetar_rotulos():
    """Posicao 2D (pixels) de cada rotulo em cada quadro."""
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    cam = sc.camera
    W, H = sc.render.resolution_x, sc.render.resolution_y
    saida = []
    for alvo, texto, f0, f1, dz in ROTULOS:
        pos = {}
        for f in range(sc.frame_start, sc.frame_end + 1):
            if f < f0 or (f1 and f > f1):
                continue
            sc.frame_set(f)
            if isinstance(alvo, Boneco):
                p = alvo.root.matrix_world.translation.copy()
                p.z += dz if dz is not None else 2.6
            elif hasattr(alvo, "matrix_world"):
                p = alvo.matrix_world.translation.copy()
                p.z += dz if dz is not None else _altura_grupo(alvo) + 1.5
            else:
                p = Vector(alvo)
                p.z += dz or 0
            v = world_to_camera_view(sc, cam, p)
            if v.z > 0 and -0.1 < v.x < 1.1 and -0.1 < v.y < 1.1:
                pos[f] = (round(v.x * W), round((1 - v.y) * H))
        saida.append({"texto": texto, "f0": f0, "pos": pos})
    return saida


def _altura_grupo(g):
    alt = 0.0
    for ob in g.children_recursive:
        if ob.type == "MESH":
            for c in ob.bound_box:
                w = ob.matrix_world @ Vector(c)
                alt = max(alt, w.z - g.matrix_world.translation.z)
    return alt
