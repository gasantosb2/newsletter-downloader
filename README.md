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

O próprio script verifica essas dependências antes de rodar e avisa se faltar alguma.

## Como rodar

```powershell
# Baixar áudio + legendas de um ou mais vídeos
python baixar.py "URL1" "URL2"

# Também salvar o vídeo completo em mp4
python baixar.py --video "URL1"

# Desligar o uso dos cookies do Chrome (caso a leitura dê erro)
python baixar.py --no-cookies "URL1"
```

## Detalhes úteis

- **Login / cookies:** por padrão a ferramenta usa os cookies do Chrome
  (`--cookies-from-browser chrome`), para acessar conteúdo que exige login
  (ex.: Instagram). Use `--no-cookies` para desativar.
- **Tolerância a falhas:** se uma URL falhar, o erro é registrado e a ferramenta
  segue para as próximas. No fim é impresso um resumo do que baixou, onde salvou
  e o que falhou.
- **Saída:** tudo é salvo em `downloads/` (essa pasta é ignorada pelo git).
