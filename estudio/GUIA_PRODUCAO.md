# Guia de produção das séries (o que já foi aprovado e o que evitar)

> **Referência de qualidade:** `series/ultima_parada/cap1/final.mp4` e o plano `series/ultima_parada/cap1_plano.py`.
> Todo capítulo novo deve seguir a mesma receita: história com uma regra revelada por cena, cenário próprio com
> contorno, vozes do ElevenLabs, som de ambiente baixo, prévias conferidas antes do render.
> O fluxo de aprovação com o usuário está na skill `serie-terror` (`~/.claude/skills/serie-terror/SKILL.md`).

Atualizado em 15/11/2026. Leia antes de produzir um capítulo novo.

## Formato aprovado
- Série de terror em capítulos, vertical 9:16, 90 a 110 s, terminando em escolha **A ou B** para o público votar.
- Referências de estilo: perfis `realidade_alternativabr` e `cenariosficticios` (Instagram). A história é sempre original.
- Estrutura: gancho forte na 1ª cena, regras do fenômeno descobertas aos poucos, revelação perto do fim, dilema final.
- O contexto tem que ficar claro: um lugar, um problema, quem é quem. O final precisa fazer sentido com o que foi mostrado.

## Voz (APROVADO)
- **ElevenLabs**, chave em `elevenlabs_key.txt`, vozes em `vozes_elevenlabs.json`.
- Narrador: **Brian**. Jovem: Liam. Idoso: Bill. Mulher madura: Lily. Criança/jovem aguda: Laura. Mulher: Sarah.
- Plano gratuito: 10.000 caracteres/mês (~1.100 por capítulo). O cache em `cache_vozes/` evita gastar duas vezes.
- Escrever números por extenso nas falas ("setecentos e quatro").
- REPROVADO: vozes do Edge (cara de IA), Edge acelerado ou com tom alterado, Chatterbox, OmniVoice/VoiceStudio
  (este último também tem licença não comercial).

## Som (APROVADO, com volume baixo)
- Sem música. Só ambiente e efeitos: chuva, zumbido, relógio, grilos que param, elevador, interfone, rádio, coração, impacto.
- Volumes em `gerar_drama.py`: `VOL_AMBIENTE = 0.3`, `VOL_EFEITO = 0.55`. O fundo alto foi reprovado.
- Personagens por rádio/interfone usam os filtros de `drama.py`.

## Visual
- APROVADO: cenários internos montados no Blender com **contorno preto** (`M.ambiente('interior')`), câmeras dirigidas
  cena a cena, objetos sincronizados com o som pelas marcas `T` (porta abre no "plim", visor troca etc.).
- APROVADO: placar pequeno no canto (nome da série + relógio), legenda do narrador branca com palavra-chave vermelha,
  falas dos personagens em amarelo, tela de escolha A/B no fim.
- REPROVADO: números gigantes, título gigante na abertura, legenda no topo, etiquetas amarelas grandes,
  objetos colados na câmera, bonecos flutuando, palavras montadas com peças (usar `M.texto_chao`/`M.texto3d`).
- A MELHORAR: modelo dos personagens (blocos Kenney parecem esquisitos) e os movimentos.

## Movimento dos personagens
- Gestos tocam UMA vez (já travado no código). A animação "idle" dos bonecos Kenney gira o corpo de um lado para o outro: "parado" agora usa pose firme com respiração leve. Não voltar para o idle.
  para o outro sem parar. Gesto toca UMA vez e depois o boneco fica parado respirando.
- Evitar câmera de lado no rosto dos bonecos Kenney: a lateral da cabeça parece um segundo rosto.

## Como produzir um capítulo
1. Escrever o roteiro em `series/roteiros/` e aprovar com o usuário ANTES de renderizar.
2. Criar o plano em `series/<serie>/capN_plano.py` (cenas, falas, sons, código 3D).
3. `gerar_drama.py <plano> --previa` e OLHAR a folha de prévias; corrigir câmeras; repetir só as cenas alteradas.
4. `gerar_drama.py <plano>` (render final, ~30 min). Ajuste só de som: `--so-audio` (não renderiza de novo).
5. Revisar 20 quadros do vídeo final antes de entregar. Avisar o que não foi verificado (o áudio não dá para ouvir).

## Séries
- `series/portaria/` — "Portaria da Noite" cap. 1: produção aprovada, mas a HISTÓRIA foi achada esquisita (final confuso).
- `series/as-3h33/` — formato antigo (gerador automático `serie.py`), substituído por este processo.
- `series/ultima_parada/` — "Última Parada" cap. 1 (ônibus 409), feito em 15/11/2026 com todo o processo acima:
  cenário `M.onibus()`, texturas em `blender/fazer_texturas_onibus.py`, sons novos (motor, campainha, freio).
  Render: 44 min para 93 s. Saldo ElevenLabs depois dele: 2.001 de 10.000. **APROVADO pelo usuário ("ficou muito bom"): este capítulo é o PADRÃO a repetir.**

## Lições do capítulo do ônibus
- Câmera dentro de cenário apertado: conferir na prévia se corrimão, banco ou passageiro tapa a frente.
- `piscar_luzes` precisa de uma chave de "luz normal" antes de começar (já corrigido), senão a cena abre escura.
- Para "todos viram ao mesmo tempo", girar o `root` do boneco com keyframe; não chamar `parado` duas vezes.
- Narrador mais estável: `stability 0.6`, `style 0.15` em `vozes_elevenlabs.json`.

## Correções pedidas depois da aprovação (15/11/2026)
- Erro grave corrigido em `mundo3d.py`: as tiras de animação usavam a propriedade errada e "vazavam" a pose para
  fora do intervalo (boneco andando em pose de sentado; boneco de pé no banco antes de levantar). O certo é
  `st.extrapolation` ("NOTHING" para animação em loop, "HOLD_FORWARD" para pose única).
- Personagem sentado SEMPRE de frente (olhar=180). De lado, o corpo atravessa o banco.
- A câmera fica no PROTAGONISTA. Figurante (manequim sem rosto etc.) aparece ao lado ou ao fundo, nunca em close.
- Câmera que anda pelo corredor do ônibus: manter x=0 e não parar em y=-3.8, -0.6 ou 2.6 (linhas dos corrimãos).
- Conferir cenas com movimento usando `--previa --amostras 6`: 3 quadros não mostram esses erros.

## Elenco brasileiro (pedido do usuário em 15/11/2026)
- O usuário achou as skins originais do Kenney estranhas e o manequim branco ruim. Agora os personagens usam skins
  pintadas por `blender/fazer_skins.py` (tipos `br_voce`, `br_senhora`, `br_motorista`, `br_homem`, `br_trocado`,
  `br_torcedor`, `br_moca`, `br_idoso`, `br_porteiro`, `br_jovem_mulher`): tons de pele variados, cabelo escuro ou
  grisalho, roupas do dia a dia (camisa da seleção, uniforme, vestido florido, xadrez).
- Para um personagem novo: acrescente uma entrada no dicionário `ELENCO` de `fazer_skins.py`, rode o script e
  registre o tipo em `KTIPOS` (mundo3d.py). Nunca usar boneco todo branco: "sem rosto" = mesma roupa, rosto liso.

## Regras de elenco (pedido do usuário em 15/11/2026)
- O modelo de boneco em bloco (estilo Roblox) CONTINUA. O que muda é a skin.
- **História nova = elenco novo:** personagens, roupas e aparências novos, sempre com cara de Brasil
  (tons de pele variados, roupas do dia a dia daqui). Criar as skins em `fazer_skins.py` antes de produzir.
- **Continuação = mesmo elenco:** os personagens que já existem usam exatamente as mesmas skins (ver `elenco` no
  `estado.json` da série). Só se cria skin nova quando entra um personagem novo na história.

## Narrador conduz a história (pedido do usuário em 16/11/2026)
No capítulo do ônibus o espectador ficou perdido: as falas apareciam "jogadas", sem dizer quem falava nem por quê.
- O narrador APRESENTA cada fala antes dela: quem fala, para quem e em que situação.
  Ex.: "O motorista nem olha pra você. Só avisa:" e então a fala do motorista.
- O narrador diz o que o protagonista PENSA e conclui ("Você faz a conta de cabeça: se desceu um, deviam ser cinco").
- Todo termo ou regra nova é explicado na hora, em uma frase (o que é a "parada", o que significa o relógio parado).
- Nunca deixar duas falas de personagens seguidas sem uma linha do narrador situando.
- Teste antes de aprovar o roteiro: alguém que só OUVE o áudio, sem ver a tela, entende quem é quem e o que aconteceu?

## Clareza para quem nunca viu a série (pedido do usuário em 16/11/2026)
- **Opções narradas:** no dilema final, o narrador LÊ as duas opções em voz alta, cada uma com o que significa e o
  que pode acontecer ("Opção A: mostrar o livro ao coronel. É o certo, mas você vira o principal suspeito.").
  Termina com "O que você faz? Comenta A ou B."
- **Caderno de pistas:** em séries de investigação, cada pista descoberta aparece anotada num caderninho na tela
  (frase curta, numerada). Antes do dilema, uma cena de recapitulação: o caderno aberto e o narrador repassando tudo.
  Em séries sem investigação, usar o equivalente (lista de regras descobertas).
- **Linguagem:** escrever para uma pessoa leiga e distraída. Frases simples, uma informação por frase, sem termo
  técnico sem explicação. Se a pessoa perder 5 segundos do vídeo, ainda precisa entender o que está acontecendo.

## Como fazer no plano: caderno, opções narradas e marcas de palavra (15/11/2026)
Tudo já está no gerador (`gerar_drama.py` + `caderno.py`); basta usar no plano da cena:
- **Pista no caderno:** `"nota": "Sala trancada por dentro"` na cena e `("som", "lapis")` como última linha. O caderninho
  desce do alto, mostra as pistas anteriores e escreve a nova em vermelho. Frase curta (até ~38 letras), numeração automática.
- **Recapitulação:** cena com `"caderno_cheio": True`. A 1ª fala do narrador abre o caderno; cada fala seguinte revela uma
  pista (uma fala por pista, na mesma ordem das notas).
- **Opções narradas:** na última cena, a fala do narrador tem "Opção A: ... Opção B: ... O que você faz? Comenta A ou B."
  A tela de escolha entra sozinha quando ele diz "Opção A", a B quando chega nela e o rodapé no "Comenta".
- **Marcas de palavra:** no código 3D, `T['p_palavra']` é o quadro em que o narrador diz a palavra (sem acento, 1ª vez na
  cena). Serve para a câmera acompanhar a narração (ex.: passar pelo rosto de cada suspeito quando ele é citado).
  Sempre com `T.get('p_x', int(F*0.5))`.
- **Sons que não seguram a narração:** `portao_fundo`, `passos_fundo` (a fala entra por cima). Trovão e impacto são cortados
  no fim da cena: nunca deixar como última linha.
- **Duração:** Shorts aceita no máximo 3 min. Conferir "duracao total" na prévia; se passar de 175 s, enxugar falas.
  Narrador apresentando falas + caderno + opções narradas dá ~3 min para 11 cenas; para ficar em 2 min, usar 8 cenas.
- **Cenários de O Relojoeiro:** `blender/palacio.py` (no código da cena é `P`): gabinete, corredor, sala_cameras, salao +
  suspeitos, portaria, patio (com chuva 3D), relampago, apagao. Texturas: `blender/fazer_texturas_relojoeiro.py`.
- **Lições das prévias do Relojoeiro:** móvel alto perto da câmera tampa o objeto do close (afastar o objeto do móvel);
  câmera por cima do ombro tem que ficar do lado oposto ao personagem de costas; a animação `correr` deixa o boneco
  inclinado demais em plano fechado (usar `andar`); objeto na mão fica ao lado do corpo, nunca solto na frente do peito;
  página de livro para close deve ser em pé (vídeo vertical) e com pouca emissão, senão estoura no branco.

## Vídeo em PRIMEIRA PESSOA (pedido do usuário em 15/11/2026: "vai dar mais suspense")
**Padrão para as histórias novas:** a câmera são os olhos do protagonista ("você"). Ele não aparece em cena.
- Usar `P.pov(keys, alvo_keys, lente, andando=[(f0, f1)])` (em `blender/palacio.py`): `keys` = por onde você anda
  (altura dos olhos 1,52 m automática; passar z para se abaixar ou se debruçar), `alvo_keys` = para onde você olha,
  `andando` = trechos com balanço de passo.
- **Campo de visão aberto** (o usuário pediu "fov mais alto"): lente 18 a 24. Só o close do gancho usa lente 40.
- Não criar o boneco do protagonista. Os outros personagens olham PARA A CÂMERA (olhar=0 quando a câmera está em -Y).
- O que o roteiro manda "você" fazer vira movimento de câmera: andar até alguém, virar para a porta, se abaixar para ver
  um objeto, se debruçar sobre o balcão, olhar um suspeito de cada vez (usar `T['p_palavra']`).
- Objeto na mão: `P.maos_com_livro(x, y, z)` mostra as mãos e as mangas na parte de baixo da tela; manter o objeto abaixo
  de 80% da altura para não brigar com a legenda (z ~1,05 com a câmera a 0,45 m).
- A fala de "você" continua existindo (voz própria, legenda amarela), só que sem boneco.
- Em continuação de série antiga em terceira pessoa (Última Parada), perguntar ao usuário antes de mudar.

## Sons: ambiente e objetos (reforçado pelo usuário em 15/11/2026)
O usuário quer **som de tudo o que acontece**, para dar suspense e drama, sempre em volume baixo e sem música.
- Toda cena tem pelo menos 2 camadas de ambiente (`amb`) e 1 som de ação ou objeto.
- Camadas: chuva, chuva_forte, vento, trovoada (trovões distantes), zumbido, bipes, tique, coracao, tensao (tom grave
  que cresce), ronco, motor, grilos.
- Ação/objeto: passos (`passos_longos`, `passos_agua`, `passos_chegando`), `portao`, `macaneta`, `rangido`, `pagina`,
  `lapis`, `alarme`, `luz_cai`, `trovao`, `tique_para`, `estatica`, `impacto`.
- `("fundo", nome)` toca por baixo da narração sem aumentar a duração; `"sons_em": [("palavra", nome)]` dispara o som
  na palavra exata do narrador (ex.: estática quando ele diz "pularam", impacto em "sumiu").
- Tensão crescente: `coracao` + `tensao` a partir da virada da história até o dilema.
