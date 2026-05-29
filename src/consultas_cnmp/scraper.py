"""Lógica de scraping do sistema ELO/CNMP."""

import re
import time
from dataclasses import dataclass, field
from typing import Optional, Tuple

from playwright.sync_api import Page, TimeoutError as PWTimeout

URL = "https://elo.cnmp.mp.br/pages/consulta.seam"

_NUM_PATTERN = re.compile(r"\d+\.\d+/\d{4}-\d{2}")

_BLOCO_PATTERN = re.compile(
    r"Número:\s*\n\s*(?P<numero>[^\n]+?)\s*\n"
    r"Localização atual:\s*\n\s*(?P<localizacao>[^\n]*?)\s*\n"
    r"Data de distribuição:\s*\n\s*(?P<data>[^\n]*?)\s*\n"
    r"Relator:\s*\n\s*(?P<relator>[^\n]*?)\s*\n"
    r"Classe processual:\s*\n\s*(?P<classe>[^\n]*?)\s*\n"
    r"Objeto do processo:\s*\n(?P<objeto>.*?)\s*\nDocumentos:",
    re.DOTALL,
)


@dataclass
class Processo:
    numero: str
    localizacao: str = ""
    data_distribuicao: str = ""
    relator: str = ""
    classe_processual: str = ""
    objeto: str = ""
    termos_busca: list[str] = field(default_factory=list)


def buscar_por_nome(
    page: Page,
    termo: str,
    arquivado: bool = False,
) -> list[Processo]:
    """Busca processos pelo nome da parte."""
    _carregar_pagina(page)
    page.fill("[name='formConteudo:decParte:txNomeInteressado']", termo)
    if arquivado:
        page.select_option(
            "[name='formConteudo:decCbArquivado:cbArquivado']", "true"
        )
    _pesquisar(page)
    return _extrair_todas_paginas(page, termos=[termo])


def buscar_por_numero(page: Page, numero: str) -> list[Processo]:
    """Busca processo pelo número (formato 1.00000/AAAA-DD)."""
    partes = _parse_numero(numero)
    if not partes:
        raise ValueError(f"Número inválido: {numero!r}. Use o formato 1.00000/AAAA-DD")

    _carregar_pagina(page)

    campos = page.locator("input.ui-inputtext").all()
    # Os 3 primeiros campos são os segmentos do número do processo
    if len(campos) >= 3:
        if partes[0]:
            campos[0].fill(partes[0])
        if partes[1]:
            campos[1].fill(partes[1])
        if partes[2]:
            campos[2].fill(partes[2])

    _pesquisar(page)
    return _extrair_todas_paginas(page, termos=[numero])


def _parse_numero(numero: str) -> Optional[Tuple[str, str, str]]:
    """Decompõe 1.00230/2015-90 em ('1', '00230/2015', '90')."""
    m = re.match(r"(\d+)\.(\d+/\d{4})-(\d+)", numero.strip())
    if not m:
        return None
    return m.group(1), m.group(2), m.group(3)


def _carregar_pagina(page: Page) -> None:
    page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_selector("input.ui-inputtext", timeout=20_000)
    time.sleep(1)


def _pesquisar(page: Page) -> None:
    page.click("[name='formConteudo:btPesquisar']")
    try:
        page.wait_for_load_state("networkidle", timeout=30_000)
    except PWTimeout:
        pass
    time.sleep(2)


def _extrair_pagina(page: Page, termos: list[str]) -> list[Processo]:
    try:
        texto = page.locator("#formConteudo").inner_text()
    except Exception:
        return []

    processos = []
    for m in _BLOCO_PATTERN.finditer(texto):
        numero = m.group("numero").strip()
        if not _NUM_PATTERN.search(numero):
            continue
        processos.append(
            Processo(
                numero=numero,
                localizacao=m.group("localizacao").strip(),
                data_distribuicao=m.group("data").strip(),
                relator=m.group("relator").strip(),
                classe_processual=m.group("classe").strip(),
                objeto=m.group("objeto").strip()[:300],
                termos_busca=termos,
            )
        )

    # Fallback: extrai só os números se o parser de blocos falhar
    if not processos:
        for num in _NUM_PATTERN.findall(texto):
            processos.append(Processo(numero=num, termos_busca=termos))

    return processos


def _proxima_pagina(page: Page) -> bool:
    for sel in [
        "a.ui-paginator-next:not(.ui-state-disabled)",
        "span.ui-paginator-next:not(.ui-state-disabled)",
        "a[title='Próxima Página']:not(.ui-state-disabled)",
    ]:
        try:
            btn = page.locator(sel).first
            if btn.count() and btn.is_visible():
                btn.click()
                try:
                    page.wait_for_load_state("networkidle", timeout=20_000)
                except PWTimeout:
                    pass
                time.sleep(1.5)
                return True
        except Exception:
            continue
    return False


def _extrair_todas_paginas(page: Page, termos: list[str]) -> list[Processo]:
    vistos: set[str] = set()
    todos: list[Processo] = []
    pagina = 1

    while True:
        processos = _extrair_pagina(page, termos)
        novos = [p for p in processos if p.numero not in vistos]
        vistos.update(p.numero for p in novos)
        todos.extend(novos)
        print(f"  Página {pagina}: {len(novos)} novo(s) | Total: {len(todos)}")

        if not _proxima_pagina(page):
            break
        pagina += 1

    return todos
