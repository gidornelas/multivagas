"""
Gerador de PDF — Fase 2
Converte o currículo HTML adaptado em PDF usando pdfkit (wkhtmltopdf).

Instalação do wkhtmltopdf no Windows:
  Baixe em: https://wkhtmltopdf.org/downloads.html
  Instale e configure o caminho abaixo em WKHTMLTOPDF_PATH.

Alternativa sem instalação: usa o Chromium do Playwright para gerar PDF.
"""

import os
import re
from pathlib import Path

ROOT    = Path(__file__).parent.parent
OUTPUT  = ROOT / "output" / "pdfs"

# Caminho do wkhtmltopdf — ajuste se necessário
WKHTMLTOPDF_PATH = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"


# ──────────────────────────────────────────────
# Método 1: pdfkit + wkhtmltopdf
# ──────────────────────────────────────────────

def html_para_pdf_pdfkit(html_path: str, pdf_path: str = "") -> str:
    """
    Converte um arquivo HTML em PDF via pdfkit.
    Requer wkhtmltopdf instalado (https://wkhtmltopdf.org/downloads.html).
    """
    try:
        import pdfkit

        config = None
        if os.path.exists(WKHTMLTOPDF_PATH):
            config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)

        if not pdf_path:
            pdf_path = str(html_path).replace(".html", ".pdf")

        opcoes = {
            "page-size": "A4",
            "margin-top": "15mm",
            "margin-right": "15mm",
            "margin-bottom": "15mm",
            "margin-left": "15mm",
            "encoding": "UTF-8",
            "no-outline": None,
            "quiet": "",
        }

        pdfkit.from_file(str(html_path), pdf_path, options=opcoes, configuration=config)
        print(f"  PDF gerado (pdfkit): {Path(pdf_path).name}")
        return pdf_path

    except Exception as e:
        print(f"  pdfkit falhou: {e}")
        return ""


# ──────────────────────────────────────────────
# Método 2: Playwright Chromium (fallback)
# Não precisa de instalação adicional — usa o Chromium do Playwright
# ──────────────────────────────────────────────

async def html_para_pdf_playwright(html_path: str, pdf_path: str = "") -> str:
    """
    Converte HTML em PDF usando o Chromium do Playwright.
    Fallback quando wkhtmltopdf não está instalado.
    """
    try:
        from playwright.async_api import async_playwright

        if not pdf_path:
            pdf_path = str(html_path).replace(".html", ".pdf")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(f"file:///{Path(html_path).resolve()}", wait_until="load")
            await page.pdf(
                path=pdf_path,
                format="A4",
                margin={"top": "15mm", "right": "15mm", "bottom": "15mm", "left": "15mm"},
                print_background=True,
            )
            await browser.close()

        print(f"  PDF gerado (Playwright): {Path(pdf_path).name}")
        return pdf_path

    except Exception as e:
        print(f"  Playwright PDF falhou: {e}")
        return ""


# ──────────────────────────────────────────────
# Gerador principal — tenta pdfkit, depois Playwright
# ──────────────────────────────────────────────

async def gerar_pdf(html_path: str, pdf_path: str = "") -> str:
    """
    Gera PDF a partir de HTML.
    Tenta pdfkit primeiro (mais rápido), usa Playwright como fallback.
    """
    if not pdf_path:
        pdf_path = str(html_path).replace(".html", ".pdf")

    # Tenta pdfkit se wkhtmltopdf estiver instalado
    if os.path.exists(WKHTMLTOPDF_PATH):
        resultado = html_para_pdf_pdfkit(html_path, pdf_path)
        if resultado:
            return resultado

    # Fallback: Playwright Chromium
    return await html_para_pdf_playwright(html_path, pdf_path)


async def gerar_todos_pdfs() -> list[str]:
    """Converte todos os HTMLs em output/pdfs/ que ainda não têm PDF."""
    htmls = list(OUTPUT.glob("*.html"))
    gerados = []
    for html in htmls:
        pdf = html.with_suffix(".pdf")
        if not pdf.exists():
            resultado = await gerar_pdf(str(html))
            if resultado:
                gerados.append(resultado)
    print(f"\n{len(gerados)} PDF(s) gerado(s).")
    return gerados


# ──────────────────────────────────────────────
# Execução standalone
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import asyncio
    asyncio.run(gerar_todos_pdfs())
