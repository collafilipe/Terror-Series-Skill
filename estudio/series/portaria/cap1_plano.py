"""PORTARIA DA NOITE - Capitulo 1: "O 704 nao existe". Dirigido a mao (roteiro em series/roteiros)."""

CAIO = "c = M.Boneco('civil', (2.5, 1.4))\nc.parado(1, F, 'parado')\n"
AMB = ["chuva", "zumbido", "tique"]

PLANO = {
    "titulo": "Portaria da Noite - Cap. 1: O 704 não existe",
    "rotulo": "PORTARIA DA NOITE · CAP. 1",
    "pergunta": "VOCÊ SOBE?",
    "opcao_a": "Subo até o 7º andar",
    "opcao_b": "Fico falando com ela",
    "legenda_post": ("A segunda regra estava sublinhada duas vezes. E o interfone tocou mesmo assim. 📞\n"
                     "Você subia?\nA - Subo até o 7º andar\nB - Fico e continuo falando com ela\n\n"
                     "Comenta A ou B: o capítulo 2 é você que decide 👇\n\n"
                     "#historiainterativa #terror #suspense #animacao3d #fyp"),
    "cenas": [
        # 1 - gancho: monitor -> rosto
        {"hud": "03:07", "amb": ["zumbido", "ronco"],
         "linhas": [("som", "estatica"),
                    ("narrador", "Tem um apartamento nesse prédio que não está na lista de moradores. E hoje, ele *ligou* pra você.")],
         "codigo": "M.ambiente('interior')\nM.hall_predio(monitor='porta')\n" + CAIO +
                   "M.piscar_luzes(1, int(F*0.25))\n"
                   "M.camera([(1, (3.7, -1.0, 1.5)), (int(F*0.4), (3.7, -0.75, 1.5)), (int(F*0.7), (2.7, -1.5, 1.75)), (F, (2.6, -1.2, 1.75))],"
                   " [(1, (3.7, 0.5, 1.5)), (int(F*0.4), (3.7, 0.5, 1.5)), (int(F*0.7), (2.5, 1.4, 1.7)), (F, (2.5, 1.4, 1.7))], lente=38)\n"},
        # 2 - chegada
        {"hud": "23:58", "amb": AMB + ["grilos"],
         "linhas": [("som", "passos"),
                    ("narrador", "Primeira noite como porteiro. O anterior foi embora sem avisar. Só deixou uma *folha*.")],
         "codigo": "M.ambiente('interior')\nM.hall_predio()\n"
                   "c = M.Boneco('civil', (-4, -3))\n"
                   "c.caminho([(-4, -3), (-0.5, 1.9), (2.5, 1.4)], 1, int(F*0.7), 'andar')\n"
                   "c.parado(int(F*0.7), F, 'parado', olhar=0)\n"
                   "M.camera([(1, (-1.5, -10, 1.1)), (F, (0.3, -5.5, 1.6))], [(1, (0, 3, 1.7)), (F, (1.5, 2, 1.5))], lente=28)\n"},
        # 3 - as regras
        {"hud": "23:59", "amb": AMB + ["grilos"],
         "linhas": [("narrador", "Três regras. A segunda está sublinhada *duas* vezes."),
                    ("jovem", "Que brincadeira é essa?")],
         "codigo": "M.ambiente('interior')\nM.hall_predio()\n" + CAIO +
                   "M.camera([(1, (1.3, 0.1, 2.5)), (F, (1.3, 0.25, 1.95))], [(1, (1.3, 0.42, 1.07)), (F, (1.3, 0.42, 1.07))], lente=45)\n"},
        # 4 - o radio
        {"hud": "00:41", "amb": AMB + ["grilos"],
         "linhas": [("som", "radio"),
                    ("idoso_radio", "Menino. Aqui é o Nestor, o síndico. Leu a folha?"),
                    ("jovem", "Li. Mas o setecentos e quatro nem aparece na lista."),
                    ("idoso_radio", "Por isso mesmo."),
                    ("som", "radio_fim"),
                    ("narrador", "Ele desliga antes de você perguntar *mais*.")],
         "codigo": "M.ambiente('interior')\nM.hall_predio()\n" + CAIO +
                   "a = T.get('l2', int(F*0.4))\n"
                   "M.camera([(1, (2.25, -1.4, 1.5)), (a - 10, (2.3, -1.15, 1.5)), (a + 12, (2.45, -1.4, 1.72)), (F, (2.5, -1.0, 1.72))],"
                   " [(1, (2.3, 0.6, 1.4)), (a - 10, (2.3, 0.6, 1.4)), (a + 12, (2.5, 1.4, 1.7)), (F, (2.5, 1.4, 1.7))], lente=40)\n"},
        # 5 - calmaria falsa
        {"hud": "01:30", "amb": AMB + ["grilos"],
         "linhas": [("pausa", 0.6),
                    ("narrador", "Uma e meia. Tudo quieto. Quieto *demais*."),
                    ("som", "grilo_para"),
                    ("pausa", 1.2)],
         "codigo": "M.ambiente('interior')\nM.hall_predio()\n" + CAIO +
                   "M.camera([(1, (0.6, -5.0, 1.75)), (F, (1.6, -3.4, 1.7))], [(1, (2.5, 1.4, 1.5)), (F, (2.5, 1.4, 1.5))], lente=32)\n"},
        # 6 - Dona Ivone
        {"hud": "02:15", "amb": ["chuva", "zumbido", "ronco"],
         "linhas": [("som", "elevador"),
                    ("idosa", "Boa noite, meu filho. Você é o novo?"),
                    ("jovem", "Sou sim, senhora. Precisa de alguma coisa?"),
                    ("idosa", "Só vim avisar. Quando ela ligar, seja educado."),
                    ("som", "porta"),
                    ("narrador", "A porta fecha. No painel, o elevador não sobe. Ele *desce*. E o prédio não tem subsolo.")],
         "codigo": "M.ambiente('interior')\n"
                   "ab, fe = T.get('elevador', 10) + 18, T.get('porta', int(F*0.6))\n"
                   "M.hall_predio(porta_social=(ab, fe), andar_final='-1', f_troca=fe + 45)\n"
                   "c = M.Boneco('civil', (2.5, 1.4), olhar=-143)\nc.parado(1, F, 'parado', olhar=-143)\n"
                   "iv = M.Boneco('mulher', (-2.5, 8.0))\niv.parado(1, F, 'parado')\n"
                   "p = T.get('l1', ab + 20)\n"
                   "M.camera([(1, (0.2, -2.6, 1.8)), (p + 40, (-0.3, -1.6, 1.75)), (p + 70, (-2.45, 4.3, 1.65)), (fe, (-2.45, 4.9, 1.65)), (fe + 40, (-2.3, 3.4, 2.0)), (F, (-2.4, 4.2, 2.5))],"
                   " [(1, (-2.5, 7.5, 1.5)), (fe, (-2.5, 8.0, 1.65)), (fe + 40, (-2.5, 7.0, 2.7)), (F, (-2.5, 7.0, 2.78))], lente=35)\n"},
        # 7 - o interfone
        {"hud": "03:07", "amb": ["zumbido"],
         "linhas": [("som", "silencio"),
                    ("som", "interfone"),
                    ("narrador", "Três e sete. O interfone toca. Não tem número no botão. Mas você sabe *qual* é.")],
         "codigo": "M.ambiente('interior')\nM.hall_predio(interfone_pisca=(T.get('interfone', 20), F))\n" + CAIO +
                   "M.piscar_luzes(T.get('interfone', 20), T.get('interfone', 20) + 50)\n"
                   "M.camera([(1, (-2.6, 1.05, 1.6)), (F, (-4.6, 1.05, 1.55))], [(1, (-5.9, 1.05, 1.55)), (F, (-5.9, 1.05, 1.5))], lente=35)\n"},
        # 8 - tentacao
        {"hud": "03:08", "amb": ["zumbido", "coracao"],
         "linhas": [("som", "interfone"),
                    ("narrador", "Toca nove vezes. Na décima, para. E o fone sai do gancho *sozinho*.")],
         "codigo": "M.ambiente('interior')\n"
                   "q = T.get('fim_falas', int(F*0.8)) - 25\n"
                   "M.hall_predio(interfone_pisca=(1, q - 20), fone_caido=q)\n"
                   "c = M.Boneco('civil', (-4.4, 1.3), olhar=-90)\nc.parado(1, F, 'interagir', olhar=-90)\n"
                   "M.camera([(1, (-2.4, -1.6, 0.7)), (F, (-2.9, -1.0, 0.8))], [(1, (-5.2, 0.9, 1.5)), (F, (-5.2, 0.7, 1.4))], lente=28)\n"},
        # 9 - a voz
        {"hud": "03:09", "amb": ["zumbido", "coracao"],
         "linhas": [("som", "estatica"),
                    ("crianca_interfone", "Moço. A minha mãe não acorda. Você pode subir?"),
                    ("jovem", "Qual é o seu apartamento?"),
                    ("crianca_interfone", "Você sabe qual é.")],
         "codigo": "M.ambiente('interior')\nM.hall_predio(fone_caido=1)\n"
                   "c = M.Boneco('civil', (-4.4, 2.0), olhar=-40)\nc.parado(1, F, 'nao', olhar=-40)\n"
                   "M.camera([(1, (-3.3, -1.9, 1.3)), (F, (-3.7, -1.4, 1.2))], [(1, (-5.5, 0.5, 1.05)), (F, (-5.5, 0.5, 1.05))], lente=30)\n"},
        # 10 - revelacao
        {"hud": "03:10", "amb": ["zumbido", "coracao", "ronco"],
         "linhas": [("som", "radio"),
                    ("idoso_radio", "Não sobe, menino! O último porteiro subiu. Ele ainda está lá."),
                    ("som", "impacto"),
                    ("narrador", "E a criança no interfone começa a *chorar*.")],
         "codigo": "M.ambiente('interior')\nM.hall_predio(monitor='crianca', fone_caido=1)\n"
                   "c = M.Boneco('civil', (-1.0, 0.4), olhar=90)\nc.parado(1, F, 'nao', olhar=90)\n"
                   "b = T.get('impacto', int(F*0.6))\n"
                   "M.camera([(1, (1.8, -1.3, 1.5)), (b - 35, (1.9, -1.1, 1.5)), (b - 8, (3.7, -0.85, 1.5)), (b + 30, (3.7, -0.6, 1.5)), (b + 55, (0.4, -0.9, 1.72)), (F, (0.2, -0.6, 1.72))],"
                   " [(1, (2.2, 0.3, 1.3)), (b - 35, (2.2, 0.3, 1.3)), (b - 8, (3.7, 0.5, 1.5)), (b + 30, (3.7, 0.5, 1.5)), (b + 55, (-1.0, 0.4, 1.7)), (F, (-1.0, 0.4, 1.7))], lente=38)\n"
                   "M.tremer_camera(b, b + 22, 0.06)\n"},
        # 11 - dilema
        {"hud": "03:11", "amb": ["zumbido", "coracao", "ronco"],
         "linhas": [("narrador", "Uma criança pedindo ajuda. E uma regra sublinhada duas vezes. O que você *faz*?")],
         "codigo": "M.ambiente('interior')\nM.hall_predio(porta_social=(1, F + 200), andar_social='7', fone_caido=1, teto=False)\n"
                   "c = M.Boneco('civil', (0, 2.2), olhar=0)\nc.parado(1, F, 'nao', olhar=0)\n"
                   "M.cam_aerea((0, 2.4, 1.0), 7.0, 5.5, 1, F, giro=60, aproximar=0.78, angulo_ini=-120)\n"},
    ],
}
