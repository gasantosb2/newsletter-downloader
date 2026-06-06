#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
baixar.py — Ferramenta de linha de comando para alimentar a pesquisa da newsletter.

Dado um ou mais links de vídeo (YouTube, X, TikTok, Instagram, etc.), baixa:
  - o ÁUDIO em mp3 (melhor qualidade disponível);
  - as LEGENDAS manuais e automáticas em português e inglês, convertidas para .srt.

Cada vídeo é salvo em sua própria pasta, dentro de "downloads/", nomeada como
"AAAA-MM-DD_titulo-do-video" (data de publicação + título sanitizado para Windows).

Por baixo dos panos usa o yt-dlp e o ffmpeg.

Uso básico:
    python baixar.py URL1 URL2 ...
    python baixar.py --video URL1        # também salva o vídeo completo em mp4
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configurações gerais
# ---------------------------------------------------------------------------

# Pasta base onde tudo é salvo (criada dentro do projeto).
PASTA_BASE = Path(__file__).resolve().parent / "downloads"

# Idiomas de legenda desejados. O ".*" pega variantes (pt, pt-BR, en, en-US...).
IDIOMAS_LEGENDA = "pt.*,en.*"

# Template de nome usado pelo yt-dlp: cria uma subpasta "AAAA-MM-DD_titulo"
# e, dentro dela, arquivos com o mesmo nome base. A flag --windows-filenames
# (adicionada mais abaixo) remove os caracteres inválidos no Windows.
TEMPLATE_SAIDA = (
    "%(upload_date>%Y-%m-%d)s_%(title)s/"
    "%(upload_date>%Y-%m-%d)s_%(title)s.%(ext)s"
)


# ---------------------------------------------------------------------------
# Verificação de dependências
# ---------------------------------------------------------------------------

def verificar_dependencias() -> None:
    """Confere se yt-dlp e ffmpeg estão instalados e acessíveis no PATH.

    Se faltar algum, mostra uma mensagem clara explicando como instalar e
    encerra o programa.
    """
    faltando = []

    if shutil.which("yt-dlp") is None:
        faltando.append(
            "  - yt-dlp não encontrado. Instale com:\n"
            "        pip install -U yt-dlp"
        )

    if shutil.which("ffmpeg") is None:
        faltando.append(
            "  - ffmpeg não encontrado. Instale com:\n"
            "        winget install ffmpeg\n"
            "    (depois feche e reabra o terminal para atualizar o PATH)"
        )

    if faltando:
        print("ERRO: faltam dependências para rodar a ferramenta:\n")
        print("\n".join(faltando))
        print(
            "\nDepois de instalar, rode novamente:\n"
            "    python baixar.py URL1 URL2 ..."
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Montagem dos comandos do yt-dlp
# ---------------------------------------------------------------------------

def args_comuns(usar_cookies: bool) -> list[str]:
    """Argumentos do yt-dlp compartilhados por todas as chamadas."""
    args = [
        "yt-dlp",
        "--windows-filenames",        # sanitiza nomes para o Windows
        "--paths", str(PASTA_BASE),   # diretório base ("downloads/")
        "--output", TEMPLATE_SAIDA,   # subpasta + nome do arquivo
        "--no-overwrites",            # não re-baixa o que já existe
        "--ignore-config",            # ignora config global do yt-dlp do usuário
    ]
    if usar_cookies:
        # Pega os cookies do Chrome para acessar sites que exigem login
        # (Instagram, X em alguns casos, etc.).
        args += ["--cookies-from-browser", "chrome"]
    return args


def descobrir_pasta(url: str, usar_cookies: bool) -> Path | None:
    """Consulta o yt-dlp (sem baixar) para descobrir em qual pasta o vídeo cairá.

    Serve para dois propósitos: validar cedo que a URL é acessível e saber o
    caminho final para mostrar no resumo. Retorna o Path da pasta ou None se a
    consulta falhar.
    """
    cmd = args_comuns(usar_cookies) + [
        "--skip-download",
        "--print", "filename",
        "--quiet",
        "--no-warnings",
        url,
    ]
    try:
        resultado = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8"
        )
    except Exception:
        return None

    if resultado.returncode != 0:
        return None

    # O yt-dlp imprime o caminho completo do arquivo; a pasta é o diretório pai.
    linha = (resultado.stdout or "").strip().splitlines()
    if not linha:
        return None
    return Path(linha[0]).parent


def baixar_audio_e_legendas(url: str, usar_cookies: bool) -> None:
    """Baixa o melhor áudio em mp3 e as legendas (pt/en) em srt."""
    cmd = args_comuns(usar_cookies) + [
        # --- Áudio ---
        "--format", "bestaudio/best",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "0",        # 0 = melhor qualidade VBR
        # --- Legendas ---
        "--write-subs",                # legendas manuais (feitas por humanos)
        "--write-auto-subs",           # legendas automáticas (geradas por IA)
        "--sub-langs", IDIOMAS_LEGENDA,
        "--convert-subs", "srt",       # converte qualquer formato de legenda p/ srt
        url,
    ]
    # check=True faz lançar exceção se o yt-dlp retornar erro.
    subprocess.run(cmd, check=True)


def baixar_video(url: str, usar_cookies: bool) -> None:
    """Baixa o vídeo completo em mp4 (melhor vídeo + melhor áudio, mesclados)."""
    cmd = args_comuns(usar_cookies) + [
        "--format", "bestvideo*+bestaudio/best",
        "--merge-output-format", "mp4",
        url,
    ]
    subprocess.run(cmd, check=True)


# ---------------------------------------------------------------------------
# Fluxo principal
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Baixa áudio (mp3) e legendas (srt, pt/en) de links de vídeo, "
            "organizando tudo em pastas dentro de 'downloads/'."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "urls",
        nargs="+",
        metavar="URL",
        help="uma ou mais URLs de vídeo (YouTube, X, TikTok, Instagram, etc.)",
    )
    parser.add_argument(
        "--video",
        action="store_true",
        help="também salva o vídeo completo em mp4 (sem a flag, baixa só áudio + legenda)",
    )
    parser.add_argument(
        "--no-cookies",
        action="store_true",
        help="não usar os cookies do Chrome (use se a leitura dos cookies der erro)",
    )
    args = parser.parse_args()

    # 1) Confere as dependências antes de qualquer download.
    verificar_dependencias()

    usar_cookies = not args.no_cookies
    PASTA_BASE.mkdir(parents=True, exist_ok=True)

    sucessos: list[tuple[str, str]] = []   # (url, pasta)
    falhas: list[tuple[str, str]] = []     # (url, motivo)

    # 2) Processa cada URL de forma independente: se uma falhar, segue para a próxima.
    for i, url in enumerate(args.urls, start=1):
        print("\n" + "=" * 70)
        print(f"[{i}/{len(args.urls)}] Processando: {url}")
        print("=" * 70)

        try:
            pasta = descobrir_pasta(url, usar_cookies)

            baixar_audio_e_legendas(url, usar_cookies)
            if args.video:
                baixar_video(url, usar_cookies)

            destino = str(pasta) if pasta else str(PASTA_BASE)
            sucessos.append((url, destino))
            print(f"\nOK: salvo em {destino}")

        except subprocess.CalledProcessError as e:
            motivo = f"yt-dlp retornou código {e.returncode}"
            falhas.append((url, motivo))
            print(f"\nFALHOU: {motivo}", file=sys.stderr)
        except Exception as e:  # qualquer outro erro inesperado
            falhas.append((url, str(e)))
            print(f"\nFALHOU: {e}", file=sys.stderr)

    # 3) Resumo final.
    print("\n" + "#" * 70)
    print("RESUMO")
    print("#" * 70)
    print(f"Total de URLs: {len(args.urls)} | "
          f"Sucesso: {len(sucessos)} | Falhas: {len(falhas)}")

    if sucessos:
        print("\nBaixados com sucesso:")
        for url, destino in sucessos:
            print(f"  [OK] {url}")
            print(f"       -> {destino}")

    if falhas:
        print("\nFalharam:")
        for url, motivo in falhas:
            print(f"  [ERRO] {url}")
            print(f"         motivo: {motivo}")

    # Código de saída != 0 se houve qualquer falha (útil para automação).
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
