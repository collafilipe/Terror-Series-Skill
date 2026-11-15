"""O RELOJOEIRO - Capitulo 1: "4h40". Roteiro em series/roteiros/o-relojoeiro-cap1.md.
VIDEO EM PRIMEIRA PESSOA: a camera sao os olhos do detetive Ramos (P.pov); ele nunca aparece, so as maos na ultima cena.
Campo de visao aberto (lente 18 a 24). Cenarios em blender/palacio.py (P).
Elenco em cena: br_coronel, br_primeira_dama, br_medica, br_secretario, br_copeira, br_cabo."""

FORA = ["chuva_forte", "vento", "trovoada"]          # debaixo de chuva / janela grande
DENTRO = ["chuva", "trovoada"]                       # chuva abafada dentro do palacio

PLANO = {
    "titulo": "O Relojoeiro - Cap. 1: 4h40",
    "rotulo": "O RELOJOEIRO · CAP. 1",
    "pergunta": "O QUE VOCÊ FAZ?",
    "opcao_a": "Mostro o livro ao coronel",
    "opcao_b": "Arranco a página",
    "legenda_post": ("O presidente está morto numa sala trancada por dentro. E a última assinatura na portaria é a minha. ⌚\n"
                     "A - Mostro o livro ao coronel\nB - Arranco a página\n\n"
                     "Comenta A ou B: o capítulo 2 é você que decide 👇\n\n"
                     "#suspense #terror #historiainterativa #detetive #animacao3d #fyp"),
    "cenas": [
        # 1 - gancho: o relogio parado na mao caida
        {"hud": "FALTAM 1H30", "amb": FORA,
         "linhas": [("som", "trovao"),
                    ("som", "tique_para"),
                    ("narrador", "O homem mais protegido do país está morto. E o relógio no pulso dele marca uma hora que ainda não *chegou*.")],
         "codigo": """
P.gabinete(raios=[T.get('trovao', 2) + 2, int(F*0.62)])
x, y, z = P.RELOGIO
M.camera([(1, (x, y - 0.34, z + 0.02)), (int(F*0.45), (x - 0.02, y - 0.42, z + 0.04)), (F, (x + 0.35, y - 1.2, z + 0.3))],
         [(1, (x, y, z)), (int(F*0.45), (x, y, z)), (F, (x - 0.05, y, z + 0.12))], lente=40)
"""},
        # 2 - a chegada: voce atravessa o portao debaixo de chuva
        {"hud": "03:10", "amb": FORA, "sons_em": [("anos", "trovao")],
         "linhas": [("fundo", "portao"),
                    ("fundo", "passos_agua"),
                    ("narrador", "Três e dez da madrugada. Chove sem parar. Você é o detetive Ramos, e há dois anos persegue um assassino que a imprensa chama de *Relojoeiro*.")],
         "codigo": """
P.patio(f_abre=T.get('portao', 8), raios=[T.get('trovao', int(F*0.6)) + 2])
P.pov([(1, (0, -8.5)), (F, (0, 11.5))], [(1, (0, 8, 2.4)), (F, (0, 27, 5.0))], lente=18, andando=[(1, F)])
"""},
        # 3 - a sala trancada
        {"hud": "FALTAM 1H27", "amb": DENTRO, "nota": "Sala trancada por dentro",
         "linhas": [("fundo", "passos_longos"),
                    ("narrador", "O coronel Brandão, chefe da segurança, te espera na porta do gabinete. Só avisa:"),
                    ("coronel", "Ninguém entrou nessa sala, detetive. E ninguém saiu."),
                    ("som", "macaneta"),
                    ("narrador", "A porta estava trancada por dentro. E a única chave estava no bolso do *presidente*."),
                    ("som", "lapis")],
         "codigo": """
P.corredor()
a, mc = T.get('l2', int(F*0.35)), T.get('macaneta', int(F*0.55))
c = M.Boneco('br_coronel', (-0.9, 14.6), olhar=15)
c.parado(1, F, 'parado', olhar=15)
rosto = (-0.9, 14.6, 1.47)
P.pov([(1, (0.2, 3.5)), (a - 10, (0.1, 13.2)), (mc - 6, (0.1, 13.3)), (mc + 16, (0.3, 14.7, 1.45)), (F, (0.3, 14.9, 1.42))],
      [(1, rosto), (mc - 6, rosto), (mc + 16, (0.0, 15.8, 1.25)), (F, (0.0, 15.8, 1.25))],
      lente=20, andando=[(1, a - 10)])
"""},
        # 4 - as cameras pularam sete minutos
        {"hud": "FALTAM 1H24", "amb": ["zumbido", "bipes"], "nota": "As câmeras perderam 7 minutos",
         "sons_em": [("pularam", "estatica")],
         "linhas": [("narrador", "Na sala de segurança, duzentas e doze câmeras. Nenhuma mostra alguém entrando. Mas você repara num detalhe: todas pularam os mesmos sete *minutos*."),
                    ("som", "lapis")],
         "codigo": """
p = T.get('p_pularam', int(F*0.6))
m = T.get('p_mas', int(F*0.45))
P.sala_cameras(f_pulo=p)
mx, my, mz = P.MONITOR
P.pov([(1, (-0.4, -2.7, 1.6)), (m, (-0.6, -0.4, 1.62)), (p - 6, (mx, 1.2, mz)), (F, (mx, 1.4, mz))],
      [(1, (0, 3, 1.75)), (m, (-0.3, 3, 1.75)), (p - 6, (mx, my, mz)), (F, (mx, my, mz))], lente=22, andando=[(1, m)])
"""},
        # 5 - a assinatura do Relojoeiro: voce se abaixa para ver o relogio
        {"hud": "FALTAM 1H22", "amb": FORA, "nota": "O relógio avisa: alguém morre às 4h40",
         "sons_em": [("perto", "tique_para")],
         "linhas": [("fundo", "rangido"),
                    ("narrador", "Você olha o relógio de perto. Não é dele. É a assinatura do Relojoeiro. Em cada vítima, ele deixa um relógio parado. E o relógio marca a hora da *próxima* morte. Esse marca quatro e quarenta."),
                    ("som", "lapis")],
         "codigo": """
P.gabinete(raios=[int(F*0.5)])
x, y, z = P.RELOGIO
a, b = T.get('p_nao', int(F*0.2)), T.get('p_esse', int(F*0.7))
P.pov([(1, (1.2, -1.6)), (a, (1.3, 0.9, 1.45)), (b - 14, (x + 0.25, y - 0.8, 0.95)), (b + 6, (x + 0.05, y - 0.4, z + 0.05)),
       (F, (x + 0.02, y - 0.35, z + 0.03))],
      [(1, (x, y, z + 0.3)), (a, (x, y, z + 0.1)), (b - 14, (x, y, z)), (b + 6, (x, y, z)), (F, (x, y, z))],
      lente=24, andando=[(1, a)])
"""},
        # 6 - o palacio fechado
        {"hud": "FALTAM 1H20", "amb": DENTRO, "nota": "O assassino está dentro do palácio",
         "linhas": [("narrador", "Você faz a conta. Falta uma hora e vinte. Então dá a ordem:"),
                    ("detetive", "Coronel, fecha o palácio. Ninguém entra, ninguém sai."),
                    ("som", "alarme"),
                    ("fundo", "portao"),
                    ("narrador", "E só depois você entende o que acabou de fazer. A próxima vítima está aqui dentro. E o assassino *também*."),
                    ("som", "lapis")],
         "codigo": """
al, po = T.get('alarme', int(F*0.45)), T.get('portao', int(F*0.5))
vt = T.get('p_assassino', int(F*0.8))
P.corredor(alerta=al, grade=(po, po + 45))
c = M.Boneco('br_coronel', (-0.2, 3.0), olhar=0)
c.parado(1, F, 'parado', olhar=0)
rosto = (-0.2, 3.0, 1.47)
P.pov([(1, (0.25, 1.3)), (al, (0.25, 1.45)), (po + 30, (0.7, 1.0)), (vt, (0.5, 1.0)), (F, (0.3, 1.4))],
      [(1, rosto), (al - 4, rosto), (al + 12, (0, 6, 3.3)), (po + 4, (0.6, 11, 2.6)), (po + 50, (0.6, 11, 1.7)),
       (vt - 12, (0.6, 11, 1.7)), (vt + 8, rosto), (F, rosto)], lente=20)
"""},
        # 7 - os suspeitos: voce olha um por um
        {"hud": "FALTAM 1H15", "amb": DENTRO + ["tique", "tensao"],
         "linhas": [("narrador", "No salão, seis pessoas. A primeira-dama. A médica. O secretário. A copeira. O guarda da porta. E o coronel. Um deles vai morrer. Um deles vai *matar*. A primeira-dama é a única que te encara, e pergunta:"),
                    ("primeira_dama", "O senhor acha que foi um de nós?")],
         "codigo": """
P.salao()
s = P.suspeitos(F)
nomes = ['primeiradama', 'medica', 'secretario', 'copeira', 'guarda', 'coronel']
ini = T.get('p_a', int(F*0.12))
marc = [T.get('p_' + n, int(F*(0.14 + 0.07*k))) for k, n in enumerate(nomes)]
um = T.get('p_um', int(F*0.6))
vol = T.get('p_unica', int(F*0.8))
def rosto(k):
    tipo, x = P.SUSPEITOS[k]
    return (x, P.Y_SUSPEITOS - abs(x) * 0.12, 1.47)
ck, ak = [(1, (0, -3.0, 1.56)), (ini - 8, (0, -2.4, 1.56))], [(1, (0, 5, 1.4)), (ini - 8, (0, 5, 1.4))]
for k, f in enumerate(marc):
    x, y, z = rosto(k)
    ck += [(f + 4, (x * 0.85, 3.1, 1.52))]
    ak += [(f + 4, (x, y, z))]
    prox = marc[k + 1] if k + 1 < len(marc) else um
    ck += [(prox - 5, (x * 0.85, 3.2, 1.52))]
    ak += [(prox - 5, (x, y, z))]
ck += [(um + 14, (0, -1.8, 1.56)), (vol - 12, (0, -1.6, 1.56)), (vol + 10, (-2.7, 3.1, 1.52)), (F, (-2.8, 3.3, 1.5))]
ak += [(um + 14, (0, 5, 1.4)), (vol - 12, (0, 5, 1.4)), (vol + 10, rosto(0)), (F, rosto(0))]
M.camera(ck, ak, lente=20)
"""},
        # 8 - a luz cai
        {"hud": "FALTAM 1H12", "amb": ["chuva_forte", "vento", "coracao", "tensao"], "nota": "A médica sumiu",
         "sons_em": [("sumiu", "impacto")],
         "linhas": [("som", "trovao"),
                    ("narrador", "Um trovão. A luz cai."),
                    ("som", "luz_cai"),
                    ("pausa", 0.5),
                    ("narrador", "Quando volta, você conta de novo. Cinco. A médica *sumiu*."),
                    ("som", "lapis")],
         "codigo": """
tr, lz, vt = T.get('trovao', 5), T.get('luz_cai', int(F*0.3)), T.get('l4', int(F*0.45))
P.salao(raios=[tr + 3, lz + 14])
P.suspeitos(F, some=('br_medica', lz + 8))
P.apagao(lz + 2, vt - 3, 0.03)
c = T.get('p_cinco', int(F*0.6))
M.camera([(1, (0, -2.0, 1.56)), (c, (0, -1.7, 1.56)), (c + 16, (-1.875, 2.0, 1.55)), (F, (-1.875, 2.4, 1.5))],
         [(1, (0, 5, 1.4)), (c, (0, 5, 1.4)), (c + 16, (-1.875, 4.8, 0.9)), (F, (-1.875, 4.8, 0.85))], lente=20)
M.tremer_camera(tr + 2, tr + 16, 0.03)
"""},
        # 9 - o livro da portaria: voce chega no balcao e se debruca
        {"hud": "FALTAM 1H08", "amb": DENTRO + ["coracao", "tensao"], "nota": "Alguém assinou o MEU nome às 1h52",
         "linhas": [("fundo", "passos_longos"),
                    ("narrador", "Você corre até a portaria pra ver quem entrou essa noite."),
                    ("som", "pagina"),
                    ("narrador", "A última assinatura antes do crime é de uma e cinquenta e dois. E o nome é o *seu*."),
                    ("som", "impacto"),
                    ("narrador", "Só que você só foi chamado às três."),
                    ("som", "lapis")],
         "codigo": """
P.portaria()
pg, im = T.get('pagina', int(F*0.3)), T.get('impacto', int(F*0.65))
lx, ly, lz = P.LIVRO
nx, ny, nz = P.LINHA
P.pov([(1, (-2.6, -2.7)), (pg - 14, (0, 0.45)), (pg + 8, (lx, ly - 0.36, 1.84)), (im - 14, (lx, ly - 0.34, 1.8)),
       (im, (nx, ny - 0.22, nz + 0.56)), (F, (nx, ny - 0.2, nz + 0.52))],
      [(1, (lx, ly, lz)), (pg - 14, (lx, ly, lz)), (pg + 8, (lx, ly, lz)), (im - 14, (lx, ly, lz)), (im, (nx, ny, nz)), (F, (nx, ny, nz))],
      lente=22, andando=[(1, pg - 14)])
M.tremer_camera(im, im + 14, 0.012)
"""},
        # 10 - o caderno: recapitulacao
        {"hud": "FALTAM 1H05", "amb": DENTRO + ["tique"], "caderno_cheio": True,
         "linhas": [("som", "pagina"),
                    ("narrador", "Você repassa o que sabe."),
                    ("narrador", "A sala estava trancada por dentro."),
                    ("narrador", "As câmeras perderam sete minutos."),
                    ("narrador", "O relógio avisa que alguém morre às quatro e quarenta."),
                    ("narrador", "O assassino está aqui dentro."),
                    ("narrador", "A médica sumiu."),
                    ("narrador", "E alguém assinou o seu nome antes de você *chegar*.")],
         "codigo": """
P.portaria()
lx, ly, lz = P.LIVRO
P.pov([(1, (0.1, 0.6, 1.7)), (F, (0.0, 0.7, 1.66))], [(1, (lx, ly + 0.2, lz)), (F, (lx, ly + 0.1, lz))], lente=22)
"""},
        # 11 - dilema: o livro na sua mao e o coronel vindo pelo corredor
        {"hud": "FALTAM 1H04", "amb": DENTRO + ["coracao", "tensao"],
         "linhas": [("fundo", "passos_chegando"),
                    ("narrador", "Passos no corredor. É o coronel, e você tem duas saídas. Opção A: mostrar o livro pra ele. É o certo a fazer, mas você vira o principal suspeito, e pode ser preso ali mesmo. Opção B: arrancar a página e esconder. Você ganha tempo pra investigar, mas, se alguém descobrir, vai parecer *culpado*. O que você faz? Comenta A ou B.")],
         "codigo": """
P.corredor()
P.maos_com_livro(0.3, 1.47, 1.05)
v = T.get('p_coronel', int(F*0.08))
c = M.Boneco('br_coronel', (-0.1, 14.5), olhar=0)
fim = T.get('card', int(F*0.3)) + 150
c.parado(1, v, 'parado', olhar=0)
c.caminho([(-0.1, 14.5), (-0.1, 3.6)], v, fim, 'andar')
c.parado(fim, F, 'parado', olhar=0)
P.pov([(1, (0.3, 1.0)), (F, (0.3, 1.0))],
      [(1, (0.3, 1.6, 0.92)), (v - 14, (0.3, 1.6, 0.92)), (v + 8, (-0.1, 9, 1.35)), (F, (-0.1, 7, 1.3))], lente=20)
"""},
    ],
}
