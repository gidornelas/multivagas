"""
Agente 1 — Buscador e Filtrador de Vagas
Foco: vagas home office, sem inglês obrigatório, perfil Design/UX/UI.

Fontes sem autenticação:
  - Remotive API          → vagas remotas internacionais
  - RemoteOK API          → vagas remotas tech/design
  - Arbeitnow API         → vagas remotas mistas
  - We Work Remotely RSS  → vagas design remotas curadas
  - LinkedIn Jobs         → vagas BR (scraping público, 60/req)

Fontes com chave gratuita (.env):
  - Adzuna Brasil         → vagas PT-BR (developer.adzuna.com)
  - Jooble Brasil         → vagas PT-BR (jooble.org/api/about)
"""

import json
import re
import asyncio
import httpx
import os
from html import unescape
from xml.etree import ElementTree as ET
from datetime import datetime
from pathlib import Path
import anthropic
from dotenv import load_dotenv

load_dotenv()

# Caminhos
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
CURRICULO_PATH = DATA_DIR / "curriculo.json"
VAGAS_PATH = DATA_DIR / "vagas.json"

# Inicializa cliente Anthropic
client = anthropic.Anthropic()


# ──────────────────────────────────────────────
# Fonte 1: Remotive API
# ──────────────────────────────────────────────

async def buscar_remotive() -> list[dict]:
    categorias = ["design", "product", "ai-ml"]
    vagas = []
    async with httpx.AsyncClient(timeout=30) as c:
        for cat in categorias:
            try:
                r = await c.get(f"https://remotive.com/api/remote-jobs?category={cat}&limit=50")
                if r.status_code == 200:
                    vagas.extend(r.json().get("jobs", []))
            except Exception as e:
                print(f"  Remotive/{cat}: {e}")
    return vagas


def normalizar_remotive(v: dict) -> dict:
    return {
        "id": f"remotive_{v.get('id', '')}",
        "titulo": v.get("title", ""),
        "empresa": v.get("company_name", ""),
        "descricao": v.get("description", ""),
        "url": v.get("url", ""),
        "salario": v.get("salary", ""),
        "localidade": v.get("candidate_required_location", "Worldwide"),
        "tags": v.get("tags", []),
        "data_publicacao": v.get("publication_date", ""),
        "plataforma": "Remotive",
        "idioma_vaga": "en",
        "pcd_detectado": False, "score": 0, "status": "nova"
    }


# ──────────────────────────────────────────────
# Fonte 2: Remote OK API (gratuita, sem auth)
# Retorna muitas vagas de design e tech
# ──────────────────────────────────────────────

async def buscar_remoteok() -> list[dict]:
    """
    Remote OK API — JSON público, sem auth.
    Endpoint: https://remoteok.com/api
    """
    try:
        async with httpx.AsyncClient(
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0 (multivagas-job-agent/1.0)"}
        ) as c:
            r = await c.get("https://remoteok.com/api")
            if r.status_code == 200:
                dados = r.json()
                # Primeiro item é metadata, não é vaga
                return [v for v in dados if isinstance(v, dict) and v.get("id")]
    except Exception as e:
        print(f"  RemoteOK: {e}")
    return []


def normalizar_remoteok(v: dict) -> dict:
    tags = v.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",")]
    descricao = v.get("description", "") or ""
    return {
        "id": f"remoteok_{v.get('id', '')}",
        "titulo": v.get("position", ""),
        "empresa": v.get("company", ""),
        "descricao": descricao,
        "url": v.get("url", ""),
        "salario": v.get("salary", ""),
        "localidade": "Remote — Worldwide",
        "tags": tags,
        "data_publicacao": v.get("date", ""),
        "plataforma": "RemoteOK",
        "idioma_vaga": "en",
        "pcd_detectado": False, "score": 0, "status": "nova"
    }


# ──────────────────────────────────────────────
# Fonte 3: Arbeitnow API (muitas vagas PT/ES/BR)
# ──────────────────────────────────────────────

async def buscar_arbeitnow(paginas: int = 4) -> list[dict]:
    vagas = []
    async with httpx.AsyncClient(timeout=30) as c:
        for pg in range(1, paginas + 1):
            try:
                r = await c.get(f"https://www.arbeitnow.com/api/job-board-api?page={pg}")
                if r.status_code == 200:
                    remotas = [v for v in r.json().get("data", []) if v.get("remote", False)]
                    vagas.extend(remotas)
            except Exception as e:
                print(f"  Arbeitnow/p{pg}: {e}")
    return vagas


def normalizar_arbeitnow(v: dict) -> dict:
    descricao = v.get("description", "") or ""
    # Detecta idioma pela descrição
    idioma = "pt" if any(w in descricao.lower() for w in ["você", "empresa", "vaga", "remoto", "requisitos"]) else "en"
    return {
        "id": f"arbeitnow_{v.get('slug', '')}",
        "titulo": v.get("title", ""),
        "empresa": v.get("company_name", ""),
        "descricao": descricao,
        "url": v.get("url", ""),
        "salario": "",
        "localidade": "Remote",
        "tags": v.get("tags", []),
        "data_publicacao": v.get("created_at", ""),
        "plataforma": "Arbeitnow",
        "idioma_vaga": idioma,
        "pcd_detectado": False, "score": 0, "status": "nova"
    }


# ──────────────────────────────────────────────
# Fonte 4: We Work Remotely RSS (sem auth)
# 60+ vagas de design remoto curadas
# ──────────────────────────────────────────────

async def buscar_wwr() -> list[dict]:
    """Busca vagas de design no We Work Remotely via RSS."""
    urls = [
        "https://weworkremotely.com/categories/remote-design-jobs.rss",
        "https://weworkremotely.com/categories/remote-product-jobs.rss",
    ]
    vagas = []
    async with httpx.AsyncClient(timeout=30, headers={"User-Agent": "Mozilla/5.0"}) as c:
        for url in urls:
            try:
                r = await c.get(url)
                if r.status_code == 200:
                    root = ET.fromstring(r.content)
                    vagas.extend(root.findall(".//item"))
            except Exception as e:
                print(f"  WWR: {e}")
    return vagas


def normalizar_wwr(item) -> dict:
    title   = item.findtext("title", "")
    link    = item.findtext("link", "")
    region  = item.findtext("region", "Worldwide")
    desc_raw = item.findtext("description", "")
    desc    = re.sub(r"<[^>]+>", " ", unescape(desc_raw)).strip()

    # Título no formato "Empresa: Cargo"
    partes  = title.split(": ", 1)
    empresa = partes[0].strip() if len(partes) > 1 else ""
    cargo   = partes[1].strip() if len(partes) > 1 else title

    return {
        "id": f"wwr_{abs(hash(link))}",
        "titulo": cargo,
        "empresa": empresa,
        "descricao": desc[:3000],
        "url": link,
        "salario": "",
        "localidade": region or "Worldwide",
        "tags": [],
        "data_publicacao": item.findtext("pubDate", ""),
        "plataforma": "WeWorkRemotely",
        "idioma_vaga": "en",
        "pcd_detectado": False, "score": 0, "status": "nova"
    }


# ──────────────────────────────────────────────
# Fonte 5: LinkedIn Jobs (scraping público, sem auth)
# Retorna 60 vagas por busca via HTML público
# ──────────────────────────────────────────────

_LINKEDIN_TERMOS = [
    "designer+ux",
    "designer+ui+ux",
    "product+designer",
    "design+engineer",
]

async def buscar_linkedin_br() -> list[dict]:
    """
    Busca vagas no LinkedIn Brasil via endpoint público (sem login).
    Retorna os cards disponíveis sem autenticação.
    """
    from bs4 import BeautifulSoup
    vagas = []
    async with httpx.AsyncClient(
        timeout=30,
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    ) as c:
        for termo in _LINKEDIN_TERMOS:
            try:
                url = (
                    f"https://www.linkedin.com/jobs/search/"
                    f"?keywords={termo}&location=Brasil&f_WT=2"
                )
                r = await c.get(url)
                if r.status_code != 200:
                    continue
                soup = BeautifulSoup(r.text, "html.parser")
                cards = soup.find_all("div", attrs={"data-entity-urn": True})
                for card in cards:
                    titulo  = card.find("h3")
                    empresa = card.find("h4")
                    link_a  = card.find("a", href=True)
                    local_span = card.find("span", class_=lambda x: x and "location" in str(x).lower())
                    if not titulo or not link_a:
                        continue
                    vagas.append({
                        "titulo":   titulo.get_text(strip=True),
                        "empresa":  empresa.get_text(strip=True) if empresa else "",
                        "url":      link_a["href"].split("?")[0],
                        "localidade": local_span.get_text(strip=True) if local_span else "Brasil",
                    })
            except Exception as e:
                print(f"  LinkedIn/{termo}: {e}")
    return vagas


def normalizar_linkedin(v: dict) -> dict:
    url = v.get("url", "")
    return {
        "id": f"linkedin_{abs(hash(url))}",
        "titulo": v.get("titulo", ""),
        "empresa": v.get("empresa", ""),
        "descricao": "",  # Sem descrição no card público
        "url": url,
        "salario": "",
        "localidade": v.get("localidade", "Brasil"),
        "tags": [],
        "data_publicacao": "",
        "plataforma": "LinkedIn",
        "idioma_vaga": "pt",  # Busca feita no Brasil
        "pcd_detectado": False, "score": 0, "status": "nova"
    }


# ──────────────────────────────────────────────
# Fonte 7: Adzuna Brasil (chave gratuita — developer.adzuna.com)
# ──────────────────────────────────────────────

async def buscar_adzuna_brasil(termos: list[str], paginas: int = 2) -> list[dict]:
    """
    Busca vagas no Adzuna Brasil.
    Requer ADZUNA_APP_ID e ADZUNA_APP_KEY no .env (cadastro gratuito).
    """
    app_id  = os.getenv("ADZUNA_APP_ID", "")
    app_key = os.getenv("ADZUNA_APP_KEY", "")
    if not app_id or not app_key:
        return []

    vagas = []
    async with httpx.AsyncClient(timeout=30) as c:
        for termo in termos:
            for pg in range(1, paginas + 1):
                try:
                    url = (
                        f"https://api.adzuna.com/v1/api/jobs/br/search/{pg}"
                        f"?app_id={app_id}&app_key={app_key}"
                        f"&results_per_page=20&what={termo.replace(' ', '+')}"
                        f"&content-type=application/json"
                    )
                    r = await c.get(url)
                    if r.status_code == 200:
                        vagas.extend(r.json().get("results", []))
                except Exception as e:
                    print(f"  Adzuna/{termo}: {e}")
    return vagas


def normalizar_adzuna(v: dict) -> dict:
    categoria = v.get("category", {}).get("label", "")
    localidade = v.get("location", {}).get("display_name", "Brasil")
    descricao = v.get("description", "") or ""
    return {
        "id": f"adzuna_{v.get('id', '')}",
        "titulo": v.get("title", ""),
        "empresa": v.get("company", {}).get("display_name", ""),
        "descricao": descricao,
        "url": v.get("redirect_url", ""),
        "salario": str(v.get("salary_min", "") or ""),
        "localidade": localidade,
        "tags": [categoria] if categoria else [],
        "data_publicacao": v.get("created", ""),
        "plataforma": "Adzuna BR",
        "idioma_vaga": "pt",  # Adzuna BR retorna vagas em PT-BR
        "pcd_detectado": False, "score": 0, "status": "nova"
    }


# ──────────────────────────────────────────────
# Fonte 8: Jooble Brasil (chave gratuita — jooble.org/api/about)
# ──────────────────────────────────────────────

async def buscar_jooble_brasil(termos: list[str]) -> list[dict]:
    """
    Busca vagas no Jooble Brasil.
    Requer JOOBLE_API_KEY no .env (cadastro gratuito).
    """
    api_key = os.getenv("JOOBLE_API_KEY", "")
    if not api_key:
        return []

    vagas = []
    async with httpx.AsyncClient(timeout=30) as c:
        for termo in termos:
            try:
                r = await c.post(
                    f"https://br.jooble.org/api/{api_key}",
                    json={"keywords": termo, "location": "Brasil", "page": 1},
                )
                if r.status_code == 200:
                    vagas.extend(r.json().get("jobs", []))
            except Exception as e:
                print(f"  Jooble/{termo}: {e}")
    return vagas


def normalizar_jooble(v: dict) -> dict:
    return {
        "id": f"jooble_{abs(hash(v.get('link', v.get('title', ''))))}",
        "titulo": v.get("title", ""),
        "empresa": v.get("company", ""),
        "descricao": v.get("snippet", ""),
        "url": v.get("link", ""),
        "salario": v.get("salary", ""),
        "localidade": v.get("location", "Brasil"),
        "tags": [],
        "data_publicacao": v.get("updated", ""),
        "plataforma": "Jooble BR",
        "idioma_vaga": "pt",
        "pcd_detectado": False, "score": 0, "status": "nova"
    }


# ──────────────────────────────────────────────
# Filtros
# ──────────────────────────────────────────────

# Termos que indicam que a vaga é relevante para o perfil
# Foco em: Design Engineer, UX/UI Designer, Design Systems — perfil Gianny
_TERMOS_ALVO = [
    # Design Engineer (foco principal)
    "design engineer", "design systems engineer", "ui engineer",
    "ux engineer", "design technologist", "frontend designer",
    "design infrastructure", "design ops", "designops",
    # UX/UI Designer
    "ux", "ui", "user experience", "user interface",
    "product designer", "ux designer", "ui designer",
    "interface", "figma", "prototyping",
    # Visual / Web
    "visual designer", "web designer", "interaction designer",
    "motion designer", "creative technologist",
    # Genérico relevante
    "design", "front-end", "frontend", "framer",
]

# Termos que excluem a vaga definitivamente
_TERMOS_EXCLUIR = [
    "interior design", "fashion design", "mechanical engineer",
    "civil engineer", "structural engineer", "firmware", "embedded",
    "electrical engineer", "hardware engineer", "3d modeling industrial",
    "graphic designer print", "package design",
    # Engenharia física/industrial (não UX/UI)
    "mechanical design engineer", "mechanical designer",
    "physical design engineer", "asic design", "fpga design",
    "rtl design", "circuit design", "pcb design",
    "structural design", "design release engineer",
    "bulk material", "crop care", "product lifecycle engineer",
    # Auxiliar/limpeza PCD não-design (vaga afirmativa fora da área)
    "auxiliar de limpeza", "auxiliar de logística", "auxiliar administrativo pcd",
]

def eh_relevante(vaga: dict) -> bool:
    texto = f"{vaga.get('titulo', '')} {' '.join(vaga.get('tags', []))}".lower()
    for ex in _TERMOS_EXCLUIR:
        if ex in texto:
            return False
    return any(t in texto for t in _TERMOS_ALVO)


# ── Filtro de inglês obrigatório ───────────────
# Regra: bloqueia apenas inglês AVANÇADO/FLUENTE/NATIVO exigido
# Inglês básico, intermediário ou "desejável" → mantém a vaga

# Padrões que DESCARTAM a vaga
_INGLES_OBRIGATORIO = [
    # EN — fluência exigida
    "fluent in english", "fluent english", "english fluency",
    "native english speaker", "english native",
    "c1 english", "c2 english", "c1/c2",
    "advanced english required", "advanced english mandatory",
    "english is required", "english required",
    "must be fluent", "must speak english fluently",
    "strong english communication", "excellent english",
    "full professional english", "business-level english required",
    "english proficiency required", "proficient in english",
    "requires fluency in english",
    # PT-BR — fluência exigida
    "inglês avançado obrigatório", "inglês fluente obrigatório",
    "inglês nativo", "fluência em inglês obrigatória",
    "domínio do inglês obrigatório", "inglês avançado (obrigatório)",
    "inglês avançado é obrigatório", "inglês fluente é obrigatório",
]

# Padrões que MANTÊM a vaga (inglês não obrigatório ou aceitável)
_INGLES_ACEITAVEL = [
    # EN — não obrigatório
    "english is a plus", "english preferred", "english not required",
    "basic english", "conversational english",
    # PT-BR — básico/intermediário/desejável (OK para o perfil)
    "inglês básico", "inglês intermediário", "inglês desejável",
    "inglês será diferencial", "inglês não obrigatório",
    "diferencial inglês", "inglês é um diferencial",
    "nice to have", "not required", "não obrigatório",
    "desejável inglês", "conhecimento em inglês",
    "inglês para leitura",
]

def ingles_obrigatorio(vaga: dict) -> bool:
    """
    Retorna True se a vaga exige inglês avançado/fluente/nativo obrigatório.
    Inglês básico, intermediário ou desejável → retorna False (vaga mantida).
    """
    descricao = (vaga.get("descricao", "") or "").lower()
    titulo    = (vaga.get("titulo", "") or "").lower()
    texto = f"{titulo} {descricao}"

    # Marcador de "aceitável" tem prioridade — não bloqueia
    for aceito in _INGLES_ACEITAVEL:
        if aceito in texto:
            return False

    for obrig in _INGLES_OBRIGATORIO:
        if obrig in texto:
            return True

    return False


def detectar_idioma_vaga(vaga: dict) -> str:
    """Detecta se a vaga está em PT-BR (prioridade) ou outro idioma."""
    texto = (vaga.get("descricao", "") or "") + (vaga.get("titulo", "") or "")
    palavras_pt = ["você", "empresa", "vaga", "remoto", "requisitos", "experiência",
                   "conhecimento", "habilidades", "benefícios", "salário", "oportunidade",
                   "candidatar", "currículo", "envie", "nosso", "nossa", "trabalho"]
    conta = sum(1 for p in palavras_pt if p in texto.lower())
    return "pt" if conta >= 3 else "en"


def detectar_pcd(vaga: dict) -> bool:
    texto = f"{vaga.get('titulo', '')} {vaga.get('descricao', '')}".lower()
    termos = [
        "pcd", "pessoa com deficiência", "deficiência", "cota inclusiva",
        "inclusiva", "disability", "disabilities", "equal opportunity",
        "accommodation", "acessibilidade"
    ]
    return any(t in texto for t in termos)


def deduplicar(vagas_novas: list[dict], existentes: list[dict]) -> list[dict]:
    ids_existentes = {v["id"] for v in existentes}
    vistos_ids = set()
    # Chave secundária: (empresa normalizada, titulo normalizado) — evita duplicatas cross-fonte.
    # Inicializa com existentes para evitar re-adição em rodadas futuras.
    vistos_chave: set[tuple[str, str]] = set()
    for e in existentes:
        emp = re.sub(r"\s+", " ", e.get("empresa", "").lower().strip())[:40]
        tit = re.sub(r"\s+", " ", e.get("titulo", "").lower().strip())[:50]
        if emp:
            vistos_chave.add((emp, tit))
    # Cap por empresa: máximo 3 vagas de qualquer empresa (evita spam de DataAnnotation etc.)
    # Inicializa contagem a partir dos existentes também.
    _CAP_POR_EMPRESA = 3
    contagem_empresa: dict[str, int] = {}
    for e in existentes:
        emp = re.sub(r"\s+", " ", e.get("empresa", "").lower().strip())[:40]
        if emp and e.get("idioma_vaga") != "pt":
            contagem_empresa[emp] = contagem_empresa.get(emp, 0) + 1
    resultado = []
    for v in vagas_novas:
        # Filtro qualidade mínima: vaga sem empresa E sem descrição é ruído
        empresa_bruta = v.get("empresa", "").strip()
        descricao_bruta = v.get("descricao", "").strip()
        if not empresa_bruta and not descricao_bruta:
            continue

        if v["id"] in ids_existentes or v["id"] in vistos_ids:
            continue

        # Normaliza para comparação
        empresa_norm = re.sub(r"\s+", " ", empresa_bruta.lower())[:40]
        titulo_norm  = re.sub(r"\s+", " ", v.get("titulo", "").lower().strip())[:50]
        chave = (empresa_norm, titulo_norm)
        if chave in vistos_chave and empresa_norm:  # só deduplica se empresa conhecida
            continue

        # Cap por empresa (ignora empresas vazias e vagas PT-BR — não limita PT-BR)
        if empresa_norm and v.get("idioma_vaga") != "pt":
            cnt = contagem_empresa.get(empresa_norm, 0)
            if cnt >= _CAP_POR_EMPRESA:
                continue
            contagem_empresa[empresa_norm] = cnt + 1

        vistos_ids.add(v["id"])
        vistos_chave.add(chave)
        resultado.append(v)
    return resultado


# ──────────────────────────────────────────────
# Score via Claude API
# ──────────────────────────────────────────────

def calcular_score(vaga: dict, curriculo: dict) -> dict:
    skills = [s["nome"] for s in curriculo.get("skills", [])]
    exp = curriculo.get("experiencias", [])
    idioma_label = "PT-BR (prioridade)" if vaga.get("idioma_vaga") == "pt" else "Inglês"

    prompt = f"""Analise compatibilidade entre esta vaga e candidato. JSON apenas, sem markdown.

VAGA: {vaga['titulo']} — {vaga['empresa']}
IDIOMA DA VAGA: {idioma_label}
DESCRIÇÃO: {(vaga.get('descricao') or '')[:1500]}

CANDIDATO:
Skills: {', '.join(skills)}
Cargo: {exp[0].get('cargo', 'UX/UI Designer') if exp else 'UX/UI Designer'}
PCD: Deficiência Auditiva | Home Office | Inglês intermediário (não fluente)

CRITÉRIOS (score 0-100):
- Skills técnicas 35%
- Experiência relevante 25%
- Keywords ATS 25%
- Fit cultural + home office 15%
BÔNUS +5 se vaga em PT-BR ou não exige inglês avançado
BÔNUS +8 se vaga for "Design Engineer", "Design Systems Engineer" ou "Design Technologist"
BÔNUS +5 se vaga mencionar Figma, Design Systems, Storybook ou Framer explicitamente

Responda exatamente neste formato JSON:
{{"score": 0, "skills_presentes": [], "gaps": [{{"item": "", "peso": "alto"}}], "recomendacao": "", "aplicar": false}}"""

    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )
        texto = msg.content[0].text
        match = re.search(r'\{[\s\S]*\}', texto)
        if match:
            return json.loads(match.group())
        return json.loads(texto)
    except Exception as e:
        print(f"    (aviso score: {e})")
        return {"score": 50, "skills_presentes": [], "gaps": [], "recomendacao": "Score estimado", "aplicar": True}


# ──────────────────────────────────────────────
# Pipeline principal
# ──────────────────────────────────────────────

async def executar_busca() -> list[dict]:
    print("Iniciando busca de vagas...")

    with open(CURRICULO_PATH, "r", encoding="utf-8") as f:
        curriculo = json.load(f)

    existentes = []
    if VAGAS_PATH.exists():
        with open(VAGAS_PATH, "r", encoding="utf-8") as f:
            existentes = json.load(f)

    # Termos de busca para APIs PT-BR
    termos_ptbr = [
        "designer ux", "designer ui", "ux ui designer",
        "design engineer", "designer produto", "web designer"
    ]

    tem_adzuna = bool(os.getenv("ADZUNA_APP_ID") and os.getenv("ADZUNA_APP_KEY"))
    tem_jooble = bool(os.getenv("JOOBLE_API_KEY"))

    # Detecta se Playwright está disponível (Fase 2)
    try:
        import playwright  # noqa: F401
        tem_playwright = True
    except ImportError:
        tem_playwright = False

    fontes_label = "Remotive, RemoteOK, Arbeitnow, WWR, LinkedIn BR"
    if tem_adzuna:    fontes_label += ", Adzuna BR"
    if tem_jooble:    fontes_label += ", Jooble BR"
    if tem_playwright: fontes_label += ", Gupy, Catho"
    fontes_label += ", PCD Online, Incluir PCD"

    print(f"Buscando em: {fontes_label}")

    from agents.scrapers.pcd_online  import buscar_pcd_online,  normalizar_pcd_online
    from agents.scrapers.incluir_pcd import buscar_incluir_pcd, normalizar_incluir_pcd

    tarefas_base = [
        buscar_remotive(),
        buscar_remoteok(),
        buscar_arbeitnow(paginas=4),
        buscar_wwr(),
        buscar_linkedin_br(),
        buscar_adzuna_brasil(termos_ptbr) if tem_adzuna else asyncio.sleep(0),
        buscar_jooble_brasil(termos_ptbr) if tem_jooble else asyncio.sleep(0),
    ]

    # Fase 2: Gupy e Catho via Playwright
    if tem_playwright:
        from agents.scrapers.gupy  import buscar_gupy,  normalizar_gupy
        from agents.scrapers.catho import buscar_catho, normalizar_catho
        tarefas_base += [buscar_gupy(), buscar_catho()]
    else:
        tarefas_base += [asyncio.sleep(0), asyncio.sleep(0)]

    # Fase 4: plataformas PCD dedicadas
    tarefas_base += [buscar_pcd_online(), buscar_incluir_pcd()]

    resultados = await asyncio.gather(*tarefas_base, return_exceptions=True)
    remotive_raw, remoteok_raw, arbeitnow_raw, wwr_raw, linkedin_raw, \
        adzuna_raw, jooble_raw, gupy_raw, catho_raw, \
        pcd_online_raw, incluir_pcd_raw = resultados

    brutas = []
    if not isinstance(remotive_raw, Exception) and isinstance(remotive_raw, list):
        brutas += [normalizar_remotive(v) for v in remotive_raw]
        print(f"  Remotive:   {len(remotive_raw):3} vagas")
    if not isinstance(remoteok_raw, Exception) and isinstance(remoteok_raw, list):
        brutas += [normalizar_remoteok(v) for v in remoteok_raw]
        print(f"  RemoteOK:   {len(remoteok_raw):3} vagas")
    if not isinstance(arbeitnow_raw, Exception) and isinstance(arbeitnow_raw, list):
        brutas += [normalizar_arbeitnow(v) for v in arbeitnow_raw]
        print(f"  Arbeitnow:  {len(arbeitnow_raw):3} vagas remotas")
    if not isinstance(wwr_raw, Exception) and isinstance(wwr_raw, list):
        brutas += [normalizar_wwr(v) for v in wwr_raw]
        print(f"  WWR:        {len(wwr_raw):3} vagas design remoto")
    if not isinstance(linkedin_raw, Exception) and isinstance(linkedin_raw, list):
        brutas += [normalizar_linkedin(v) for v in linkedin_raw]
        print(f"  LinkedIn BR:{len(linkedin_raw):3} vagas BR")
    if tem_adzuna and not isinstance(adzuna_raw, Exception) and isinstance(adzuna_raw, list):
        brutas += [normalizar_adzuna(v) for v in adzuna_raw]
        print(f"  Adzuna BR:  {len(adzuna_raw):3} vagas PT-BR")
    if tem_jooble and not isinstance(jooble_raw, Exception) and isinstance(jooble_raw, list):
        brutas += [normalizar_jooble(v) for v in jooble_raw]
        print(f"  Jooble BR:  {len(jooble_raw):3} vagas PT-BR")
    if tem_playwright and not isinstance(gupy_raw, Exception) and isinstance(gupy_raw, list):
        brutas += [normalizar_gupy(v) for v in gupy_raw]
        print(f"  Gupy:       {len(gupy_raw):3} vagas PT-BR (Playwright)")
    if tem_playwright and not isinstance(catho_raw, Exception) and isinstance(catho_raw, list):
        brutas += [normalizar_catho(v) for v in catho_raw]
        print(f"  Catho:      {len(catho_raw):3} vagas PT-BR (Playwright)")
    if not isinstance(pcd_online_raw, Exception) and isinstance(pcd_online_raw, list):
        brutas += [normalizar_pcd_online(v) for v in pcd_online_raw]
        print(f"  PCD Online: {len(pcd_online_raw):3} vagas PCD PT-BR")
    if not isinstance(incluir_pcd_raw, Exception) and isinstance(incluir_pcd_raw, list):
        brutas += [normalizar_incluir_pcd(v) for v in incluir_pcd_raw]
        print(f"  Incluir PCD:{len(incluir_pcd_raw):3} vagas PCD PT-BR")

    print(f"\nTotal bruto: {len(brutas)}")

    # ── Filtro 1: relevância de cargo
    relevantes = [v for v in brutas if eh_relevante(v)]
    print(f"Relevantes (cargo/área):      {len(relevantes)}")

    # ── Filtro 2: inglês obrigatório → descarta
    sem_ingles_obrig = [v for v in relevantes if not ingles_obrigatorio(v)]
    descartadas_ingles = len(relevantes) - len(sem_ingles_obrig)
    print(f"Após remover inglês obrig.:   {len(sem_ingles_obrig)}  ({descartadas_ingles} removidas)")

    # ── Detecta idioma para priorização
    # Plataformas BR já definiram idioma_vaga="pt" corretamente — não sobrescrever
    _PLATAFORMAS_BR = {"Adzuna BR", "LinkedIn", "Gupy", "Catho"}
    for v in sem_ingles_obrig:
        if v.get("plataforma") not in _PLATAFORMAS_BR:
            v["idioma_vaga"] = detectar_idioma_vaga(v)

    pt_br = [v for v in sem_ingles_obrig if v["idioma_vaga"] == "pt"]
    outros = [v for v in sem_ingles_obrig if v["idioma_vaga"] != "pt"]
    print(f"  PT-BR: {len(pt_br)} | Outros idiomas: {len(outros)}")

    # PT-BR primeiro na fila
    ordenadas = pt_br + outros

    novas = deduplicar(ordenadas, existentes)
    print(f"Vagas novas (sem duplicatas):  {len(novas)}")

    if not novas:
        print("Nenhuma vaga nova encontrada.")
        return []

    # ── Score via Claude
    print(f"\nCalculando scores ({len(novas)} vagas)...")
    pontuadas = []
    for i, vaga in enumerate(novas, 1):
        vaga["pcd_detectado"] = detectar_pcd(vaga)
        idioma_label = "[PT-BR]" if vaga["idioma_vaga"] == "pt" else "[EN] "
        print(f"  [{i:2}/{len(novas)}] {idioma_label} {vaga['titulo'][:42]} — {vaga['empresa'][:20]}")
        r = calcular_score(vaga, curriculo)
        vaga["score"]           = r.get("score", 0)
        vaga["skills_presentes"]= r.get("skills_presentes", [])
        vaga["gaps"]            = r.get("gaps", [])
        vaga["recomendacao"]    = r.get("recomendacao", "")
        vaga["aplicar"]         = r.get("aplicar", False)
        vaga["data_processamento"] = datetime.now().isoformat()
        pontuadas.append(vaga)

    pontuadas.sort(key=lambda v: v["score"], reverse=True)

    pipeline  = [v for v in pontuadas if v["score"] >= 80]
    media     = [v for v in pontuadas if 60 <= v["score"] < 80]
    baixas    = [v for v in pontuadas if v["score"] < 60]

    print(f"\nResultados:")
    print(f"  Pipeline principal (>= 80): {len(pipeline)}")
    print(f"  Média prioridade  (60-79):  {len(media)}")
    print(f"  Descartadas       (< 60):   {len(baixas)}")

    # Salva local
    todas = existentes + pontuadas
    with open(VAGAS_PATH, "w", encoding="utf-8") as f:
        json.dump(todas, f, ensure_ascii=False, indent=2)
    print(f"\nSalvo em {VAGAS_PATH}")

    # Sincroniza novas vagas com Supabase (apenas as pontuadas desta rodada)
    try:
        from db.client import upsert_vagas
        ok = upsert_vagas(pontuadas)
        if ok:
            print(f"Supabase: {len(pontuadas)} vagas sincronizadas.")
        else:
            print("Supabase: não configurado ou erro — usando apenas JSON local.")
    except Exception as e:
        print(f"Supabase: erro ao sincronizar vagas ({e})")

    if pipeline:
        print(f"\nTop vagas para candidatura:")
        for v in pipeline[:5]:
            pcd  = " [PCD]"   if v.get("pcd_detectado") else ""
            lang = " [PT-BR]" if v.get("idioma_vaga") == "pt" else ""
            print(f"  [{v['score']}]{pcd}{lang} {v['titulo']} — {v['empresa']}")

    return pipeline


if __name__ == "__main__":
    asyncio.run(executar_busca())
