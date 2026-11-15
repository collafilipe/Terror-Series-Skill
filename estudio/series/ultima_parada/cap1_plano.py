"""ULTIMA PARADA - Capitulo 1: "Ainda sao seis". Roteiro em series/roteiros/ultima-parada-cap1.md."""

# passageiros sentados (tipo, fileira, lado); "voce" e o civil em (1, 'd')
OUTROS = "[('br_senhora', 1, 'e'), ('br_torcedor', 3, 'e'), ('br_moca', 4, 'd'), ('br_idoso', 3, 'd')]"
BASE = ("M.ambiente('interior')\n"
        "def senta(tp, fi, la, olhar=180):\n"
        "    b = M.Boneco(tp, M.assento(fi, la), olhar=olhar)\n"
        "    b.parado(1, F, 'sentar', olhar=olhar)\n"
        "    return b\n"
        "def mot():\n"
        "    m = M.Boneco('br_motorista', (-0.7, 4.95), olhar=180)\n"
        "    m.parado(1, F, 'sentar', olhar=180)\n"
        "VX, VY = M.assento(1, 'd')\n")
TODOS = "for tp, fi, la in " + OUTROS + ":\n    senta(tp, fi, la)\n"
AMB = ["motor", "chuva"]

PLANO = {
    "titulo": "Última Parada - Cap. 1: Ainda são seis",
    "rotulo": "ÚLTIMA PARADA · CAP. 1",
    "pergunta": "O QUE VOCÊ FAZ?",
    "opcao_a": "Desço na minha casa",
    "opcao_b": "Fico até o ponto final",
    "legenda_post": ("O motorista só disse uma coisa: não desce antes do ponto final. 🚌\n"
                     "A - Desço na minha casa\nB - Fico até o ponto final\n\n"
                     "Comenta A ou B: o capítulo 2 é você que decide 👇\n\n"
                     "#historiainterativa #terror #suspense #animacao3d #fyp"),
    "cenas": [
        # 1 - gancho: painel -> seu rosto
        {"hud": "01:12", "amb": AMB,
         "linhas": [("som", "campainha"),
                    ("narrador", "Esse ônibus não existe em nenhum aplicativo. E a próxima parada dele é a sua *casa*.")],
         "codigo": BASE + "M.onibus(painel='rua')\nmot()\n" + TODOS + "senta('br_voce', 1, 'd')\n"
                   "M.piscar_luzes(int(F*0.1), int(F*0.3))\n"
                   "M.camera([(1, (0, 3.9, 2.05)), (int(F*0.42), (0, 3.4, 2.0)), (int(F*0.7), (0.55, -1.2, 1.4)), (F, (0.6, -1.5, 1.38))],"
                   " [(1, (0, 6.4, 2.25)), (int(F*0.42), (0, 6.4, 2.25)), (int(F*0.7), (VX, VY, 1.32)), (F, (VX, VY, 1.32))], lente=32)\n"},
        # 2 - voce entra
        {"hud": "00:40", "amb": AMB,
         "linhas": [("narrador", "Meia-noite e quarenta. Você perdeu o último metrô, e o quatrocentos e nove é o único ônibus que ainda *passa*."),
                    ("idoso", "Não desce antes do ponto final.")],
         "codigo": BASE + "M.onibus()\nmot()\n" + TODOS + "senta('br_homem', 2, 'e')\n"
                   "v = M.Boneco('br_voce', (0.3, 4.3), olhar=0)\n"
                   "a = int(F*0.62)\n"
                   "v.caminho([(0.3, 4.3), (0, 3.2), (0, -2.3), (VX, VY)], 1, a, 'andar')\n"
                   "v.parado(a, F, 'sentar', olhar=180)\n"
                   "M.camera([(1, (-0.25, -6.1, 1.85)), (F, (-0.2, -5.4, 1.75))], [(1, (0, 2.5, 1.25)), (F, (0.3, 0, 1.2))], lente=24)\n"},
        # 3 - os passageiros
        {"hud": "00:47", "amb": AMB,
         "linhas": [("narrador", "Seis passageiros. Ninguém conversa, ninguém mexe no celular. Todo mundo olhando pra *frente*.")],
         "codigo": BASE + "M.onibus()\nmot()\n" + TODOS + "senta('br_homem', 2, 'e')\nsenta('br_voce', 1, 'd')\n"
                   "M.camera([(1, (0, 3.6, 1.55)), (F, (0, 2.3, 1.45))], [(1, (0, -3, 1.15)), (F, (0, -3, 1.15))], lente=26)\n"},
        # 4 - primeira parada: um homem desce
        {"hud": "00:52", "amb": AMB,
         "linhas": [("som", "campainha"),
                    ("mulher_radio", "Próxima parada."),
                    ("narrador", "A campainha toca sozinha. O ônibus para num ponto sem placa, no meio do *nada*."),
                    ("som", "freio"),
                    ("narrador", "Um homem levanta e desce, sem olhar pra trás.")],
         "codigo": BASE + "p = T.get('freio', int(F*0.55))\n"
                   "M.onibus(painel='proxima', parar=p)\nmot()\n" + TODOS + "senta('br_voce', 1, 'd')\n"
                   "h = M.Boneco('br_homem', M.assento(2, 'e'), olhar=180)\n"
                   "h.parado(1, p, 'sentar', olhar=180)\n"
                   "h.caminho([M.assento(2, 'e'), (0, -1.2), (0, 3.9), (1.15, 4.2)], p + 5, F, 'andar')\n"
                   "M.camera([(1, (0.0, -3.55, 1.8)), (F, (0.0, -3.1, 1.75))], [(1, (0.3, 1.5, 1.2)), (F, (0.5, 2.5, 1.2))], lente=26)\n"},
        # 5 - ainda sao seis
        {"hud": "00:54", "amb": AMB,
         "linhas": [("narrador", "A porta fecha, o ônibus anda. E você conta de novo. Seis. Ainda são *seis*.")],
         "codigo": BASE + "M.onibus(partir=15)\nmot()\n" + TODOS +
                   "senta('br_trocado', 2, 'e')\nsenta('br_voce', 1, 'd')\n"
                   "M.piscar_luzes(int(F*0.55), int(F*0.8))\n"
                   "M.camera([(1, (0.0, 1.2, 1.5)), (F, (0.0, -0.1, 1.45))], [(1, (0.0, -2.6, 1.2)), (F, (0.5, -2.9, 1.28))], lente=28)\n"},
        # 6 - o celular
        {"hud": "01:03", "amb": AMB,
         "linhas": [("narrador", "Você abre o mapa. A linha quatrocentos e nove foi desativada em dois mil e *onze*. E o seu celular diz que você ainda está parado no ponto.")],
         "codigo": BASE + "M.onibus(celular=True)\nmot()\n" + TODOS + "senta('br_trocado', 2, 'e')\n"
                   "M.camera([(1, (VX, VY + 0.05, 1.3)), (F, (VX, VY + 0.22, 1.24))], [(1, (VX, VY + 0.75, 1.2)), (F, (VX, VY + 0.75, 1.2))], lente=32)\n"},
        # 7 - a senhora
        {"hud": "01:07", "amb": AMB,
         "linhas": [("idosa", "Eles não descem, meu filho. Eles são trocados."),
                    ("jovem", "Trocados pelo quê?"),
                    ("idosa", "Quando a campainha tocar pra você, não levanta.")],
         "codigo": BASE + "M.onibus()\nmot()\n"
                   "for tp, fi, la in [('br_torcedor', 3, 'e'), ('br_moca', 4, 'd')]:\n    senta(tp, fi, la)\n"
                   "senta('br_trocado', 2, 'e')\nsenta('br_senhora', 1, 'e', 150)\nsenta('br_voce', 1, 'd')\n"
                   "SX, SY = M.assento(1, 'e')\n"
                   "M.camera([(1, (-0.2, SY + 1.3, 1.42)), (F, (-0.3, SY + 1.1, 1.4))], [(1, (SX, SY, 1.3)), (F, (SX, SY, 1.3))], lente=30)\n"},
        # 8 - a sua parada: todos viram
        {"hud": "01:11", "amb": AMB + ["coracao"],
         "linhas": [("som", "campainha"),
                    ("mulher_radio", "Próxima parada. Rua das Acácias, cinquenta e oito."),
                    ("narrador", "É o seu *endereço*."),
                    ("som", "impacto"),
                    ("narrador", "E todos os passageiros viram pra você, ao mesmo tempo.")],
         "codigo": BASE + "M.onibus(painel='rua')\nmot()\n"
                   "v = T.get('impacto', int(F*0.6))\n"
                   "for tp, fi, la in [('br_senhora', 1, 'e'), ('br_torcedor', 3, 'e'), ('br_moca', 4, 'd'), ('br_trocado', 2, 'e')]:\n"
                   "    x, y = M.assento(fi, la)\n"
                   "    b = M.Boneco(tp, (x, y), olhar=180)\n"
                   "    b.parado(1, v, 'sentar', olhar=180)\n"
                   "    b.root.rotation_euler[2] = math.radians(math.degrees(math.atan2(VY - y, VX - x)) + 90)\n"
                   "    b.root.keyframe_insert('rotation_euler', frame=v + 7)\n"
                   "a = T.get('l2', int(F*0.45))\n"
                   "M.camera([(1, (0, 3.8, 2.05)), (a - 6, (0, 3.5, 2.02)), (a + 8, (0.7, -2.6, 1.5)), (F, (0.6, -2.3, 1.45))],"
                   " [(1, (0, 6.4, 2.25)), (a - 6, (0, 6.4, 2.25)), (a + 8, (-0.15, 0.6, 1.15)), (F, (-0.15, 0.6, 1.15))], lente=26)\n"
                   "M.tremer_camera(v, v + 20, 0.05)\n"},
        # 9 - a sua casa
        {"hud": "01:12", "amb": ["chuva", "coracao"],
         "linhas": [("som", "freio"),
                    ("narrador", "O ônibus para na frente da sua casa. A luz está acesa. E tem alguém parado na porta, olhando pro ônibus. É *você*.")],
         "codigo": BASE + "M.onibus(painel='rua', casa=True)\nmot()\n"
                   "senta('br_voce', 1, 'd')\n"
                   "d = M.Boneco('br_voce', (4.6, -0.4, -0.85), olhar=-90)\nd.parado(1, F, 'acenar', olhar=-90)\n"
                   "M.camera([(1, (-0.9, -2.4, 1.55)), (F, (-0.2, -1.9, 1.5))], [(1, (4.6, -0.4, 0.5)), (F, (4.6, -0.4, 0.45))], lente=30)\n"},
        # 10 - dilema
        {"hud": "01:13", "amb": ["chuva", "coracao"],
         "linhas": [("idoso", "O ponto final ainda tá longe, rapaz."),
                    ("narrador", "A porta abre. O motorista te olha pelo espelho. O que você *faz*?")],
         "codigo": BASE + "M.onibus(painel='rua', casa=True)\nmot()\n"
                   "for tp, fi, la in [('br_senhora', 1, 'e'), ('br_torcedor', 3, 'e'), ('br_moca', 4, 'd'), ('br_trocado', 2, 'e')]:\n"
                   "    x, y = M.assento(fi, la)\n"
                   "    senta(tp, fi, la, math.degrees(math.atan2(VY - y, VX - x)) + 90)\n"
                   "senta('br_voce', 1, 'd')\n"
                   "M.camera([(1, (-0.3, -6.1, 2.1)), (F, (-0.1, -5.0, 1.95))], [(1, (0.5, 0.5, 1.1)), (F, (0.6, -1.5, 1.2))], lente=24)\n"},
    ],
}
