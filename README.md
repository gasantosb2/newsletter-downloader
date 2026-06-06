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
