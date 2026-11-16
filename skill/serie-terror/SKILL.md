---
name: serie-terror
description: Cria e continua séries de terror em capítulos para Shorts/Reels (3D no Blender, vozes ElevenLabs, público vota A ou B). Use quando o usuário pedir uma série nova, um capítulo novo, a continuação de uma série, ou escrever /serie-terror. Conduz o fluxo com aprovações do usuário em cada etapa — premissa, roteiro, vídeo — e salva o estado para as continuações.
---

# Séries de terror em capítulos

Tudo fica em `C:\Users\Filipe\MoneyPrinterTurbo\estudio`. **Antes de qualquer coisa, leia `GUIA_PRODUCAO.md`**
nessa pasta: ele lista o que o usuário aprovou, o que reprovou e as lições de cada capítulo.
A referência de qualidade é `series/ultima_parada/` (capítulo aprovado com entusiasmo).

O usuário fala português informal, por texto ou voz transcrita. Responda em português, direto.
Você não consegue ouvir áudio: sempre diga isso ao entregar e peça que ele avalie voz e volume.

## Regra geral do fluxo
Nunca avance para a etapa seguinte sem a aprovação explícita do usuário. A cada etapa ele pode
**aprovar**, **pedir ajuste** (você corrige e mostra de novo) ou **reprovar** (você propõe outra coisa).
Registre cada decisão em `series/<slug>/estado.json` e cada lição nova em `GUIA_PRODUCAO.md`.

## Modo 1 — Série nova
1. **Premissas.** Proponha 3 ou 4 premissas originais com a ferramenta de pergunta (uma frase cada, com o gancho).
   Critérios: um lugar só (um cenário para construir), fenômeno com regras, contexto claro em 10 segundos,
   final que muda a pergunta. Nunca copie histórias dos canais de referência.
2. **Roteiro.** Escreva o capítulo 1 em `series/roteiros/<slug>-cap1.md` no formato do roteiro de
   `ultima-parada-cap1.md`: premissa, regras reveladas (uma por cena), vozes, sons, 9 a 11 cenas com a fala de cada
   uma, tela de escolha A/B e ideias para a continuação de cada opção. Mostre um resumo no chat e envie o arquivo.
   Espere a aprovação.
3. **Produção** (só depois do roteiro aprovado):
   - Cenário: reutilize um existente (`M.hall_predio`, `M.onibus`) ou construa um novo em `blender/mundo3d.py`,
     no mesmo estilo (`M.ambiente('interior')` liga o contorno). Texturas com texto: gere com PIL, como em
     `blender/fazer_texturas_onibus.py`.
   - Plano: `series/<slug>/cap1_plano.py`, copiando a estrutura de `series/ultima_parada/cap1_plano.py`
     (cenas com `hud`, `amb`, `linhas` e `codigo`; marcas `T` para sincronizar com o som).
   - Prévia: `..\.venv\Scripts\python.exe gerar_drama.py <plano> --previa`, **olhe** `previas.jpg`, corrija câmeras
     e repita só as cenas alteradas com `--cenas 2,5`.
   - Final: `..\.venv\Scripts\python.exe gerar_drama.py <plano>` em segundo plano (30 a 45 min).
   - Revise 20 quadros do `final.mp4` antes de entregar. Confira o saldo do ElevenLabs.
4. **Entrega.** Envie o vídeo e o `publicar.txt`. Diga o que conferiu, o que não conferiu e o que sabe que
   ficou imperfeito. Espere a avaliação: aprovado, ajustar (som: `--so-audio` não renderiza de novo) ou refazer.
5. **Salvar.** Com o vídeo aprovado, grave em `estado.json`: premissa, cenário, vozes, regras reveladas,
   mistérios abertos, e o capítulo com pergunta, opções A/B, ideias de continuação e `status: video_aprovado`.

## Modo 2 — Continuação
1. Liste as séries (`series/*/estado.json`) e pergunte qual continuar, se ele não disse.
2. Leia o `estado.json` e o roteiro do capítulo anterior. Pergunte **qual opção o público votou** (A ou B).
3. **O que vai acontecer.** Proponha 2 ou 3 caminhos para o capítulo (um parágrafo cada: o que acontece,
   qual regra nova é revelada, qual é o novo dilema A/B). Respeite tudo que já foi estabelecido.
   Espere ele escolher ou ajustar.
4. Siga os passos 2 a 5 do Modo 1 para o capítulo N. O capítulo abre lembrando a escolha do público em uma
   frase e mostrando a consequência. Reaproveite o cenário e as mesmas vozes dos personagens.
5. Atualize o `estado.json`: `escolha_do_publico` do capítulo anterior e o capítulo novo.

## Narrador (regra do usuário)
- O narrador conduz: antes de cada fala, ele diz quem fala e em que situação ("O motorista nem olha pra você. Só avisa:").
- Ele conta o que o protagonista pensa e conclui, e explica na hora cada termo ou regra nova.
- Nunca duas falas de personagens seguidas sem o narrador situando. Quem só ouve o áudio precisa entender tudo.

## Clareza (regra do usuário)
- No dilema final, o narrador lê as opções A e B em voz alta, com o que cada uma significa e a consequência provável.
- Séries de investigação têm o **caderno do detetive**: cada pista vira uma anotação na tela, e antes do dilema há uma
  cena de recapitulação com o caderno aberto. Em outras séries, o equivalente é a lista de regras descobertas.
- Escreva para uma pessoa leiga e distraída: frases simples, uma informação por frase, nada sem explicação.

## Elenco (regra do usuário)
- O boneco em bloco (estilo Roblox) continua sempre. O que muda é a **skin**, pintada em `blender/fazer_skins.py`.
- **Série nova:** crie um elenco novo, com personagens, roupas e aparências diferentes das outras séries, sempre com
  cara de Brasil (tons de pele variados, cabelo escuro ou grisalho, roupas do dia a dia). Acrescente as entradas em
  `ELENCO`, rode o script, registre os tipos `br_<nome>` em `KTIPOS` (mundo3d.py) e renderize uma folha do elenco para
  conferir. Grave o elenco em `estado.json`.
- **Continuação:** use exatamente as mesmas skins do `elenco` salvo no `estado.json`. Skin nova só para personagem
  novo que entra na história.
- Nunca use boneco todo branco. Figura "sem rosto" = roupa e pele normais com o rosto liso (`rosto=False`).

## Padrões aprovados (resumo; o guia tem os detalhes)
- Vozes: ElevenLabs (`elevenlabs_key.txt`, `vozes_elevenlabs.json`). Narrador Brian. Números por extenso.
  Cerca de 900 a 1.100 caracteres por capítulo; plano gratuito de 10.000 por mês. Avise o saldo.
- Som: sem música; ambiente baixo (`VOL_AMBIENTE 0.3`, `VOL_EFEITO 0.55`), um som-assinatura por série.
- Visual: contorno preto, placar pequeno no canto, narrador em branco com palavra-chave vermelha, falas em
  amarelo, tela A/B no fim. Sem números gigantes, sem título gigante, sem legenda no topo.
- Bonecos: Kenney em bloco, pose firme (não usar o "idle"), gestos só uma vez, evitar câmera de lado no rosto.
- Duração: 90 a 110 segundos.

## Primeira pessoa (regra do usuário)
- Histórias novas são filmadas em **primeira pessoa**: a câmera são os olhos de "você", que não aparece.
  Usar `P.pov(...)` com lente 18 a 24 (campo de visão aberto) e balanço de passo quando anda.
- No roteiro, descrever cada cena pelo que "você" vê e faz (anda, vira, se abaixa, se debruça).
- Os personagens encaram a câmera. Objetos que você segura aparecem com as mãos na parte de baixo da tela.

## Sons (regra do usuário)
- Sem música, mas com **som de tudo**: 2 camadas de ambiente por cena + sons de passos, portas, objetos e sustos,
  em volume baixo. Usar `("fundo", nome)` e `"sons_em"` para não alongar o vídeo. Lista completa no guia.

## Personagens em cena (regra do usuário)
- Quando um personagem fala, **a boca mexe**: `boneco.falar(T['lK'], T['lK_fim'])`.
- Nunca mostrar parte do corpo solta (braço sem corpo): o personagem inteiro tem que existir na cena.
- Toda ação tem som (porta, portão, passos, chuva, objetos).

## Antes do render final
- Mostrar ao usuário a folha de prévias (principalmente cenas com personagem, móvel ou objeto novo) e esperar o OK.
  O render leva ~50 min; cada correção depois dele custa outro render inteiro.

## Recursos prontos no gerador
- Caderno: `"nota": "..."` + `("som", "lapis")` na cena; recapitulação com `"caderno_cheio": True`.
- Opções narradas: a última fala do narrador com "Opção A: ... Opção B: ..." sincroniza a tela de escolha sozinha.
- `T['p_palavra']`: quadro em que o narrador diz a palavra, para a câmera acompanhar a narração.
- Duração máxima 3 min (Shorts): conferir "duracao total" na prévia antes de renderizar.
- Detalhes e lições em `estudio/GUIA_PRODUCAO.md`, seção "Como fazer no plano".

## Cuidados
- Não cole nem repita a chave do ElevenLabs no chat.
- Baixar ou instalar qualquer coisa nova exige pedir permissão antes.
- Lembre o usuário de conferir no site do ElevenLabs se o plano dele permite uso comercial antes de monetizar.
