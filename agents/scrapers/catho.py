"""
Scraper Catho — Fase 2
Busca vagas no Catho usando Playwright.
Foco: vagas home office de design/UX/UI.

Portal: https://www.catho.com.br
"""

import json
import asyncio
import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent.parent
DATA_DIR = ROOT / "data"

TERMOS_BUSCA = [
    "designer ux ui",
    "ux designer",
    "ui designer",
    "product designer",
    "web designer",
]


async def buscar_catho(headless: bool = True) -> list[dict]:
    """Busca vagas no Catho via Playwright."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("  Playwright não instalado. Execute: py -m playwright install chromium")
        return []

    vagas = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 900},
        )
        page = await context.new_page()

        for termo in TERMOS_BUSCA:
            print(f"  Catho buscando: {termo}...")
            try:
                # Busca com filtro home office
                termo_enc = termo.replace(" ", "%20")
                url = f"https://www.catho.com.br/vagas/{termo.replace(' ', '-')}/?q={termo_enc}&home_office=1"
                await page.goto(url, timeout=30000, wait_until="networkidle")
                await page.wait_for_timeout(2000)

                # Fecha popups se existirem
                try:
                    fechar = await page.query_selector("[aria-label='Fechar'], .close-button, button[data-dismiss]")
                    if fechar:
                        await fechar.click()
                        await page.wait_for_timeout(500)
                except Exception:
                    pass

                # Rola para carregar mais
                for _ in range(3):
                    await page.keyboard.press("End")
                    await page.wait_for_timeout(800)

                # Extrai cards
                cards = await page.query_selector_all(
                    "article, .job-card, [data-testid='job-card'], li.sc-dBAPEh"
                )

                for card in cards:
                    try:
                        titulo_el  = await card.query_selector("h2, h3, .job-title")
                        empresa_el = await card.query_selector(".company-name, .sc-iGgWBj")
                        local_el   = await card.query_selector(".location, .sc-bdnxRM")
                        link_el    = await card.query_selector("a[href]")

                        titulo  = await titulo_el.inner_text() if titulo_el else ""
                        empresa = await empresa_el.inner_text() if empresa_el else ""
                        local   = await local_el.inner_text() if local_el else ""
                        href    = await link_el.get_attribute("href") if link_el else ""

                        if not titulo or len(titulo) < 3:
                            continue

                        url_vaga = href if href.startswith("http") else f"https://www.catho.com.br{href}"

                        vagas.append({
                            "titulo":   titulo.strip(),
                            "empresa":  empresa.strip(),
                            "local":    local.strip(),
                            "url":      url_vaga,
                            "termo_busca": termo,
                        })
                    except Exception:
                        continue

            except Exception as e:
                print(f"  Catho/{termo}: {e}")

        await browser.close()

    print(f"  Catho: {len(vagas)} vagas coletadas")
    return vagas


def normalizar_catho(v: dict) -> dict:
    url = v.get("url", "")
    local = v.get("local", "").lower()
    pcd = "pcd" in v.get("titulo", "").lower() or "deficiência" in v.get("titulo", "").lower()
    return {
        "id": f"catho_{abs(hash(url))}",
        "titulo": v.get("titulo", ""),
        "empresa": v.get("empresa", ""),
        "descricao": "",
        "url": url,
        "salario": "",
        "localidade": v.get("local", "Brasil"),
        "tags": ["pcd"] if pcd else [],
        "data_publicacao": datetime.now().strftime("%Y-%m-%d"),
        "plataforma": "Catho",
        "idioma_vaga": "pt",
        "pcd_detectado": pcd,
        "score": 0,
        "status": "nova"
    }


async def executar_catho(salvar: bool = True) -> list[dict]:
    print("Iniciando scraper Catho...")
    raw = await buscar_catho()
    vagas = [normalizar_catho(v) for v in raw]

    vistos = set()
    unicas = []
    for v in vagas:
        if v["id"] not in vistos:
            vistos.add(v["id"])
            unicas.append(v)

    print(f"Catho: {len(unicas)} vagas únicas")

    if salvar:
        saida = DATA_DIR / "catho_vagas.json"
        with open(saida, "w", encoding="utf-8") as f:
            json.dump(unicas, f, ensure_ascii=False, indent=2)
        print(f"Salvo em {saida}")

    return unicas


if __name__ == "__main__":
    asyncio.run(executar_catho())
