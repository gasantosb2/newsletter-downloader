#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
transcrever.py — transcreve arquivos de áudio (mp3, m4a, wav, etc.) em texto.

Usa o faster-whisper: o modelo Whisper (reconhecimento de fala) rodando
LOCALMENTE no seu PC — de graça, offline e sem enviar o áudio para fora.

Para cada arquivo de áudio, gera DOIS arquivos ao lado dele:
  - <nome>.txt   -> texto corrido (bom para ler/pesquisar)
  - <nome>.srt   -> trechos com marcação de tempo (bom para revisar/citar)

Uso:
    python transcrever.py audio1.mp3 audio2.mp3
    python transcrever.py --modelo medium --idioma pt "C:\\caminho\\audio.mp3"

Observações:
  - Na primeira vez, o modelo escolhido é baixado automaticamente (uma vez só).
  - Sem --idioma, o idioma é detectado automaticamente.
"""

import argparse
import sys
from pathlib import Path

# Extensões de áudio/vídeo que costumam funcionar (o ffmpeg decodifica o resto).
EXTENSOES_SUPORTADAS = {".mp3", ".m4a", ".wav", ".flac", ".ogg", ".opus",
                        ".aac", ".wma", ".mp4", ".mkv", ".webm"}


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def verificar_dependencias() -> None:
    """Confere se o faster-whisper está instalado; se não, ensina a instalar."""
    try:
        import faster_whisper  # noqa: F401
    except ImportError:
        print(
            "ERRO: a biblioteca faster-whisper não está instalada.\n"
            "Instale com:\n"
            "    pip install -U faster-whisper\n"
        )
        sys.exit(1)


def formatar_timestamp(segundos: float) -> str:
    """Converte segundos (float) para o formato de tempo do SRT: HH:MM:SS,mmm."""
    milissegundos = int(round(segundos * 1000))
    horas, milissegundos = divmod(milissegundos, 3_600_000)
    minutos, milissegundos = divmod(milissegundos, 60_000)
    segs, milissegundos = divmod(milissegundos, 1_000)
    return f"{horas:02d}:{minutos:02d}:{segs:02d},{milissegundos:03d}"


def escrever_saidas(caminho_audio: Path, segmentos: list) -> tuple[Path, Path]:
    """Grava o .txt (texto corrido) e o .srt (com tempos) ao lado do áudio."""
    saida_txt = caminho_audio.with_suffix(".txt")
    saida_srt = caminho_audio.with_suffix(".srt")

    # Texto corrido: junta o texto de todos os trechos.
    texto = " ".join(seg.text.strip() for seg in segmentos).strip()
    saida_txt.write_text(texto + "\n", encoding="utf-8")

    # SRT: cada trecho vira uma entrada numerada com tempo de início e fim.
    linhas = []
    for i, seg in enumerate(segmentos, start=1):
        linhas.append(str(i))
        linhas.append(
            f"{formatar_timestamp(seg.start)} --> {formatar_timestamp(seg.end)}"
        )
        linhas.append(seg.text.strip())
        linhas.append("")  # linha em branco separa as entradas
    saida_srt.write_text("\n".join(linhas), encoding="utf-8")

    return saida_txt, saida_srt


# ---------------------------------------------------------------------------
# Fluxo principal
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Transcreve arquivos de áudio em texto (.txt) e legenda com tempos "
            "(.srt), usando o Whisper localmente (faster-whisper)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "arquivos",
        nargs="+",
        metavar="ARQUIVO",
        help="um ou mais arquivos de áudio (ex.: audio.mp3)",
    )
    parser.add_argument(
        "--modelo",
        default="small",
        help=("tamanho do modelo Whisper: tiny, base, small (padrão), medium, "
              "large-v3. Maior = mais preciso, porém mais lento."),
    )
    parser.add_argument(
        "--idioma",
        default=None,
        help="código do idioma (ex.: pt, en). Sem isso, é detectado automaticamente.",
    )
    args = parser.parse_args()

    # 1) Confere a dependência antes de carregar qualquer coisa.
    verificar_dependencias()
    from faster_whisper import WhisperModel

    # 2) Carrega o modelo uma única vez (reaproveitado para todos os arquivos).
    #    device="cpu" + compute_type="int8" = leve e rápido sem placa de vídeo.
    print(f"Carregando o modelo '{args.modelo}' (pode baixar na 1ª vez)...")
    try:
        modelo = WhisperModel(args.modelo, device="cpu", compute_type="int8")
    except Exception as e:
        print(f"ERRO ao carregar o modelo '{args.modelo}': {e}", file=sys.stderr)
        sys.exit(1)

    sucessos: list[tuple[str, str, str]] = []   # (audio, txt, srt)
    falhas: list[tuple[str, str]] = []          # (audio, motivo)

    # 3) Processa cada arquivo de forma independente.
    for i, nome in enumerate(args.arquivos, start=1):
        caminho = Path(nome).expanduser().resolve()
        print("\n" + "=" * 70)
        print(f"[{i}/{len(args.arquivos)}] Transcrevendo: {caminho.name}")
        print("=" * 70)

        try:
            if not caminho.is_file():
                raise FileNotFoundError("arquivo não encontrado")
            if caminho.suffix.lower() not in EXTENSOES_SUPORTADAS:
                print(f"Aviso: extensão '{caminho.suffix}' incomum; tentando mesmo assim.")

            # vad_filter=True ignora silêncios, melhorando a precisão.
            segmentos_iter, info = modelo.transcribe(
                str(caminho), language=args.idioma, vad_filter=True
            )

            idioma_detectado = info.language
            print(f"Idioma: {idioma_detectado} "
                  f"(confiança {info.language_probability:.0%}) | "
                  f"duração {info.duration:.0f}s")
            print("Processando o áudio... (acompanhe os trechos abaixo)")

            # O resultado é um gerador: percorremos uma vez e guardamos numa lista.
            segmentos = []
            for seg in segmentos_iter:
                segmentos.append(seg)
                # Mostra o progresso ao vivo: tempo + trecho transcrito.
                print(f"  [{formatar_timestamp(seg.start)}] {seg.text.strip()}")

            txt, srt = escrever_saidas(caminho, segmentos)
            sucessos.append((caminho.name, str(txt), str(srt)))
            print(f"\nOK: {txt.name} e {srt.name}")

        except Exception as e:
            falhas.append((nome, str(e)))
            print(f"\nFALHOU: {e}", file=sys.stderr)

    # 4) Resumo final.
    print("\n" + "#" * 70)
    print("RESUMO")
    print("#" * 70)
    print(f"Total: {len(args.arquivos)} | "
          f"Sucesso: {len(sucessos)} | Falhas: {len(falhas)}")

    if sucessos:
        print("\nTranscritos:")
        for audio, txt, srt in sucessos:
            print(f"  [OK] {audio}")
            print(f"       -> {txt}")
            print(f"       -> {srt}")

    if falhas:
        print("\nFalharam:")
        for audio, motivo in falhas:
            print(f"  [ERRO] {audio}")
            print(f"         motivo: {motivo}")

    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
