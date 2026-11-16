"""
Gerador de Shorts 3D low-poly (estilo "Voce construiu um presidio...", "Como escapar da Coreia do Norte").

Uso:
    .venv\\Scripts\\python.exe estudio\\gerar3d.py "Voce acabou de roubar um banco" [--voz thalita]

1) Claude Code escreve a historia (voce como protagonista, tensao crescente) e programa cada cena 3D
2) Narracao por cena (Edge TTS) + tratamento de audio
3) Blender monta e renderiza cada cena (GPU)
4) Etiquetas amarelas, numero gigante, barra de progresso, legenda, efeitos e musica
"""

import argparse
import json
import math
import random
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import historia_shorts as base  # noqa: E402
import animacao_shorts as anim  # noqa: E402

ROOT = base.ROOT
W, H, FPS, SR = 1080, 1920, 30, 44100
BLENDER = Path.home() / "Blender" / "blender-4.5.9-windows-x64" / "blender.exe"
RENDER = ROOT / "estudio" / "blender" / "render_cena.py"
OUT_DIR = ROOT / "estudio" / "videos3d"
FONT = str(base.FONT_FILE)

API = r"""
BIBLIOTECA 3D (objeto M). Metros, chao em z=0, X para a direita, Y para o fundo; a camera
"de frente" fica em -Y olhando para +Y. Boneco tem ~1,9 m. 30 quadros/s. A variavel F e o
numero total de quadros da cena - SEMPRE expresse tempos como fracao de F, ex: int(F*0.3).
Tudo que nao for boneco devolve um "grupo" animavel.

CENARIO (chame UM no inicio):
  M.ambiente(tipo)   'campo' | 'deserto' | 'neve' | 'cidade' | 'cidade_noite' | 'praia' | 'noite' | 'subsolo' | 'vazio'
                     'subsolo' = vista em CORTE do subsolo (parede de terra em y=0, terra para z<0)
  M.caixa((dx,dy,dz), (x,y,z), '#cor')    caixa generica (pos = centro). Ex. piso: M.caixa((40,40,0.05),(0,0,0.03),'#b9a27a')
  M.texto3d('TEXTO', (x,y,z), tamanho=1.5, cor='#ffffff', rot=0)   letreiro 3D em pe
  M.texto_chao('SOS', x, y, tamanho=4, cor='#3a3a3a', rot=0)        palavra escrita/deitada no chao (areia, asfalto)

PECAS (x,y = posicao no chao; rot em graus):
  Construcoes: M.cerca_reta(x,y,comp,rot)  M.cerca_quadrada(x,y,lado,farpado=False)  M.arame_farpado(x,y,comp,rot,z=2.7)
    M.muro_reto(x,y,comp,rot,altura=5)  M.muro_quadrado(x,y,lado,altura=5)  M.portao(x,y,largura=6,rot)  M.guarita(x,y,altura=7)
    M.cela(x,y,rot)  M.predio(x,y,w,d,h,cor=None)  M.casa(x,y,cor,telhado,rot)  M.banco(x,y,rot,nome='BANCO')
    M.cofre(x,y,rot,aberto=False)  M.ponte(x,y,comp,rot)  M.torre(x,y,altura)  M.bunker(x,y,rot)  M.piramide(x,y,lado)
    M.fosso(x,y,comp,largura,rot)  M.minas(x,y,area,n)  M.estrada(x,y,comp,rot,largura=10)  M.poste(x,y,rot,ligado=False)
  Natureza: M.arvore(x,y)  M.pinheiro(x,y)  M.cacto(x,y)  M.floresta(raio_min,raio_max,n)  M.montanha(x,y,raio,altura,neve)
    M.rio(x,y,comp,largura,rot)  M.lago(x,y,raio)
  Veiculos: M.carro(x,y,cor,rot)  M.carro_policia(x,y,rot,f0,f1) (sirene piscando)  M.caminhao(x,y,cor,rot)
    M.helicoptero(x,y,z,cor,f0,f1)  M.barco(x,y,cor,rot)  M.foguete(x,y)
  Objetos: M.dinheiro(x,y,pilhas=6,z=0)  M.saco_dinheiro(x,y,z=0)  M.mochila(x,y,z=0)  M.celular(x,y,z=2,rot,tamanho=1)
    M.monitor(x,y,z=0,rot)  M.camera_seguranca(x,y,z=4,rot,varrer=(f0,f1))  M.sinal(x,y,f0,f1,cor='#ff3b30',raio=12) (ondas de GPS/radar)
  M.bandeira(x,y,pais,altura=6,rot)  pais: brasil portugal eua russia alemanha franca italia japao china coreia_norte
    coreia_sul argentina espanha mexico reino_unido ucrania israel
  Subsolo: M.tunel(x0,x1,z=-4,altura=1.8)  M.poco(x,z_fundo=-4)     (com ambiente 'subsolo')
  Luz/efeito: M.holofote(x,y,z,alvo=(x,y,z))  M.explosao(x,y,f,raio=8,nuclear=False,cor='#ff8c1a') (cor muda: tinta '#d61f2b', fumaca '#9e9e9e')
    M.fogo(x,y,f0,f1,escala=1.0) (fogueira com chamas e luz; escala 2-4 = fogo grande)  M.fumaca(x,y,f0,f1,cor='#f2f2f2') (coluna subindo)

ANIMACAO DE PECAS:
  M.surgir(grupo, f, dur=14, modo='crescer'|'pop'|'cair')   aparece no quadro f (antes fica invisivel)
  M.sumir(grupo, f)   M.mover(grupo, [(f,(x,y,z)), ...])   M.girar(grupo, f0, f1, graus)
  M.rotulo(alvo, 'TEXTO', f0)   etiqueta amarela 2D que acompanha o alvo (grupo, boneco ou (x,y,z))

MODELOS 3D PRONTOS (bonitos, use SEMPRE que existir um adequado, no lugar das pecas simples):
  M.modelo(nome, x, y, rot=0, escala=1.0)   ja vem em tamanho real (predio ~12 m, casa ~6 m, carro ~4,5 m). Devolve grupo.
  {modelos}

BONECOS animados (estilo Minecraft/Roblox). tipos: preso (uniforme laranja) guarda policial ladrao ninja soldado
explorador cientista medico velho trabalhador civil homem turista mulher mulher2 crianca pirata zumbi robo robo2
presidente agente empresario monstro boneco_teste sobrevivente mendigo japonesa sem_rosto (manequim branco liso,
otimo para multidao sinistra) (+ rei e astronauta, mais simples)
  b = M.Boneco(tipo, (x,y), olhar=0)   olhar em graus (0 = virado para -Y/camera, 180 = de costas)
  b.caminho([(x,y),(x,y),...], f0, f1, acao='andar'|'correr', z=0)
  b.parado(f0, f1, acao, olhar=None)   acao: parado comemorar acenar sim nao susto apontar interagir pegar cavar
                                       cair (morre/desmaia) sentar lutar socar chutar dirigir segurar
  b.escalar(f0, f1, altura, olhar=180)    b.pular_para(f0, f1, (x,y,z))
  M.multidao(tipo, n, (xmin,xmax,ymin,ymax), f0, f1, acao='andar'|'correr'|'parado'|'comemorar'|'susto', seed=0,
             olhar_para=None)   olhar_para=(x,y): todos parados ENCARANDO esse ponto (otimo para terror)
  M.fila(tipo, n, (x,y), (x,y), f0, f1, acao='andar')
  Encadeie movimentos em intervalos diferentes (ex: 1..int(F*0.5) andar, int(F*0.5)..F parado).

CAMERA (chame exatamente UMA, SEMPRE NO FINAL do codigo, depois de animar os bonecos):
  M.cam_perto(alvo, f0, f1, distancia=4.5, altura=1.7, angulo=-90, empurrar=0.75)  CLOSE no rosto (alvo = boneco). angulo -90 = de frente, -60/-120 = 3/4
  M.cam_ombro(boneco, alvo, f0, f1)          por cima do ombro de um boneco olhando para o alvo (outro boneco/ponto)
  M.cam_baixa(alvo, f0, f1, distancia=6)     de baixo para cima (alvo imponente: muralha, policial, foguete)
  M.cam_seguir(boneco, f0, f1, distancia=8, altura=4)   acompanha um boneco correndo/andando
  M.cam_aerea(alvo=(x,y,z), distancia, altura, f0, f1, giro=25, aproximar=0.75)   visao geral girando e descendo
  M.cam_aproximar(alvo=(x,y,z), de=(x,y,z), para=(x,y,z), f0, f1)     voo reto
  M.cam_corte(x_centro, z_centro, f0, f1, largura=30)                  de lado mostrando o subsolo
  M.tremer_camera(f0, f1, forca=0.25)        tremida (use JUNTO com outra camera em momentos de impacto)
  M.piscar_luzes(f0, f1)                     luzes falhando/piscando (terror; chame depois do ambiente)
NUNCA coloque objeto grande (arvore, predio, rocha) entre a camera e o personagem nem a menos de 6 m da camera.
ENQUADRAMENTO (video vertical 9:16): a acao no centro. Close: distancia 3.5-6. Grupo de bonecos: 10-16.
Visao geral: cam_aerea distancia 40-70. Nao use bpy diretamente, nem import, nem arquivos.
"""

PROMPT = """Voce e roteirista e diretor 3D de um canal brasileiro de Shorts virais em 3D low-poly (bonecos quadradoes),
no estilo dos canais "Agora Eu Sei Como" e "Criador de Mundos". Os videos prendem porque contam uma HISTORIA com
voce (o espectador) como protagonista e revelam COMO AS COISAS FUNCIONAM DE VERDADE, passo a passo.
Tema: {tema}

ROTEIRO (portugues do Brasil falado, {n} cenas). O SEGREDO DA RETENCAO E A CURIOSIDADE: a pessoa precisa
QUERER SABER o que acontece depois, como resolver, e como aquilo funciona. Siga esta estrutura:

1) GANCHO (cena 1, no maximo 2 frases): situacao extrema + uma PROMESSA de revelacao que so sera paga no final.
   Ex: "Voce acordou numa ilha, sozinho, sem nada. E a maioria dos naufragos morre por um erro que parece esperto."
   (a pessoa fica para descobrir QUAL e o erro). Primeira frase com no maximo 9 palavras.
2) ESCADA DE PROBLEMAS (cenas do meio): cada cena e uma mini-historia:
   o que VOCE tenta -> por que da errado (consequencia concreta e visivel: sede, frio, ser pego, cair) ->
   a solucao esperta que funciona DE VERDADE e como ela funciona -> e a ultima frase ABRE o proximo problema
   ("so que agora...", "mas ai voce percebe...", "e e exatamente aqui que quase todo mundo erra").
   Use relogio para urgencia quando couber ("dia um", "hora seis", "faltam quarenta segundos").
3) VIRADA (penultima cena): paga a promessa do gancho com um fato real chocante (caso real, nome, ano).
4) FECHO (ultima): uma frase de impacto + pergunta que faz a pessoa se colocar no lugar ("E voce, teria ficado?").

ESTILO: amigo contando um segredo, presente do indicativo, "voce" o tempo todo, verbos de acao, detalhes concretos.
A informacao NUNCA vem como dica de lista; ela aparece como CONSEQUENCIA da historia.
PROIBIDO: "dica", "primeiro", "segundo", "passo", "neste video", "voce sabia", reticencias, comecar duas cenas
com a mesma palavra, frases genericas ("isso e muito importante").
Ritmo de Shorts: frases curtas (5 a 14 palavras) ligadas por virgula. Cada cena 12 a 24 palavras; total 140 a 175.
So fatos verdadeiros e verificaveis. Marque UMA palavra-chave por cena entre asteriscos: *jangada*.

EXEMPLO DO NIVEL ESPERADO (outro tema, so para mostrar o tom, NAO copie):
"Voce esta preso num submarino afundado, a cem metros. E o instinto que todo mundo tem aqui te mata."
"O manual manda esperar o resgate. Mas o gas carbonico sobe mais rapido que o socorro chega."
"Entao voce sai pelo tubo de torpedo, com um capuz que vira uma bolha de ar em volta da cabeca."
"E ai vem o instinto: prender a respiracao. Na subida o ar do pulmao expande, e se voce prender, ele rasga."
"O certo e o contrario, soltar o ar a subida inteira, gritando. E voce, teria coragem de subir?"

DIRECAO 3D (codigo Python para cada cena, usando SOMENTE a biblioteca abaixo):
- O desenho MOSTRA literalmente o que a frase diz.
- CENA 1 prende o olho no PRIMEIRO segundo: algo ja esta acontecendo no quadro 1 (alarme, explosao, perseguicao,
  boneco correndo, muralha surgindo) + M.tremer_camera(1, int(F*0.25)) + camera em movimento rapido (cam_perto com
  empurrar=0.55, ou cam_aproximar de longe para perto). Nada parado no comeco.
- Pelo menos METADE das cenas em CLOSE (M.cam_perto / M.cam_ombro) com o rosto do boneco mostrando a EMOCAO certa.
  As outras: visao geral (cam_aerea), cam_baixa, cam_seguir, cam_corte. Nunca a mesma camera duas cenas seguidas.
- O protagonista ("voce") e sempre o mesmo boneco (mesmo tipo e cor) em todas as cenas.
- Toda cena tem movimento: bonecos agindo e a novidade surgindo (M.surgir) no momento certo.
- No MAXIMO 1 M.rotulo() por cena, com 1 ou 2 palavras (ex: 'JANGADA'), e so quando ajuda a entender.
- Palavras escritas no mundo (SOS na areia, nome no chao): use M.texto_chao, nunca monte letras com pecas.
- Bonecos sempre de pe no chao (z=0), exceto quando escalam. Nada flutuando no ar.
- Momento de impacto (explosao, flagra, alarme): M.tremer_camera junto.
{api}

FORMATO DA RESPOSTA (exatamente assim, sem mais nada):
TITULO: titulo curioso (ate 60 caracteres)
DESCRICAO: descricao curta com 3 hashtags
PROTAGONISTA: tipo do boneco que e "voce" e como ele e (ex: sobrevivente barbudo de roupa rasgada)
=== CENA ===
TEXTO: frase narrada com *destaque*
```python
M.ambiente('cidade')
...
```
=== CENA ===
...
"""

PROMPT_SERIE_ROTEIRO = """Voce e roteirista e diretor 3D de uma SERIE INTERATIVA de suspense e terror em Shorts 3D
low-poly (bonecos quadradoes), no estilo "E SE...": cada video e um CAPITULO, termina num dilema A ou B, e o publico
vota nos comentarios qual caminho o protagonista ("voce") segue no proximo capitulo.

{contexto}

ROTEIRO DESTE CAPITULO (portugues do Brasil falado, {n} cenas):
1) ABERTURA (cena 1): se nao for o capitulo 1, comece lembrando em UMA frase curta o que o publico escolheu e
   jogue direto na consequencia ("Voces escolheram B. Voce finge ser cego, e funciona, por enquanto.").
   Se for o capitulo 1, apresente a premissa "E se..." em uma frase e por que ela e assustadora.
2) TENSAO CRESCENTE (cenas do meio): suspense e medo psicologico, nada de violencia explicita ou sangue.
   Detalhes que arrepiam (silencio, olhares, sons, algo fora do lugar), uma REGRA do mundo que e descoberta aos
   poucos, um personagem secundario misterioso, e cada cena termina abrindo uma pergunta ("so que...", "e ai voce
   percebe..."). Contagem de tempo quando couber ("tres e trinta e tres da manha", "dia dois").
3) REVELACAO (penultima cena): algo muda tudo e aumenta o perigo.
4) DILEMA (ultima cena): duas saidas, AMBAS arriscadas e tentadoras, e a pergunta direta "O que voce faz?".
   Nunca resolva o dilema; o capitulo acaba ali.
- Mantenha 100% de coerencia com os capitulos anteriores (nomes, regras do mundo, quem esta vivo, lugar).
- "Voce" o tempo todo, presente do indicativo, frases curtas (5 a 14 palavras), ritmo rapido, sem reticencias.
- Cada cena 12 a 24 palavras; total 150 a 185. Marque UMA palavra-chave por cena entre asteriscos: *janela*.
- Clima visual de terror (estilo dos canais de referencia):
  * CENA 1 abre num CLOSE EXTREMO no rosto do protagonista (M.cam_perto(prot, 1, F, distancia=2.2, empurrar=0.6)).
  * Multidoes sinistras: M.multidao('sem_rosto', ..., acao='parado', olhar_para=(x,y) do protagonista).
  * Planos com a camera ANDANDO junto do protagonista (prot.caminho(...) + M.cam_seguir(prot, ...)).
  * Em 1 ou 2 cenas de medo, luzes falhando: M.piscar_luzes(int(F*0.2), int(F*0.8)).
  * Prefira 'cidade_noite' ou 'noite', holofotes, cameras baixas e closes no rosto.
"""

PROMPT_SERIE_FORMATO_EXTRA = """
ALEM DO FORMATO ACIMA, logo depois da linha PROTAGONISTA escreva tambem estas linhas:
RESUMO: o que aconteceu neste capitulo em 2 frases (para manter a continuidade dos proximos)
PERGUNTA: a pergunta do dilema, curta, em CAIXA ALTA e COM ACENTOS (ex: VOCÊ ABRE A PORTA?)
(Na PERGUNTA, OPCOES, HUD e TEXTO escreva sempre em portugues correto, com acentos.)
OPCAO_A: opcao A em ate 5 palavras (ex: Abro a porta)
OPCAO_B: opcao B em ate 5 palavras (ex: Fujo pela janela)
E em cada cena, logo depois de TEXTO:, uma linha HUD: com um contador curto para o canto da tela que mude ao
longo do capitulo (ex: "DIA 1 · 03:33", "PESSOAS PARADAS: 1.204", "OLHANDO PRA VOCE: 12"), ou HUD: vazio.
"""


def prompt_serie(contexto, n, api):
    direcao = PROMPT[PROMPT.index("DIRECAO 3D"):]
    return (PROMPT_SERIE_ROTEIRO.format(contexto=contexto, n=n) + "\n" + direcao.replace("{api}", api)
            + PROMPT_SERIE_FORMATO_EXTRA)


FIX_PROMPT = """O codigo abaixo de uma cena 3D deu erro no Blender. Corrija usando SOMENTE a biblioteca M descrita.
{api}
Cena (narracao): {texto}
Codigo com erro:
```python
{codigo}
```
Erro:
{erro}
Responda SOMENTE com o codigo corrigido dentro de ```python ... ```."""

FALLBACK = """M.ambiente('campo')
M.multidao('civil', 10, (-12, 12, -12, 12), 1, F)
M.cam_aerea((0, 0, 0), 45, 30, 1, F)
"""


# ------------------------------------------------------------------ roteiro
def claude(prompt):
    base.config.app["claude_code_timeout"] = 900  # roteiro com codigo 3D demora mais
    return base.llm._generate_response(prompt, request_timeout=900) or ""


def parse_plano(raw):
    raw = raw.replace("\r", "")
    titulo = (re.search(r"TITULO:\s*(.+)", raw) or [None, ""])[1].strip()
    desc = (re.search(r"DESCRICAO:\s*(.+)", raw) or [None, ""])[1].strip()
    prot = (re.search(r"PROTAGONISTA:\s*(.+)", raw) or [None, ""])[1].strip()
    extra = {}
    cabeca = raw.split("=== CENA ===")[0]
    for chave in ("RESUMO", "PERGUNTA", "OPCAO_A", "OPCAO_B"):
        m = re.search(chave + r":\s*(.+)", cabeca)
        if m:
            extra[chave.lower()] = m.group(1).strip()
    cenas = []
    for bloco in raw.split("=== CENA ===")[1:]:
        texto = re.search(r"TEXTO:\s*(.+)", bloco)
        cod = re.search(r"```(?:python)?\n(.*?)```", bloco, re.S)
        if not texto or not cod:
            continue
        hud = re.search(r"HUD:[ \t]*(.*)", bloco)
        hud = (hud.group(1).strip().strip('"') if hud else "")
        if hud.lower() in ("vazio", "(vazio)", "-", "nenhum"):
            hud = ""
        partes = []
        for pedaco in (x.strip() for x in hud.split("·")):  # tira repeticoes (ex: "03:33 · 03:33")
            if pedaco and pedaco not in partes:
                partes.append(pedaco)
        hud = " · ".join(partes)
        cenas.append({"texto": texto.group(1).strip(), "numero": "", "hud": hud[:34], "codigo": cod.group(1)})
    return {"titulo": titulo, "descricao": desc, "protagonista": prot, "cenas": cenas, **extra}


MODELOS_SUGERIDOS = {
    "Cidade": ["building-a", "building-b", "building-c", "building-d", "building-e", "building-f", "building-g",
               "building-h", "building-skyscraper-a", "building-skyscraper-b", "building-skyscraper-c",
               "building-type-a", "building-type-c", "building-type-f", "building-type-k", "building-type-p",
               "fence-1x3", "planter", "tree-large", "tree-small", "detail-awning", "detail-parasol-a"],
    "Rua": ["road-straight", "road-crossroad", "road-intersection", "traffic-light", "light-square", "electricity-pole",
            "dumpster", "construction-barrier", "construction-cone", "road-sign-stop", "sign-highway", "bridge-pillar"],
    "Veiculos": ["police", "sedan", "suv", "taxi", "truck", "van", "ambulance", "firetruck", "garbage-truck",
                 "delivery", "tractor", "race", "hatchback-sports", "cone", "box", "debris-tire", "debris-door"],
    "Natureza": ["tree_default", "tree_oak", "tree_fat", "tree_tall", "tree_detailed", "rock_largeA", "rock_tallA",
                 "cliff_block_rock", "cliff_large_rock", "campfire_logs", "flower_redA", "plant_bush", "log", "stump_round"],
    "Interior": ["bedSingle", "bedBunk", "desk", "chair", "chairDesk", "table", "computerScreen", "laptop", "kitchenFridge",
                 "toilet", "bathtub", "televisionModern", "bookcaseOpen", "loungeSofa", "doorway", "wall", "wallWindow",
                 "stairs", "lampSquareFloor", "cardboardBoxClosed", "trashcan", "radio", "speaker"],
    "Sobrevivencia": ["barrel", "box-large", "chest", "tent", "campfire-pit", "workbench", "tool-shovel", "tool-pickaxe",
                      "tool-axe", "tool-hammer", "resource-wood", "rock-a", "fence-fortified", "structure-metal-wall",
                      "signpost", "bucket", "bottle"],
}


def lista_modelos():
    """So os nomes que existem de verdade na pasta kenney."""
    pasta = ROOT / "estudio" / "blender" / "kenney"
    existentes = {p.stem for p in pasta.rglob("*.glb")}
    linhas = []
    for grupo_nome, nomes in MODELOS_SUGERIDOS.items():
        ok = [n for n in nomes if n in existentes]
        if ok:
            linhas.append(f"  {grupo_nome}: " + " ".join(ok))
    return "\n".join(linhas) or "  (nenhum modelo instalado)"


def planejar(tema, n, contexto=None):
    api = API.replace("{modelos}", lista_modelos())
    for tentativa in range(3):
        prompt = prompt_serie(contexto, n, api) if contexto else PROMPT.format(tema=tema, n=n, api=api)
        plano = parse_plano(claude(prompt))
        if len(plano["cenas"]) >= 4 and (not contexto or (plano.get("opcao_a") and plano.get("opcao_b"))):
            return plano
        base.log(f"   roteiro incompleto (tentativa {tentativa + 1})")
    raise RuntimeError("o Claude Code nao devolveu um roteiro valido")


# ------------------------------------------------------------------ blender
def blender_cena(codigo, frames, pasta, seed, so_testar=False, extra=None):
    pasta.mkdir(parents=True, exist_ok=True)
    cfg = pasta / "cena.json"
    dados = {"codigo": codigo, "frames": frames, "saida": str(pasta), "seed": seed, "so_testar": so_testar}
    dados.update(extra or {})
    cfg.write_text(json.dumps(dados), encoding="utf-8")
    p = subprocess.run([str(BLENDER), "--background", "--factory-startup", "--python", str(RENDER), "--", str(cfg)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = p.stdout + p.stderr
    if "ERRO_CENA_INICIO" in out:
        return out.split("ERRO_CENA_INICIO")[1].split("ERRO_CENA_FIM")[0].strip()
    if so_testar and "TESTE_OK" in out:
        return None
    if not so_testar and "RENDER_OK" in out:
        return None
    return (out[-1500:] or f"blender saiu com codigo {p.returncode}")


def preparar_cena(cena, i, pasta, frames):
    """Testa o codigo; se der erro pede correcao ao Claude Code (ate 2x)."""
    codigo = cena["codigo"]
    for tentativa in range(3):
        erro = blender_cena(codigo, frames, pasta, seed=i + 1, so_testar=True)
        if not erro:
            return codigo
        base.log(f"   cena {i + 1}: erro no 3D, pedindo correcao ({tentativa + 1}) -> {erro.strip().splitlines()[-1][:120]}")
        if tentativa == 2:
            break
        resp = claude(FIX_PROMPT.format(api=API.replace("{modelos}", lista_modelos()), texto=cena["texto"],
                                        codigo=codigo, erro=erro[-1200:]))
        m = re.search(r"```(?:python)?\n(.*?)```", resp.replace("\r", ""), re.S)
        if m:
            codigo = m.group(1)
    base.log(f"   cena {i + 1}: usando cena reserva")
    return FALLBACK


REVISAO_PROMPT = """Voce e o diretor de fotografia de um Short vertical em 3D low-poly. Use a ferramenta Read para
ABRIR e OLHAR a imagem "revisao.png" desta pasta: sao 3 momentos da mesma cena (inicio, meio, fim), lado a lado.

Narracao desta cena: "{texto}"
Protagonista do video: {protagonista}

Confira com rigor (o video vai para o YouTube, erro visual faz a pessoa sair):
1. O protagonista/acao principal aparece INTEIRO e GRANDE (pelo menos 1/4 da altura do quadro), perto do centro,
   em pelo menos 2 dos 3 momentos. Nada cortado pela borda.
2. Nada tapando a camera (arvore, rocha, predio, fumaca na frente), nada flutuando no ar, nada atravessando outra coisa.
3. Da para ENTENDER o que a narracao diz so olhando (o objeto/acao citado esta visivel e destacado).
4. A cena nao esta vazia nem com o fundo dominando; o quadro e bonito e claro.

Se estiver tudo bom, responda exatamente: OK
Se houver problema, devolva o codigo COMPLETO corrigido (mesma biblioteca M) dentro de ```python ... ```,
ajustando camera (distancia, angulo, alvo), posicoes e o que for preciso. Nao explique.

Codigo atual da cena:
```python
{codigo}
```
{api}
"""


def claude_com_imagem(prompt, pasta):
    """Chama o Claude Code com permissao so de LER arquivos (para ele olhar a previa)."""
    cli = shutil.which("claude") or str(Path.home() / ".local" / "bin" / "claude.exe")
    env, _ = base.llm.build_claude_code_env()
    p = subprocess.run([cli, "-p", "--output-format", "json", "--allowedTools", "Read"], input=prompt, cwd=str(pasta),
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=900)
    try:
        return json.loads(p.stdout).get("result", "") or ""
    except json.JSONDecodeError:
        return p.stdout[-4000:]


def montar_previa(pasta):
    imgs = [Image.open(f).convert("RGB") for f in sorted(pasta.glob("f_*.png"))[:3]]
    if not imgs:
        return None
    w, h = imgs[0].size
    folha = Image.new("RGB", (w * len(imgs) + 20 * (len(imgs) - 1), h), (255, 255, 255))
    for k, im in enumerate(imgs):
        folha.paste(im, (k * (w + 20), 0))
    destino = pasta / "revisao.png"
    folha.save(destino)
    return destino


def revisar_cena(cena, i, pasta, frames, api, protagonista, rodadas=2):
    """Renderiza uma previa, o Claude Code olha e corrige o enquadramento se precisar."""
    codigo = cena["codigo"]
    for rodada in range(rodadas):
        prev = pasta / f"previa_{rodada}"
        if prev.exists():
            shutil.rmtree(prev)
        if blender_cena(codigo, frames, prev, seed=i + 1, extra={"amostra": 3, "percentual": 40}):
            return codigo
        if not montar_previa(prev):
            return codigo
        resp = claude_com_imagem(REVISAO_PROMPT.format(texto=cena["texto"].replace("*", ""), protagonista=protagonista,
                                                       codigo=codigo, api=api), prev)
        m = re.search(r"```(?:python)?\n(.*?)```", resp.replace("\r", ""), re.S)
        if not m:
            base.log(f"   cena {i + 1}: revisao visual OK")
            return codigo
        novo = m.group(1)
        if blender_cena(novo, frames, pasta / "teste_revisao", seed=i + 1, so_testar=True):
            base.log(f"   cena {i + 1}: correcao da revisao deu erro, mantendo a versao anterior")
            return codigo
        base.log(f"   cena {i + 1}: revisao visual corrigiu o enquadramento (rodada {rodada + 1})")
        codigo = novo
    return codigo


# ------------------------------------------------------------------ sobreposicoes
_fc = {}


def fonte(size):
    if size not in _fc:
        _fc[size] = ImageFont.truetype(FONT, size)
    return _fc[size]


def etiqueta(texto):
    """Etiqueta discreta (pequena) com setinha apontando para o objeto."""
    texto = texto[:22]
    f = fonte(40)
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, t, r, b = d0.textbbox((0, 0), texto, font=f, stroke_width=5)
    w, h = r - l + 14, b - t + 14
    im = Image.new("RGBA", (w, h + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((7 - l, 7 - t), texto, font=f, fill=(255, 212, 0), stroke_width=5, stroke_fill=(0, 0, 0))
    cx = w // 2
    d.polygon([(cx - 11, h - 2), (cx + 11, h - 2), (cx, h + 15)], fill=(255, 212, 0), outline=(0, 0, 0), width=3)
    return im


def titulo_img(titulo):
    """Titulo-gancho grande para os primeiros 2 segundos (1a linha amarela)."""
    palavras, linhas, atual = titulo.upper().split(), [], ""
    for p in palavras:
        if len(atual) + len(p) + 1 > 12 and atual:
            linhas.append(atual)
            atual = p
        else:
            atual = (atual + " " + p).strip()
    if atual:
        linhas.append(atual)
    linhas = linhas[:6]  # nao corta o titulo; se ficar grande, a fonte diminui
    f = fonte(104 if len(linhas) <= 4 else 84)
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    medidas = [d0.textbbox((0, 0), ln, font=f, stroke_width=11) for ln in linhas]
    w = max(b[2] - b[0] for b in medidas) + 40
    alt = sum(b[3] - b[1] + 14 for b in medidas) + 30
    im = Image.new("RGBA", (w, alt), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = 15
    for k, (ln, b) in enumerate(zip(linhas, medidas)):
        lw = b[2] - b[0]
        d.text(((w - lw) / 2 - b[0], y - b[1]), ln, font=f, fill=(255, 212, 0) if k == 0 else (255, 255, 255),
               stroke_width=11, stroke_fill=(0, 0, 0))
        y += b[3] - b[1] + 14
    if im.width > W - 80:  # nunca sai da tela
        k = (W - 80) / im.width
        im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    return im


def adicionar_frase_topo(ass_path, frases):
    """Frase inteira pequena no topo (como nos canais de referencia)."""
    txt = ass_path.read_text(encoding="utf-8")
    estilo = ("Style: Topo,Be Vietnam Pro,50,&H00FFFFFF,&H000000FF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,4,1,8,"
              "100,100,150,1")
    txt = txt.replace("\n\n[Events]", "\n" + estilo + "\n\n[Events]", 1)
    extra = "".join(f"Dialogue: 1,{base.ass_time(a)},{base.ass_time(b)},Topo,,0,0,0,,{t}\n" for a, b, t in frases)
    ass_path.write_text(txt + extra, encoding="utf-8")


def texto_simples(texto, tamanho, cor=(255, 255, 255), contorno=5):
    f = fonte(tamanho)
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, t, r, b = d0.textbbox((0, 0), texto, font=f, stroke_width=contorno)
    im = Image.new("RGBA", (r - l + 8, b - t + 8), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 - l, 4 - t), texto, font=f, fill=cor, stroke_width=contorno, stroke_fill=(0, 0, 0))
    return im


def caixa_opcao(letra, texto, cor):
    """Botao arredondado da opcao (A vermelho, B laranja)."""
    f = fonte(52)
    rotulo = f"{letra} - {texto.upper()}"
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, t, r, b = d0.textbbox((0, 0), rotulo, font=f)
    w = min(W - 80, max(620, r - l + 80))
    while r - l > w - 60 and f.size > 30:
        f = fonte(f.size - 4)
        l, t, r, b = d0.textbbox((0, 0), rotulo, font=f)
    h = 118
    im = Image.new("RGBA", (w + 12, h + 12), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([6, 10, w + 6, h + 10], radius=26, fill=(0, 0, 0, 150))
    d.rounded_rectangle([0, 0, w, h], radius=26, fill=cor, outline=(255, 255, 255), width=5)
    d.text(((w - (r - l)) / 2 - l, (h - (b - t)) / 2 - t), rotulo, font=f, fill=(255, 255, 255),
           stroke_width=3, stroke_fill=(0, 0, 0))
    return im


def compor(cenas_info, total_frames, saida_mp4, titulo="", serie=None, gf0=0):
    tit = None  # titulo gigante de abertura desativado a pedido (tampava a cena)
    DUR_TIT = 66
    hud_cache = {}
    card = None
    if serie:
        card = {
            "ini": total_frames - serie["card_frames"],
            "pergunta": texto_simples(serie["pergunta"].upper(), 74, (255, 212, 0), 8),
            "a": caixa_opcao("A", serie["a"], (214, 48, 49)),
            "b": caixa_opcao("B", serie["b"], (240, 128, 20)),
            "rodape": texto_simples("COMENTA A OU B", 46, (255, 255, 255), 5),
        }
        hud_titulo = texto_simples(serie["rotulo"], 32, (255, 255, 255), 4)
    enc = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", str(saida_mp4)],
        stdin=subprocess.PIPE)
    gf = gf0   # gf0 > 0: compondo so um trecho do video (gerar_drama --refazer)
    for info in cenas_info:
        rot = json.loads((info["pasta"] / "rotulos.json").read_text(encoding="utf-8"))
        etqs = [(r, etiqueta(r["texto"])) for r in rot[:1]]  # no maximo 1 etiqueta por cena
        num = None  # numeros gigantes desativados a pedido (poluiam a tela)
        for f in range(1, info["frames"] + 1):
            png = info["pasta"] / f"f_{f:04d}.png"
            frame = Image.open(png).convert("RGB") if png.exists() else Image.new("RGB", (W, H))
            ocupados = []  # caixas ja usadas neste quadro (evita etiquetas encavaladas)
            if num is not None:
                ocupados.append((W / 2, 560, num.width, num.height))  # etiquetas fogem do numero gigante
            for r, img in etqs:
                p = r["pos"].get(str(f))
                if not p:
                    continue
                k = min(1.0, (f - r["f0"]) / 6)
                s = anim.ease_out_back(max(0.0, k))
                x = min(max(p[0], img.width // 2 + 20), W - img.width // 2 - 20)
                y = p[1] - img.height / 2 - 10
                TOPO_LIVRE = 140  # margem de cima (barra de progresso e interface do app)
                for _ in range(6):
                    bate = [b for b in ocupados if abs(b[0] - x) < (b[2] + img.width) / 2 and abs(b[1] - y) < (b[3] + img.height) / 2]
                    if not bate:
                        break
                    y = min(b[1] for b in bate) - img.height - 4
                    if y - img.height / 2 < TOPO_LIVRE:  # sem espaco em cima: desce
                        y = max(b[1] for b in bate) + img.height + 4
                y = max(TOPO_LIVRE + img.height / 2, y)
                ocupados.append((x, y, img.width, img.height))
                anim.colar(frame, img, x, y, max(s, 0.01))
            if num is not None:
                s = anim.ease_out_back(min(1, f / 10)) * (1 + 0.03 * math.sin(f / 5))
                anim.colar(frame, num, W / 2, 560, s)
            if tit is not None and gf < DUR_TIT:
                s = anim.ease_out_back(min(1, gf / 7)) * (1 + 0.02 * math.sin(gf / 3))
                treme = 9 * max(0, 1 - gf / 20)
                a = min(1.0, (DUR_TIT - gf) / 8)
                anim.colar(frame, tit, W / 2 + treme * math.sin(gf * 2.1), 760 + treme * math.cos(gf * 1.7), s, 0, a)
            ov = info.get("overlay")
            if ov:   # desenho 2D proprio da cena (ex.: caderno do detetive)
                frame = ov(frame, f) or frame
            if serie:
                # placar discreto no canto (capitulo + contador da cena)
                frame.paste(hud_titulo, (46, 150), hud_titulo)
                hud = info.get("hud") or ""
                if hud:
                    if hud not in hud_cache:
                        hud_cache[hud] = texto_simples(hud.upper(), 44, (255, 212, 0), 5)
                    hi = hud_cache[hud]
                    frame.paste(hi, (46, 150 + hud_titulo.height + 4), hi)
                # tela de escolha A/B no final
                if card and gf >= card["ini"]:
                    k = gf - card["ini"]
                    escuro = Image.new("RGB", (W, H), (0, 0, 0))
                    frame = Image.blend(frame, escuro, min(0.45, k / 20))
                    at = serie.get("atrasos", (0, 8, 16, 24))
                    for atraso, chave, y in ((at[0], "pergunta", 700), (at[1], "a", 880), (at[2], "b", 1030), (at[3], "rodape", 1175)):
                        if k >= atraso:
                            p = min(1.0, (k - atraso) / 8)
                            s = anim.ease_out_back(p)
                            if chave in ("a", "b") and p >= 1:
                                s = 1 + 0.025 * math.sin((k + (0 if chave == "a" else 9)) / 4)
                            anim.colar(frame, card[chave], W / 2, y, max(s, 0.01))
            gf += 1
            ImageDraw.Draw(frame).rectangle([0, 0, int(W * gf / total_frames), 12], fill=(255, 212, 0))
            enc.stdin.write(frame.tobytes())
    enc.stdin.close()
    if enc.wait() != 0:
        raise RuntimeError("falha ao codificar")


def trilha_tensa(total, destino, seed=7, inicios=None, card_ini=None, cenas_pisca=()):
    """Trilha de suspense no estilo dos canais de referencia (medido no espectrograma deles):
    pulso grave a cada ~1 s o video inteiro, drone, tom agudo arrepiante no comeco, o pulso some antes
    da revelacao e volta com um BOOM, riser antes do dilema e impacto metalico na tela de escolha."""
    import numpy as np
    import wave
    n = int(total * SR) + SR
    t = np.arange(n) / SR
    rng = np.random.default_rng(seed)
    inicios = inicios or [0.0]
    card_ini = card_ini if card_ini is not None else total - 3.5
    revel = inicios[-2] if len(inicios) >= 3 else total * 0.7  # penultima cena = revelacao
    sinal = np.zeros(n)

    def add(ini, sig, amp=1.0):
        i = int(ini * SR)
        if i >= n or i < 0:
            return
        j = min(n, i + len(sig))
        sinal[i:j] += sig[: j - i] * amp

    # drone grave continuo (cresce ao longo do video)
    cresce = 0.6 + 0.4 * (t / max(total, 1))
    drone = (np.sin(2 * np.pi * 41.2 * t) * 0.5 + np.sin(2 * np.pi * 41.7 * t) * 0.35
             + np.sin(2 * np.pi * 61.7 * t) * 0.18 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * t)))
    sinal += drone * cresce * 0.55
    # pulso grave (kick escuro) a cada ~1 s, sumindo 2 s antes da revelacao
    Lk = int(0.45 * SR)
    tk = np.arange(Lk) / SR
    kick = np.sin(2 * np.pi * np.cumsum(np.linspace(62, 38, Lk)) / SR) * np.exp(-tk * 7)
    s = 0.25
    while s < card_ini:
        if not (revel - 2.0 <= s < revel):
            add(s, kick, 1.0)
        s += 1.0
    # tom agudo arrepiante (~880 Hz com tremolo) nos primeiros 20 s, bem baixo
    m = t < min(20, total)
    tom = np.sin(2 * np.pi * 880 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 5.5 * t)) * 0.035
    sinal += tom * m * np.clip((20 - t) / 4, 0, 1)
    # BOOM na revelacao (grave + ruido)
    Lb = int(1.6 * SR)
    tb = np.arange(Lb) / SR
    boom = (np.sin(2 * np.pi * np.cumsum(np.linspace(70, 30, Lb)) / SR) * np.exp(-tb * 2.5)
            + np.convolve(rng.normal(0, 1, Lb), np.ones(80) / 80, mode="same") * np.exp(-tb * 4) * 2.2)
    add(revel, boom, 1.6)
    # riser (ruido + tom subindo) nos 3 s antes da tela de escolha
    Lr = int(3.0 * SR)
    tr = np.arange(Lr) / SR
    ruido = rng.normal(0, 1, Lr)
    ruido = ruido - np.convolve(ruido, np.ones(20) / 20, mode="same")  # deixa agudo (chiado)
    riser = (ruido * 0.25 + np.sin(2 * np.pi * np.cumsum(np.linspace(200, 1400, Lr)) / SR) * 0.12) * (tr / 3.0) ** 2
    add(card_ini - 3.0, riser, 1.0)
    # impacto metalico (stinger) quando a tela A/B aparece
    Ls = int(2.5 * SR)
    ts = np.arange(Ls) / SR
    stinger = sum(np.sin(2 * np.pi * f * ts) * a for f, a in ((147, 0.6), (233, 0.4), (371, 0.3), (587, 0.2)))
    stinger = stinger * np.exp(-ts * 1.6) + np.sin(2 * np.pi * np.cumsum(np.linspace(60, 32, Ls)) / SR) * np.exp(-ts * 3)
    add(card_ini, stinger, 1.2)
    # zumbido eletrico nas cenas com luz piscando
    for ini, fim in cenas_pisca:
        L = int((fim - ini) * SR)
        if L <= 0:
            continue
        tz = np.arange(L) / SR
        zum = (np.sign(np.sin(2 * np.pi * 120 * tz)) * 0.04 + np.sin(2 * np.pi * 60 * tz) * 0.05)
        zum *= (rng.random(L) > 0.002).cumsum() % 2000 > 300  # falhas
        add(ini, zum, 1.0)
    sinal = sinal / (np.abs(sinal).max() + 1e-9) * 0.75
    fade = np.minimum(1, t / 0.4) * np.minimum(1, (total + 0.5 - t).clip(0) / 0.8)
    sinal = (sinal * fade).astype(np.float32)
    with wave.open(str(destino), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((sinal * 32767).astype(np.int16).tobytes())


# ------------------------------------------------------------------ principal
def main():
    ap = argparse.ArgumentParser(description="Gera um Short 3D low-poly.")
    ap.add_argument("tema")
    ap.add_argument("--cenas", type=int, default=9)
    ap.add_argument("--voz", default="antonio", help="antonio | thalita | andrew | brian | francisca")
    ap.add_argument("--velocidade", default="+30%")
    ap.add_argument("--musica", type=float, default=0.06)
    ap.add_argument("--plano", help="arquivo plano.json pronto (pula o Claude Code)")
    ap.add_argument("--sem-revisao", action="store_true", help="pula a revisao visual das cenas (mais rapido)")
    ap.add_argument("--contexto", help="arquivo de contexto de SERIE (usado pelo serie.py)")
    ap.add_argument("--serie-rotulo", default="", help="ex: 'E SE #1 · CAPITULO 2' (canto da tela)")
    ap.add_argument("--capitulo", type=int, default=1)
    ap.add_argument("--saida", help="pasta onde salvar (padrao: estudio/videos3d/...)")
    args = ap.parse_args()
    contexto = Path(args.contexto).read_text(encoding="utf-8") if args.contexto else None
    CARD = int(3.5 * FPS)  # segundos extras no fim para a tela de escolha
    if contexto:  # estilo das series de terror: locutor grave, palavra-chave vermelha
        base.PITCH = "-34Hz"
        base.COR_DESTAQUE = "&H002B2BFF&"
        if args.velocidade == "+30%":
            args.velocidade = "+18%"
    if not BLENDER.exists():
        raise SystemExit(f"Blender nao encontrado em {BLENDER}")
    base.VOICE = base.VOZES.get(args.voz, args.voz)

    t_ini = time.time()
    if args.plano:
        plano = json.loads(Path(args.plano).read_text(encoding="utf-8"))
    else:
        base.log("1/6 Claude Code escrevendo a historia e dirigindo as cenas 3D...")
        plano = planejar(args.tema, args.cenas, contexto)
    if args.saida:
        work = Path(args.saida)
    else:
        work = OUT_DIR / f"{time.strftime('%Y%m%d-%H%M%S')}-{base.slugify(plano.get('titulo') or args.tema)}"
    work.mkdir(parents=True, exist_ok=True)
    (work / "plano.json").write_text(json.dumps(plano, ensure_ascii=False, indent=2), encoding="utf-8")
    base.log(f"   titulo: {plano['titulo']} ({len(plano['cenas'])} cenas)")

    base.log(f"2/6 gravando a narracao (voz {base.VOICE})...")
    palavras, frames_cena, off = [], [], 0.0
    frases = []  # (inicio, fim, texto) para a legenda de cima
    linhas = []
    for i, c in enumerate(plano["cenas"]):
        destaque = {base.norm(x) for d in re.findall(r"\*([^*]+)\*", c["texto"]) for x in d.split()}
        mp3 = work / f"voz_{i:02d}.mp3"
        fala = c["texto"].replace("*", "").replace("...", ",").replace("…", ",")
        ws = base.tts(fala, mp3, args.velocidade)
        # corta o silencio do comeco e do fim usando o tempo exato das palavras
        ini = max(0.0, ws[0][0] - 0.04)
        fim = min(base.probe_duration(mp3), ws[-1][1] + 0.1)
        nf = int(math.ceil((fim - ini) * FPS))
        if contexto and i == len(plano["cenas"]) - 1:
            nf += CARD  # a ultima cena continua enquanto a tela de escolha aparece
        dur = nf / FPS
        wav = mp3.stem + ".wav"
        base.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{ini:.3f}", "-to", f"{fim:.3f}", "-i", mp3.name,
                  "-af", f"apad=whole_dur={dur:.3f}", "-t", f"{dur:.3f}", "-ar", str(SR), "-ac", "1", wav], cwd=work)
        linhas.append(f"file '{wav}'\n")
        for s, e, txt in ws:
            palavras.append({"start": off + s - ini, "end": off + e - ini, "text": txt, "cena": i,
                             "destaque": base.norm(txt) in destaque and base.norm(txt) != ""})
        frases.append((off, off + dur, fala))
        frames_cena.append(nf)
        off += dur
    total = off
    (work / "voz_lista.txt").write_text("".join(linhas), encoding="utf-8")
    base.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", "voz_lista.txt", "-c:a", "pcm_s16le",
              "narracao_bruta.wav"], cwd=work)
    base.run(["ffmpeg", "-y", "-v", "error", "-i", "narracao_bruta.wav", "-af", base.MASTER_VOZ, "-ar", str(SR),
              "-ac", "1", "-c:a", "pcm_s16le", "narracao.wav"], cwd=work)
    base.log(f"   narracao: {total:.1f}s")

    base.log("3/6 conferindo o codigo 3D de cada cena...")
    for i, c in enumerate(plano["cenas"]):
        c["codigo"] = preparar_cena(c, i, work / f"cena_{i:02d}", frames_cena[i])
    if not args.sem_revisao:
        base.log("3b/6 revisao visual: o Claude Code olha uma previa de cada cena e corrige...")
        api = API.replace("{modelos}", lista_modelos())
        prot = plano.get("protagonista") or "o personagem principal (voce)"
        for i, c in enumerate(plano["cenas"]):
            c["codigo"] = revisar_cena(c, i, work / f"cena_{i:02d}", frames_cena[i], api, prot)
    (work / "plano.json").write_text(json.dumps(plano, ensure_ascii=False, indent=2), encoding="utf-8")

    base.log("4/6 renderizando no Blender (GPU)...")
    infos = []
    for i, c in enumerate(plano["cenas"]):
        t0 = time.time()
        pasta = work / f"cena_{i:02d}"
        erro = blender_cena(c["codigo"], frames_cena[i], pasta, seed=i + 1)
        if erro:
            base.log(f"   cena {i + 1}: falhou no render, usando reserva")
            blender_cena(FALLBACK, frames_cena[i], pasta, seed=i + 1)
        base.log(f"   cena {i + 1}/{len(plano['cenas'])}: {frames_cena[i]} quadros em {time.time() - t0:.0f}s")
        hud_atual = c.get("hud") or (infos[-1]["hud"] if infos else "")
        infos.append({"pasta": pasta, "frames": frames_cena[i], "numero": c.get("numero", ""), "hud": hud_atual})

    base.log("5/6 etiquetas, legenda e sons...")
    serie_cfg = None
    if contexto:
        serie_cfg = {"rotulo": args.serie_rotulo or f"CAPITULO {args.capitulo}",
                     "pergunta": plano.get("pergunta") or "O QUE VOCE FAZ?",
                     "a": plano.get("opcao_a", "Opcao A"), "b": plano.get("opcao_b", "Opcao B"),
                     "card_frames": CARD + 15}
    compor(infos, sum(frames_cena), work / "visual.mp4", plano.get("titulo", ""), serie_cfg)
    inicios, acc = [], 0.0
    for nf in frames_cena:
        inicios.append(acc)
        acc += nf / FPS
    pops = []
    for info, ini in zip(infos, inicios):
        for r in json.loads((info["pasta"] / "rotulos.json").read_text(encoding="utf-8")):
            pops.append(ini + (r["f0"] - 1) / FPS)
    anim.salvar_wav(work / "sfx.wav", anim.sfx_track(total, inicios, pops, [0.0]))  # estrondo na abertura
    base.build_ass(palavras, work / "legendas.ass", y_pos=1480)  # so a legenda de baixo (frase do topo removida)
    (work / "fonts").mkdir(exist_ok=True)
    shutil.copy(base.FONT_FILE, work / "fonts" / base.FONT_FILE.name)

    base.log("6/6 juntando tudo...")
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", "visual.mp4", "-i", "narracao.wav", "-i", "sfx.wav"]
    songs = sorted(base.SONGS_DIR.glob("*.mp3"))
    if contexto:  # serie de terror: trilha de suspense propria (desenho de som estilo referencia)
        pisca = [(inicios[k], inicios[k] + frames_cena[k] / FPS) for k, c in enumerate(plano["cenas"])
                 if "piscar_luzes" in c.get("codigo", "")]
        trilha_tensa(total, work / "trilha.wav", inicios=inicios, card_ini=total - (CARD + 15) / FPS,
                     cenas_pisca=pisca)
        args.musica = 0.8
        cmd += ["-i", "trilha.wav"]
        songs = None
    if args.musica > 0 and songs:
        cmd += ["-stream_loop", "-1", "-i", str(random.choice(songs))]
    if args.musica > 0 and (songs or contexto):
        fc = (f"[0:v]subtitles=legendas.ass:fontsdir=fonts[v];[2:a]volume=0.4[s];"
              f"[3:a]volume={args.musica},afade=t=out:st={max(total - 2, 0):.2f}:d=2[m];"
              f"[1:a][s][m]amix=inputs=3:duration=first:normalize=0[a]")
    else:
        fc = "[0:v]subtitles=legendas.ass:fontsdir=fonts[v];[2:a]volume=0.4[s];[1:a][s]amix=inputs=2:duration=first:normalize=0[a]"
    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", f"{total:.2f}", "-c:v", "libx264", "-preset",
            "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "final.mp4"]
    base.run(cmd, cwd=work)
    if contexto:
        legenda = (f"{plano.get('pergunta', 'O QUE VOCE FAZ?').capitalize()}\n"
                   f"A - {plano.get('opcao_a', '')}\nB - {plano.get('opcao_b', '')}\n\n"
                   f"Comenta A ou B: o capítulo {args.capitulo + 1} é você que decide 👇\n\n"
                   "#ese #historiainterativa #suspense #terror #animacao3d #fyp")
        (work / "publicar.txt").write_text(
            f"TITULO:\n{plano['titulo']}\n\nLEGENDA DO POST (copie e cole):\n{legenda}\n\nROTEIRO:\n"
            + "\n".join(c["texto"].replace("*", "") for c in plano["cenas"]) + "\n", encoding="utf-8")
    else:
        (work / "publicar.txt").write_text(
            f"TITULO:\n{plano['titulo']}\n\nDESCRICAO:\n{plano['descricao']}\n\nROTEIRO:\n"
            + "\n".join(c["texto"].replace("*", "") for c in plano["cenas"]) + "\n", encoding="utf-8")
    for p in work.glob("cena_*/f_*.png"):
        p.unlink()
    for tmp in list(work.glob("voz_*")) + [work / "visual.mp4", work / "sfx.wav", work / "narracao_bruta.wav"]:
        tmp.unlink(missing_ok=True)
    base.log(f"PRONTO em {(time.time() - t_ini) / 60:.1f} min: {work / 'final.mp4'}")
    print(f"VIDEO_FILE={work / 'final.mp4'}")


if __name__ == "__main__":
    main()
