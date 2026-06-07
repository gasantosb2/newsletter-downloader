# newsletter-downloader

Ferramenta de linha de comando (Windows) para alimentar a pesquisa da newsletter.

Dado um ou mais links de vídeo (YouTube, X, TikTok, Instagram, etc.), ela baixa:

- o **áudio em mp3** (melhor qualidade disponível);
- as **legendas** manuais e automáticas em **português e inglês**, convertidas para **.srt**.

Cada vídeo vai para a própria pasta dentro de `downloads/`, nomeada como
`AAAA-MM-DD_titulo-do-video` (data de publicação + título, sanitizado para o Windows).
Dentro dela ficam o `.mp3` e o(s) `.srt`.

## Pré-requisitos

- **Python 3** (já instalado).
- **yt-dlp**: `pip install -U yt-dlp`
- **ffmpeg**: `winget install ffmpeg` (feche e reabra o terminal depois)
- **faster-whisper** (só para transcrever): `pip install -U faster-whisper`

Os scripts verificam essas dependências antes de rodar e avisam se faltar alguma.

## Como rodar

```powershell
# Baixar áudio + legendas de um ou mais vídeos
python baixar.py "URL1" "URL2"

# Também salvar o vídeo completo em mp4
python baixar.py --video "URL1"

# Desligar o uso dos cookies do Chrome (caso a leitura dê erro)
python baixar.py --no-cookies "URL1"
```

## Transcrever áudio em texto (`transcrever.py`)

O `baixar.py` pega legendas que **já existem** no vídeo. Para transcrever um
`.mp3` qualquer (mesmo sem legenda), use o `transcrever.py`, que roda o modelo
Whisper localmente — de graça, offline, sem enviar o áudio para fora.

Para cada áudio, gera ao lado dele um `.txt` (texto corrido) e um `.srt` (com tempos):

```powershell
# Transcrever um ou mais áudios
python transcrever.py "downloads\2005-04-24_Me at the zoo\2005-04-24_Me at the zoo.mp3"

# Forçar o idioma (mais rápido/preciso que a detecção automática)
python transcrever.py --idioma pt "audio.mp3"

# Usar um modelo maior (mais preciso, porém mais lento na CPU)
python transcrever.py --modelo medium "audio.mp3"
```

Modelos: `tiny`, `base`, `small` (padrão), `medium`, `large-v3`. Na primeira
execução, o modelo escolhido é baixado uma única vez. Sem placa de vídeo, áudios
longos com modelos grandes podem levar alguns minutos.

## Dica para o YouTube

O YouTube vem exigindo um runtime JavaScript para extrair alguns formatos e
limita a API de legendas (pode retornar "HTTP 429: Too Many Requests" se muitos
pedidos forem feitos em sequência). Para melhor compatibilidade:

- Instale o **deno** (runtime JS recomendado pelo yt-dlp): `winget install DenoLand.Deno`
- Se aparecer 429 nas legendas, espere alguns minutos e rode de novo. O áudio é
  baixado de qualquer forma — a ferramenta salva o áudio mesmo que as legendas
  falhem (e avisa "sem legendas" no resumo).

## Detalhes úteis

- **Login / cookies:** por padrão a ferramenta usa os cookies do Chrome
  (`--cookies-from-browser chrome`), para acessar conteúdo que exige login
  (ex.: Instagram). Use `--no-cookies` para desativar.
- **Tolerância a falhas:** se uma URL falhar, o erro é registrado e a ferramenta
  segue para as próximas. No fim é impresso um resumo do que baixou, onde salvou
  e o que falhou.
- **Saída:** tudo é salvo em `downloads/` (essa pasta é ignorada pelo git).
