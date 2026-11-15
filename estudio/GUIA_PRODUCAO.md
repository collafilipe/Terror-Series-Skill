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
