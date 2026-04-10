"""
Scraper — Incluir PCD (incluirpcd.com.br)
Plataforma de vagas exclusivamente inclusivas/PCD no Brasil.

Método: scraping HTTP + BeautifulSoup
Foco: todas as vagas são PCD por definição
"""

import re
import asyncio
import httpx
from bs4 import BeautifulSoup
from datetime import datetime

BASE_URL  = "https://www.incluirpcd.com.br"
BUSCA_URL = f"{BASE_URL}/vagas"
TERMOS    = ["design", "ux", "ui designer", "designer"]
HEADERS   = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
}


async def buscar_incluir_pcd() -> list[dict]:
    """
    Busca vagas de design/UX marcadas como PCD no Incluir PCD.

    Returns:
        Lista de dicts com dados brutos das vagas
    """
    vagas: list[dict] = []

    async with httpx.AsyncClient(headers=HEADERS, timeout=20, follow_redirects=True) as c:
        for termo in TERMOS:
            try:
                r = await c.get(f"{BUSCA_URL}?busca={termo}&modalidade=home-office")
                if r.status_code == 200:
                    vagas += _parsear_listagem(r.text, termo)
            except Exception as e:
                print(f"  Incluir PCD/{termo}: {e}")

    # Deduplicação por URL
    vistas: set[str] = set()
    unicas: list[dict] = []
    for v in vagas:
        url = v.get("_raw_url", "")
        if url not in vistas:
            vistas.add(url)
            unicas.append(v)

    return unicas


def _parsear_listagem(html: str, termo: str) -> list[dict]:
    """Extrai vagas da listagem HTML do Incluir PCD."""
    soup  = BeautifulSoup(html, "html.parser")
    vagas = []

    # Incluir PCD usa estrutura de cards semelhante a outros job boards
    cartoes = (
        soup.select(".vaga-item, .job-card, .card-vaga, .listing-item, article")
        or soup.select("ul.jobs li, .jobs-list .job")
    )

    for cartao in cartoes:
        titulo_el  = cartao.select_one("h2, h3, h4, .cargo, .titulo, .job-title")
        empresa_el = cartao.select_one(".empresa, .company, .empregador")
        link_el    = cartao.select_one("a[href]")
        local_el   = cartao.select_one(".local, .cidade, .location")

        titulo  = titulo_el.get_text(strip=True)  if titulo_el  else ""
        empresa = empresa_el.get_text(strip=True) if empresa_el else ""
        href    = link_el["href"]                  if link_el    else ""
        local   = local_el.get_text(strip=True)   if local_el   else "Brasil"

        if not titulo:
            continue

        url = href if href.startswith("http") else f"{BASE_URL}{href}"

        vagas.append({
            "_raw_titulo":  titulo,
            "_raw_empresa": empresa,
            "_raw_url":     url,
            "_raw_local":   local,
            "_termo_busca": termo,
        })

    return vagas


def normalizar_incluir_pcd(v: dict) -> dict:
    """Normaliza para o formato padrão do pipeline."""
    slug = re.sub(r"[^a-z0-9]", "_", v.get("_raw_titulo", "").lower())[:40]
    return {
        "id":              f"incluirpcd_{slug}",
        "titulo":          v.get("_raw_titulo", ""),
        "empresa":         v.get("_raw_empresa", ""),
        "descricao":       "",
        "url":             v.get("_raw_url", ""),
        "salario":         "",
        "localidade":      v.get("_raw_local", "Brasil"),
        "tags":            [],
        "data_publicacao": datetime.now().isoformat(),
        "plataforma":      "Incluir PCD",
        "idioma_vaga":     "pt",
        "pcd_detectado":   True,        # todas as vagas são PCD por definição
        "score":           0,
        "status":          "nova",
    }


if __name__ == "__main__":
    vagas = asyncio.run(buscar_incluir_pcd())
    print(f"Incluir PCD: {len(vagas)} vagas encontradas")
    for v in vagas[:3]:
        print(f"  · {v['_raw_titulo']} — {v['_raw_empresa']}")
