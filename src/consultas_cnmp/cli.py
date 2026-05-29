"""CLI — entrada principal do pacote consultas-cnmp."""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from consultas_cnmp.browser import new_page
from consultas_cnmp.exporters import exportar
from consultas_cnmp.scraper import buscar_por_nome, buscar_por_numero

_DEFAULT_TERMO = "Ministério Público do Estado de Pernambuco"
_DEFAULT_SAIDA = Path("resultados")
_FORMATOS_VALIDOS = ["txt", "csv", "json", "excel"]


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="consultas-cnmp",
        description="Consulta processos no sistema ELO do CNMP.",
    )
    grupo = p.add_mutually_exclusive_group()
    grupo.add_argument(
        "--termo", "-t",
        default=_DEFAULT_TERMO,
        metavar="TEXTO",
        help=f'Nome da parte (padrão: "{_DEFAULT_TERMO}")',
    )
    grupo.add_argument(
        "--numero", "-n",
        metavar="NUMERO",
        help="Número do processo (ex: 1.00230/2015-90)",
    )
    p.add_argument(
        "--arquivado", "-a",
        action="store_true",
        help="Buscar apenas processos arquivados",
    )
    p.add_argument(
        "--formato", "-f",
        nargs="+",
        default=["txt"],
        choices=_FORMATOS_VALIDOS,
        metavar="FMT",
        help=f"Formatos de saída: {', '.join(_FORMATOS_VALIDOS)} (padrão: txt)",
    )
    p.add_argument(
        "--saida", "-o",
        type=Path,
        default=_DEFAULT_SAIDA,
        metavar="DIR",
        help=f"Diretório de saída (padrão: {_DEFAULT_SAIDA})",
    )
    p.add_argument(
        "--browserbase",
        action="store_true",
        help="Usar Browserbase em vez do Chromium local",
    )
    return p


def main(argv: Optional[List[str]] = None) -> None:
    args = _parser().parse_args(argv)

    print("=" * 55)
    print("  Consulta ELO/CNMP")
    print("=" * 55)

    with new_page(use_browserbase=args.browserbase) as page:
        if args.numero:
            print(f"Buscando número: {args.numero}")
            processos = buscar_por_numero(page, args.numero)
        else:
            print(f"Buscando por nome: {args.termo}")
            processos = buscar_por_nome(page, args.termo, arquivado=args.arquivado)

    if not processos:
        print("\nNenhum processo encontrado.")
        sys.exit(0)

    print(f"\nTotal encontrado: {len(processos)}")
    print(f"Exportando para: {args.saida}/")
    exportar(processos, args.saida, args.formato)
    print("\nConcluído.")


if __name__ == "__main__":
    main()
