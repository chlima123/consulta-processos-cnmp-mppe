#!/usr/bin/env python3
"""
Consulta processos CNMP - Ministério Público do Estado de Pernambuco
Site: https://elo.cnmp.mp.br/pages/consulta.seam
"""

import re
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

TERMO_BUSCA = "Ministério Público do Estado de Pernambuco"
URL = "https://elo.cnmp.mp.br/pages/consulta.seam"

OUTPUT_DIR = Path(
    "/Users/chlima/Library/Mobile Documents/com~apple~CloudDocs"
    "/[0ia]claude_CH/automacoes/cnmp"
)
OUTPUT_FILE = OUTPUT_DIR / f"processos_mppe_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

PADRAO_NUMERO = re.compile(r"\d+\.\d+/\d{4}-\d{2}")


def extrair_numeros_pagina(page) -> list[str]:
    texto = page.locator("#formConteudo").inner_text()
    return PADRAO_NUMERO.findall(texto)


def proxima_pagina(page) -> bool:
    """Clica no botão '>' de próxima página. Retorna False se não existir ou estiver desabilitado."""
    seletores = [
        "a.ui-paginator-next:not(.ui-state-disabled)",
        "span.ui-paginator-next:not(.ui-state-disabled)",
        "a[title='Próxima Página']:not(.ui-state-disabled)",
        "a[title='Next Page']:not(.ui-state-disabled)",
    ]
    for sel in seletores:
        try:
            btn = page.locator(sel).first
            if btn.count() and btn.is_visible():
                btn.click()
                page.wait_for_load_state("networkidle", timeout=20000)
                time.sleep(1.5)
                return True
        except Exception:
            continue
    return False


def run():
    todos_processos: list[str] = []

    with sync_playwright() as p:
        print("Iniciando navegador...")
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page = ctx.new_page()
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        try:
            print(f"Acessando {URL} ...")
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector("input.ui-inputtext", timeout=20000)
            time.sleep(1)

            print(f"Buscando: '{TERMO_BUSCA}'")
            page.fill("[name='formConteudo:decParte:txNomeInteressado']", TERMO_BUSCA)
            page.click("[name='formConteudo:btPesquisar']")
            page.wait_for_load_state("networkidle", timeout=30000)
            time.sleep(2)

            pagina = 1
            while True:
                numeros = extrair_numeros_pagina(page)
                novos = [n for n in numeros if n not in todos_processos]
                todos_processos.extend(novos)
                print(f"  Página {pagina}: {len(novos)} novo(s) | Total: {len(todos_processos)}")

                if not proxima_pagina(page):
                    break
                pagina += 1

        except Exception as e:
            print(f"\nErro: {e}")
            page.screenshot(path=str(OUTPUT_DIR / "debug_erro.png"))
        finally:
            browser.close()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(todos_processos))

    print(f"\n{'='*50}")
    print(f"Total de processos: {len(todos_processos)}")
    print(f"Arquivo salvo em:\n  {OUTPUT_FILE}")
    print("=" * 50)


if __name__ == "__main__":
    run()
