"""
Scraper Gupy — Fase 2
Busca vagas no Portal Gupy usando Playwright (SPA).
Foco: vagas remotas/home office com filtro PCD.

Portal: https://portal.gupy.io
"""

import json
import asyncio
import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent.parent
DATA_DIR = ROOT / "data"


# ──────────────────────────────────────────────
# Busca via Portal Gupy (Playwright)
# ──────────────────────────────────────────────

TERMOS_BUSCA = [
    # Design Engineer — foco principal
    "design engineer",
    "design systems engineer",
    "engenheiro de design",
    # UX/UI
    "designer ux",
    "designer ui",
    "ux ui designer",
    "product designer",
    # Web / Visual
    "web designer",
    "design technologist",
]


# JavaScript para extrair vagas do Gupy usando a estrutura real da página
_JS_EXTRAIR_GUPY = """() => {
    const links = [...document.querySelectorAll('a[href*=\".gupy.io/job/\"]')];
    return links.map(a => {
        const card = a.closest('li') || a.closest('article') || a.parentElement;
        const h3 = card ? card.querySelector('h3') : null;
        const ps = card ? [...card.querySelectorAll('p, span')]
            .map(e => e.innerText.trim()).filter(t => t.length > 1) : [];
        const textoCompleto = a.innerText || '';
        const pcd = textoCompleto.toLowerCase().includes('pcd') ||
                    textoCompleto.toLowerCase().includes('pcd') ||
                    textoCompleto.toLowerCase().includes('defici');
        return {
            url: a.href,
            titulo: h3 ? h3.innerText.trim() : (ps[0] || ''),
            empresa: ps[0] || '',
            local: ps[2] || '',
            pcd: pcd
        };
    });
}"""


async def _extrair_pagina_gupy(page, url: str) -> list[dict]:
    """Navega até uma URL do Gupy e extrai todas as vagas da página."""
    await page.goto(url, timeout=30000, wait_until="networkidle")
    await page.wait_for_timeout(2500)
    # Scroll para carregar lazy load
    for _ in range(4):
        await page.keyboard.press("End")
        await page.wait_for_timeout(700)
    return await page.evaluate(_JS_EXTRAIR_GUPY)


async def buscar_gupy(headless: bool = True) -> list[dict]:
    """
    Busca vagas no Portal Gupy via Playwright.
    Filtra por: remoto/home office + termos de design + vagas PCD.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("  Playwright não instalado. Execute: py -m playwright install chromium")
        return []

    vagas = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        )

        # Busca por termos de design (remoto)
        for termo in TERMOS_BUSCA:
            print(f"  Gupy: {termo}...")
            try:
                url = (
                    f"https://portal.gupy.io/job-search/term={termo.replace(' ', '%20')}"
                    f"?workplaceTypes[]=remote"
                )
                encontrados = await _extrair_pagina_gupy(page, url)
                for v in encontrados:
                    v["termo_busca"] = termo
                vagas.extend(encontrados)
            except Exception as e:
                print(f"  Gupy/{termo}: {e}")

        # Busca dedicada a vagas PCD
        print("  Gupy: vagas PCD remoto...")
        try:
            encontrados = await _extrair_pagina_gupy(
                page,
                "https://portal.gupy.io/job-search/term=pcd?workplaceTypes[]=remote"
            )
            for v in encontrados:
                v["termo_busca"] = "pcd"
                v["pcd"] = True
            vagas.extend(encontrados)
        except Exception as e:
            print(f"  Gupy/PCD: {e}")

        await browser.close()

    print(f"  Gupy: {len(vagas)} vagas coletadas")
    return vagas


async def buscar_descricao_gupy(url: str, headless: bool = True) -> str:
    """Abre a página de uma vaga Gupy e extrai a descrição completa."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return ""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=20000, wait_until="domcontentloaded")
            await page.wait_for_timeout(1500)
            desc_el = await page.query_selector(".job-description, [data-testid='job-description'], main")
            desc = await desc_el.inner_text() if desc_el else ""
            return desc[:4000]
        except Exception:
            return ""
        finally:
            await browser.close()


def normalizar_gupy(v: dict) -> dict:
    url = v.get("url", "")
    pcd = v.get("pcd_explicito", False) or "pcd" in v.get("titulo", "").lower()
    localidade = v.get("local", "")
    return {
        "id": f"gupy_{abs(hash(url))}",
        "titulo": v.get("titulo", ""),
        "empresa": v.get("empresa", ""),
        "descricao": v.get("descricao", ""),
        "url": url,
        "salario": "",
        "localidade": localidade or "Remoto",
        "tags": ["pcd"] if pcd else [],
        "data_publicacao": datetime.now().strftime("%Y-%m-%d"),
        "plataforma": "Gupy",
        "idioma_vaga": "pt",
        "pcd_detectado": pcd,
        "score": 0,
        "status": "nova"
    }


# ──────────────────────────────────────────────
# Execução standalone
# ──────────────────────────────────────────────

async def executar_gupy(salvar: bool = True) -> list[dict]:
    print("Iniciando scraper Gupy...")
    raw = await buscar_gupy()
    vagas = [normalizar_gupy(v) for v in raw]

    # Deduplica por URL
    vistos = set()
    unicas = []
    for v in vagas:
        if v["id"] not in vistos:
            vistos.add(v["id"])
            unicas.append(v)

    print(f"Gupy: {len(unicas)} vagas únicas")

    if salvar:
        saida = DATA_DIR / "gupy_vagas.json"
        with open(saida, "w", encoding="utf-8") as f:
            json.dump(unicas, f, ensure_ascii=False, indent=2)
        print(f"Salvo em {saida}")

    return unicas


if __name__ == "__main__":
    asyncio.run(executar_gupy())
