"""
Scraper — PCD Online (pcdonline.com.br)
Plataforma exclusiva para vagas PCD/inclusivas no Brasil.

Método: scraping HTTP + BeautifulSoup (sem Playwright)
Foco: vagas de design/UX/UI marcadas como PCD
"""

import re
import asyncio
import httpx
from bs4 import BeautifulSoup
from datetime import datetime

BASE_URL   = "https://www.pcdonline.com.br"
BUSCA_URL  = f"{BASE_URL}/vagas-pcd"
TERMOS     = ["design", "ux", "ui", "designer", "produto"]
HEADERS    = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
}


async def buscar_pcd_online() -> list[dict]:
    """
    Busca vagas de design/UX marcadas como PCD no PCD Online.

    Returns:
        Lista de dicts com dados brutos das vagas encontradas
    """
    vagas: list[dict] = []

    async with httpx.AsyncClient(headers=HEADERS, timeout=20, follow_redirects=True) as c:
        for termo in TERMOS:
            try:
                r = await c.get(f"{BUSCA_URL}?q={termo}&tipo=remoto")
                if r.status_code == 200:
                    vagas += _parsear_listagem(r.text, termo)
            except Exception as e:
                print(f"  PCD Online/{termo}: {e}")

    # Deduplicação por URL
    vistas: set[str] = set()
    unicas: list[dict] = []
    for v in vagas:
        if v.get("url") not in vistas:
            vistas.add(v.get("url", ""))
            unicas.append(v)

    return unicas


def _parsear_listagem(html: str, termo: str) -> list[dict]:
    """Extrai vagas da listagem HTML."""
    soup  = BeautifulSoup(html, "html.parser")
    vagas = []

    # Seletores comuns para listagens de emprego
    cartoes = (
        soup.select(".job-listing, .vaga-card, .job-card, article.vaga, .vacancy-item")
        or soup.select("ul.vagas li, .lista-vagas .item")
        or soup.find_all("article")
    )

    for cartao in cartoes:
        titulo_el  = cartao.select_one("h2, h3, .title, .cargo, .job-title")
        empresa_el = cartao.select_one(".company, .empresa, .employer")
        link_el    = cartao.select_one("a[href]")
        local_el   = cartao.select_one(".location, .localidade, .cidade")

        titulo  = titulo_el.get_text(strip=True) if titulo_el  else ""
        empresa = empresa_el.get_text(strip=True) if empresa_el else ""
        href    = link_el["href"] if link_el else ""
        local   = local_el.get_text(strip=True) if local_el else "Remoto"

        if not titulo:
            continue

        # Garante URL absoluta
        url = href if href.startswith("http") else f"{BASE_URL}{href}"

        vagas.append({
            "_raw_titulo":  titulo,
            "_raw_empresa": empresa,
            "_raw_url":     url,
            "_raw_local":   local,
            "_termo_busca": termo,
        })

    return vagas


def normalizar_pcd_online(v: dict) -> dict:
    """Normaliza para o formato padrão do pipeline."""
    slug = re.sub(r"[^a-z0-9]", "_", v.get("_raw_titulo", "").lower())[:40]
    return {
        "id":               f"pcdonline_{slug}",
        "titulo":           v.get("_raw_titulo", ""),
        "empresa":          v.get("_raw_empresa", ""),
        "descricao":        "",           # preenchido na paginação de detalhe se necessário
        "url":              v.get("_raw_url", ""),
        "salario":          "",
        "localidade":       v.get("_raw_local", "Remoto — Brasil"),
        "tags":             [],
        "data_publicacao":  datetime.now().isoformat(),
        "plataforma":       "PCD Online",
        "idioma_vaga":      "pt",
        "pcd_detectado":    True,         # todas as vagas desta plataforma são PCD
        "score":            0,
        "status":           "nova",
    }


if __name__ == "__main__":
    import asyncio
    vagas = asyncio.run(buscar_pcd_online())
    print(f"PCD Online: {len(vagas)} vagas encontradas")
    for v in vagas[:3]:
        print(f"  · {v['_raw_titulo']} — {v['_raw_empresa']}")
