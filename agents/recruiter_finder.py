"""
Recruiter Finder — Fase 4
Localiza e-mail do recrutador/RH a partir da URL da vaga e domínio da empresa.

Estratégias (em ordem de confiança):
  1. E-mails na própria página da vaga
  2. Página de carreiras/contato da empresa (/careers, /jobs, /contato...)
  3. Página inicial com filtro por palavras-chave de RH
  4. Retorna None se não encontrar (nunca chuta)

Uso:
  py orchestrator.py enriquecer              — dry-run, mostra o que seria preenchido
  py orchestrator.py enriquecer --confirmar  — atualiza candidaturas.json com e-mails reais
"""

import re
import httpx
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
CANDIDATURAS_PATH = DATA_DIR / "candidaturas.json"

# Prefixos de e-mail associados a RH/recrutamento
_RH_KEYWORDS = {
    "hr", "rh", "people", "talent", "recruit", "career", "jobs",
    "vagas", "selecao", "selecção", "recrutamento", "hiring",
    "contratacao", "contratação", "emprego",
}

# E-mails genéricos/spam a ignorar
_BLACKLIST = {
    "noreply", "no-reply", "donotreply", "notifications", "unsubscribe",
    "support", "suporte", "help", "info", "contato", "contact",
    "newsletter", "news", "marketing", "vendas", "sales", "billing",
    "abuse", "admin", "postmaster", "webmaster",
}

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MultiVagas/1.0; job-application-tool)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
}

# Páginas de empresa a tentar
_CAREERS_PATHS = [
    "/careers", "/jobs", "/vagas", "/trabalhe-conosco",
    "/contato", "/contact", "/about", "/team", "/sobre",
]

# Job boards — o domínio da URL não é da empresa
_JOB_BOARDS = {
    "adzuna", "gupy.io", "catho", "linkedin", "remotive",
    "remoteok", "jooble", "arbeitnow", "weworkremotely",
    "glassdoor", "infojobs", "indeed", "workana", "99jobs",
}


# ──────────────────────────────────────────────
# Funções utilitárias
# ──────────────────────────────────────────────

def _extrair_emails(html: str, dominio_empresa: str = "") -> list[str]:
    """Extrai e-mails de HTML, priorizando endereços da empresa."""
    padrao = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
    todos  = {m.lower() for m in padrao.findall(html)}

    validos = [
        e for e in todos
        if len(e) <= 80
        and not any(bl in e.split("@")[0] for bl in _BLACKLIST)
        and "." in e.split("@")[1]
    ]

    if dominio_empresa:
        da_empresa = [e for e in validos if dominio_empresa in e]
        outros     = [e for e in validos if dominio_empresa not in e]
        return da_empresa + outros

    return validos


def _dominio_empresa(url: str) -> str:
    """
    Extrai o domínio da empresa da URL da vaga.
    Retorna '' quando a URL pertence a um job board externo.
    """
    try:
        host = urlparse(url).netloc.lower().replace("www.", "")
        if any(board in host for board in _JOB_BOARDS):
            return ""
        # Remove subdomínio (ex: jobs.empresa.com → empresa.com)
        partes = host.split(".")
        if len(partes) >= 3:
            host = ".".join(partes[-2:])
        return host
    except Exception:
        return ""


def _get(client: httpx.Client, url: str) -> str:
    """Faz GET seguro e retorna o HTML ou ''."""
    try:
        r = client.get(url, timeout=8)
        if r.status_code == 200:
            return r.text
    except Exception:
        pass
    return ""


# ──────────────────────────────────────────────
# Busca principal
# ──────────────────────────────────────────────

def buscar_email_recrutador(url_vaga: str, empresa: str) -> str | None:
    """
    Tenta encontrar o e-mail do recrutador/RH.

    Args:
        url_vaga: URL da página da vaga
        empresa:  Nome da empresa (para logs)

    Returns:
        E-mail encontrado (str) ou None
    """
    dominio = _dominio_empresa(url_vaga)

    with httpx.Client(headers=_HEADERS, follow_redirects=True) as c:

        # Estratégia 1 — página da vaga (só se for domínio da empresa)
        if dominio and dominio in url_vaga:
            emails = _extrair_emails(_get(c, url_vaga), dominio)
            if emails:
                melhor = _preferir_rh(emails)
                print(f"  ✓ {empresa}: {melhor} (página da vaga)")
                return melhor

        if not dominio:
            # URL é de job board, não podemos acessar o site da empresa
            return None

        # Estratégia 2 — páginas de carreiras
        for path in _CAREERS_PATHS:
            html = _get(c, f"https://{dominio}{path}")
            if html:
                emails = _extrair_emails(html, dominio)
                if emails:
                    melhor = _preferir_rh(emails)
                    print(f"  ✓ {empresa}: {melhor} ({path})")
                    return melhor

        # Estratégia 3 — página inicial
        html = _get(c, f"https://{dominio}")
        if html:
            emails = _extrair_emails(html, dominio)
            if emails:
                melhor = _preferir_rh(emails)
                print(f"  ✓ {empresa}: {melhor} (home)")
                return melhor

    print(f"  ✗ {empresa}: e-mail não encontrado")
    return None


def _preferir_rh(emails: list[str]) -> str:
    """Dentre uma lista de e-mails, prefere os que têm prefixo de RH."""
    for e in emails:
        prefixo = e.split("@")[0]
        if any(kw in prefixo for kw in _RH_KEYWORDS):
            return e
    return emails[0]


# ──────────────────────────────────────────────
# Enriquecimento em lote
# ──────────────────────────────────────────────

def enriquecer_candidaturas(dry_run: bool = True) -> int:
    """
    Percorre candidaturas.json e tenta preencher e-mails ausentes.

    Args:
        dry_run: True = mostra o que encontrou sem salvar

    Returns:
        Número de candidaturas atualizadas
    """
    import json

    if not CANDIDATURAS_PATH.exists():
        print("  candidaturas.json não encontrado")
        return 0

    with open(CANDIDATURAS_PATH, encoding="utf-8") as f:
        candidaturas = json.load(f)

    sem_email = [
        c for c in candidaturas
        if "[" in c.get("email_gerado", {}).get("para", "[")
        and c.get("url_vaga")
    ]

    if not sem_email:
        print("  Todas as candidaturas já têm e-mail preenchido")
        return 0

    print(f"  {len(sem_email)} candidatura(s) sem e-mail do recrutador")
    if dry_run:
        print("  [DRY RUN] Tentando localizar e-mails...\n")

    atualizadas = 0
    for c in sem_email:
        url    = c.get("url_vaga", "")
        empresa = c.get("empresa", "")
        email  = buscar_email_recrutador(url, empresa)

        if email:
            if not dry_run:
                c.setdefault("email_gerado", {})["para"] = email
            atualizadas += 1

    if not dry_run and atualizadas:
        with open(CANDIDATURAS_PATH, "w", encoding="utf-8") as f:
            json.dump(candidaturas, f, ensure_ascii=False, indent=2)
        print(f"\n  {atualizadas} e-mail(s) preenchido(s) em candidaturas.json")
    elif dry_run:
        print(f"\n  [DRY RUN] {atualizadas} e-mail(s) seriam preenchidos")
        print("  Execute: py orchestrator.py enriquecer --confirmar")

    return atualizadas


if __name__ == "__main__":
    enriquecer_candidaturas(dry_run=True)
