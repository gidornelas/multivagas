"""
Agente 2 — Construtor de Currículo Inteligente
Transforma o currículo base em versão personalizada para cada vaga,
otimizada para o ATS específico da empresa.
Inclui análise de Fit Cultural (Fase 5).
"""

import json
import re
import time
from pathlib import Path
import anthropic

# Caminhos
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
CONFIG_DIR = ROOT / "config"
OUTPUT_DIR = ROOT / "output"
CURRICULO_PATH = DATA_DIR / "curriculo.json"
ATS_DB_PATH = CONFIG_DIR / "ats_database.json"
PDFS_DIR = OUTPUT_DIR / "pdfs"
COVERS_DIR = OUTPUT_DIR / "covers"

# Garante que os diretórios de saída existem
PDFS_DIR.mkdir(parents=True, exist_ok=True)
COVERS_DIR.mkdir(parents=True, exist_ok=True)

# Inicializa cliente Anthropic
client = anthropic.Anthropic()


# ──────────────────────────────────────────────
# Detector de ATS
# ──────────────────────────────────────────────

def detectar_ats(url_candidatura: str, ats_db: dict) -> dict:
    """Identifica o ATS a partir da URL de candidatura."""
    url_lower = url_candidatura.lower()
    for dominio, config in ats_db.get("ats_domains", {}).items():
        if dominio in url_lower:
            return config
    return ats_db.get("default", {})


def carregar_ats_db() -> dict:
    """Carrega o banco de dados de ATS."""
    with open(ATS_DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ──────────────────────────────────────────────
# Análise de Fit Cultural (Fase 5)
# ──────────────────────────────────────────────

def analisar_fit_cultural(empresa: str, url_vaga: str = "") -> dict:
    """
    Tenta buscar a página da empresa e detectar o perfil cultural.
    Retorna dict com: tipo ('startup'|'corporate'|'product'|'agency'|'unknown'),
    tom recomendado, e palavras-chave encontradas.
    Falha silenciosamente — retorna valores padrão se não conseguir buscar.
    """
    resultado = {"tipo": "unknown", "tom": "profissional e direto", "keywords": []}

    # Heurística por nome/URL antes de fazer request
    empresa_lower = empresa.lower()
    url_lower = url_vaga.lower()

    if any(k in empresa_lower for k in ["bank", "banco", "itau", "bradesco", "governo", "federal", "ministerio", "caixa"]):
        resultado.update(tipo="corporate", tom="formal e institucional",
                         keywords=["excelência", "compliance", "processos", "governança"])
        return resultado

    if any(k in empresa_lower for k in ["agency", "agência", "agencia", "studio", "criativo"]):
        resultado.update(tipo="agency", tom="criativo e colaborativo",
                         keywords=["criatividade", "colaboração", "projetos", "clientes"])
        return resultado

    try:
        import urllib.request
        import urllib.parse

        # Tenta pegar página da empresa via URL da vaga ou busca por nome
        target_url = None
        if "gupy.io" in url_lower or "inhire.io" in url_lower:
            # Extrai domínio da empresa do subdomínio da plataforma
            parts = url_lower.split(".")
            if len(parts) >= 3:
                empresa_slug = parts[0].replace("https://", "").replace("http://", "")
                target_url = f"https://{empresa_slug}.com.br/sobre"

        if not target_url:
            slug = re.sub(r"[^a-z0-9]", "", empresa_lower)[:20]
            target_url = f"https://www.{slug}.com.br/sobre"

        req = urllib.request.Request(
            target_url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; Multivagas/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            html = resp.read().decode("utf-8", errors="ignore")[:8000]

        html_lower = html.lower()
        startup_kw = ["startup", "scale-up", "inovação", "inovacao", "disruptiv", "ágil", "agil", "movimento rápido"]
        corporate_kw = ["governança", "compliance", "resultado sustentável", "décadas", "sólida", "tradição"]
        product_kw = ["produto", "product-led", "growth", "data-driven", "usuário no centro", "ux research"]

        startup_hits  = sum(1 for k in startup_kw  if k in html_lower)
        corporate_hits = sum(1 for k in corporate_kw if k in html_lower)
        product_hits   = sum(1 for k in product_kw   if k in html_lower)

        max_hits = max(startup_hits, corporate_hits, product_hits)
        if max_hits == 0:
            return resultado

        if startup_hits == max_hits:
            resultado.update(tipo="startup", tom="dinâmico, com impacto e velocidade",
                             keywords=["inovação", "agilidade", "impacto", "crescimento"])
        elif product_hits == max_hits:
            resultado.update(tipo="product", tom="centrado no usuário e orientado a dados",
                             keywords=["produto", "UX", "dados", "iteração"])
        else:
            resultado.update(tipo="corporate", tom="formal e orientado a resultados",
                             keywords=["excelência", "processos", "eficiência", "resultados"])

    except Exception:
        pass  # Falha silenciosa — retorna resultado padrão

    return resultado


# ──────────────────────────────────────────────
# Adaptação do currículo via Claude API
# ──────────────────────────────────────────────

def adaptar_curriculo_e_cover(vaga: dict, curriculo_base: dict, regras_ats: dict) -> tuple[dict, str]:
    """
    Combina adaptação de currículo + cover letter em UMA única chamada ao Claude.
    Usa Haiku para máxima velocidade. Retorna (curriculo_adaptado, cover_letter).
    """
    skills_principais = ', '.join([s['nome'] for s in curriculo_base.get('skills', [])[:6]])
    pcd = vaga.get('pcd_detectado', False)

    # Fit Cultural (Fase 5) — falha silenciosa
    fit = analisar_fit_cultural(vaga.get('empresa', ''), vaga.get('url', ''))
    fit_instrucao = ""
    if fit['tipo'] != 'unknown':
        kws = ', '.join(fit['keywords'][:3])
        fit_instrucao = (f"\nFIT CULTURAL: empresa tipo '{fit['tipo']}' — "
                         f"use tom {fit['tom']} — keywords sugeridas: {kws}")

    # Monta contexto rico do candidato para personalização
    nome_candidato = curriculo_base.get('nome', '')
    resumo_base = curriculo_base.get('resumo', '')
    exps = curriculo_base.get('experiencias', [])
    exp_recente = exps[0] if exps else {}
    cargo_recente = exp_recente.get('cargo', '')
    empresa_recente = exp_recente.get('empresa', '')
    resultados_recentes = ' | '.join(exp_recente.get('resultados', [])[:3])
    projetos = curriculo_base.get('projetos', [])
    proj_destaque = projetos[0].get('nome', '') if projetos else ''
    idiomas = curriculo_base.get('idiomas', [])
    idiomas_str = ', '.join([f"{i.get('idioma','')} ({i.get('nivel','')})" for i in idiomas])

    prompt = f"""Você é um redator sênior de candidaturas para tecnologia/design no Brasil.
Gere DUAS saídas em uma única resposta, separadas por ===COVER===.

CONTEXTO DA VAGA:
Título: {vaga['titulo']}
Empresa: {vaga['empresa']}
Descrição completa: {vaga['descricao'][:2500]}
PCD: {pcd}{fit_instrucao}

PERFIL DO CANDIDATO:
Nome: {nome_candidato}
Cargo atual/recente: {cargo_recente} na {empresa_recente}
Resumo: {resumo_base}
Skills principais: {skills_principais}
Resultados comprovados: {resultados_recentes}
Projeto em destaque: {proj_destaque}
Idiomas: {idiomas_str}

CURRÍCULO COMPLETO:
{json.dumps(curriculo_base, ensure_ascii=False, indent=2)[:3000]}

ATS: {regras_ats.get('nome', 'Genérico')} | Colunas duplas: {'NÃO' if not regras_ats.get('regras', {}).get('colunas_duplas') else 'SIM'}

PARTE 1 — JSON do currículo adaptado:
- Extraia keywords da descrição da vaga e injete no resumo e nos bullets de experiências
- Priorize skills mais relevantes para esta vaga específica
- {'Mencione PCD (deficiência auditiva) com naturalidade no resumo' if pcd else ''}
- Adicione campos: "keywords_injetadas":[], "ats_nome":"...", "vaga_titulo":"...", "vaga_empresa":"...", "fit_cultural":"..."
- Retorne JSON válido e completo

===COVER===

PARTE 2 — Cover letter em português, tom {fit['tom'] if fit['tipo'] != 'unknown' else 'direto e profissional'}:

REGRAS INEGOCIÁVEIS:
- Escreva como um ser humano real que conhece a empresa, não como template
- PROIBIDO: "sou apaixonado", "tenho o prazer", "venho por meio desta", "acredito que posso contribuir", "grande oportunidade", "desafio estimulante", "estou certo de que", "não meça esforços"
- Use frases curtas, diretas, com personalidade própria
- Mencione algo específico da descrição da vaga (um requisito, uma responsabilidade, uma tecnologia citada) — não escreva genérico
- Inclua pelo menos 1 resultado concreto com número ou impacto mensurável
- Evite adjetivos sem sustância ("proativo", "dinâmico", "dedicado")

ESTRUTURA (4 parágrafos curtos):
P1 — Abertura: conecte diretamente seu trabalho recente ({cargo_recente} na {empresa_recente}) com o que a vaga pede. Seja específico.
P2 — Prova: cite 1 ou 2 resultados reais ({resultados_recentes if resultados_recentes else 'da experiência do candidato'}). Números ou impacto concreto.
P3 — Empresa: mostre que você pesquisou — mencione algo real sobre a empresa ou o produto deles. {'Mencione sua deficiência auditiva de forma natural, destacando autonomia e comunicação assíncrona.' if pcd else ''}
P4 — Fechamento: curto, sem rodeios. Disponibilidade para conversa.

Assine como: {nome_candidato}"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    texto = message.content[0].text
    partes = texto.split("===COVER===", 1)

    # Parte 1: currículo JSON
    curriculo_adaptado = curriculo_base.copy()
    try:
        parte_json = partes[0].strip()
        parte_json = re.sub(r'^```(?:json)?\s*', '', parte_json)
        parte_json = re.sub(r'\s*```$', '', parte_json)
        json_match = re.search(r'\{[\s\S]*\}', parte_json)
        if json_match:
            curriculo_adaptado = json.loads(json_match.group())
    except (json.JSONDecodeError, Exception):
        curriculo_adaptado["erro_adaptacao"] = True

    # Parte 2: cover letter
    cover_letter = partes[1].strip() if len(partes) > 1 else ""

    return curriculo_adaptado, cover_letter


# Mantém assinaturas antigas como wrappers para compatibilidade
def adaptar_curriculo(vaga: dict, curriculo_base: dict, regras_ats: dict) -> dict:
    curriculo, _ = adaptar_curriculo_e_cover(vaga, curriculo_base, regras_ats)
    return curriculo


def gerar_cover_letter(vaga: dict, curriculo: dict) -> str:
    _, cover = adaptar_curriculo_e_cover(vaga, {}, {})
    return cover


# ──────────────────────────────────────────────
# Geração de PDF (HTML → PDF via WeasyPrint)
# ──────────────────────────────────────────────

def curriculo_para_html(curriculo: dict) -> str:
    """Converte o dicionário do currículo para HTML formatado (ATS-safe)."""
    skills = curriculo.get("skills", [])
    skills_texto = " · ".join([s["nome"] for s in skills])

    experiencias_html = ""
    for exp in curriculo.get("experiencias", []):
        bullets = "".join([f"<li>{b}</li>" for b in exp.get("descricao", [])])
        resultados = "".join([f"<li>{r}</li>" for r in exp.get("resultados", [])])
        experiencias_html += f"""
        <div class="experiencia">
            <strong>{exp.get('cargo', '')}</strong> — {exp.get('empresa', '')}
            <span class="periodo">{exp.get('periodo', '')}</span>
            <ul>{bullets}</ul>
            <ul class="resultados">{resultados}</ul>
        </div>"""

    projetos_html = ""
    for proj in curriculo.get("projetos", []):
        stack = ", ".join(proj.get("stack", []))
        projetos_html += f"""
        <div class="projeto">
            <strong>{proj.get('nome', '')}</strong> — {stack}
            <p>{proj.get('descricao', '')}</p>
        </div>"""

    educacao_html = ""
    for edu in curriculo.get("educacao", []):
        educacao_html += f"""
        <div class="educacao">
            <strong>{edu.get('curso', '')}</strong> — {edu.get('instituicao', '')} ({edu.get('ano', '')})
        </div>"""

    pcd_badge = ""
    if curriculo.get("pcd"):
        pcd_badge = f'<span class="pcd-badge">PCD — {curriculo.get("tipo_pcd", "")}</span>'

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: Arial, sans-serif; font-size: 11pt; color: #222; margin: 40px; line-height: 1.5; }}
  h1 {{ font-size: 18pt; margin-bottom: 2px; }}
  h2 {{ font-size: 12pt; border-bottom: 1px solid #ccc; padding-bottom: 4px; margin-top: 20px; }}
  .contato {{ font-size: 10pt; color: #555; margin-bottom: 8px; }}
  .pcd-badge {{ background: #e8f4fd; padding: 2px 8px; border-radius: 3px; font-size: 9pt; }}
  .skills {{ background: #f9f9f9; padding: 8px; margin: 8px 0; }}
  .experiencia, .projeto, .educacao {{ margin-bottom: 12px; }}
  .periodo {{ color: #666; font-size: 10pt; float: right; }}
  ul {{ margin: 4px 0; padding-left: 18px; }}
  .resultados li {{ font-style: italic; color: #333; }}
  a {{ color: #0066cc; text-decoration: none; }}
</style>
</head>
<body>
<h1>{curriculo.get('nome', '')}</h1>
<div class="contato">
  {curriculo.get('localidade', '')} |
  {curriculo.get('contato', {}).get('email', '')} |
  {curriculo.get('contato', {}).get('linkedin', '')} |
  {curriculo.get('contato', {}).get('portfolio', '')}
  {pcd_badge}
</div>

<h2>Resumo</h2>
<p>{curriculo.get('resumo_base', '')}</p>

<h2>Skills</h2>
<div class="skills">{skills_texto}</div>

<h2>Experiência</h2>
{experiencias_html}

<h2>Projetos</h2>
{projetos_html}

<h2>Educação</h2>
{educacao_html}

</body>
</html>"""


def salvar_curriculo_html(curriculo: dict, nome_arquivo: str) -> Path:
    """Salva o currículo como arquivo HTML."""
    html = curriculo_para_html(curriculo)
    caminho = PDFS_DIR / f"{nome_arquivo}.html"
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(html)
    return caminho


def salvar_cover_letter(texto: str, nome_arquivo: str) -> Path:
    """Salva a cover letter como arquivo TXT."""
    caminho = COVERS_DIR / f"{nome_arquivo}_cover.txt"
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(texto)
    return caminho


# ──────────────────────────────────────────────
# Pipeline principal
# ──────────────────────────────────────────────

def processar_vaga(vaga: dict) -> dict:
    """
    Processa uma vaga: detecta ATS, adapta currículo, gera cover letter.
    Retorna dicionário com caminhos dos arquivos gerados.
    """
    print(f"\nProcessando: {vaga['titulo']} — {vaga['empresa']}")

    # Carrega dados
    with open(CURRICULO_PATH, "r", encoding="utf-8") as f:
        curriculo_base = json.load(f)
    ats_db = carregar_ats_db()

    # Detecta ATS
    ats = detectar_ats(vaga.get("url", ""), ats_db)
    print(f"  ATS detectado: {ats.get('nome', 'Genérico')}")

    # Nome base do arquivo
    empresa_slug = re.sub(r'[^a-z0-9]', '-', vaga['empresa'].lower())[:20]
    titulo_slug = re.sub(r'[^a-z0-9]', '-', vaga['titulo'].lower())[:20]
    from datetime import date
    data = date.today().strftime("%Y-%m-%d")
    nome_base = f"{empresa_slug}_{titulo_slug}_{data}"

    # Adapta currículo + cover letter em uma única chamada
    print("  Gerando currículo e cover letter (chamada única)...")
    curriculo_adaptado, cover_letter = adaptar_curriculo_e_cover(vaga, curriculo_base, ats)

    # Salva arquivos
    caminho_curriculo = salvar_curriculo_html(curriculo_adaptado, nome_base)
    caminho_cover = salvar_cover_letter(cover_letter, nome_base)

    print(f"  Currículo salvo: {caminho_curriculo.name}")
    print(f"  Cover letter salva: {caminho_cover.name}")

    return {
        "vaga_id": vaga["id"],
        "ats": ats.get("nome", "Genérico"),
        "curriculo_path": str(caminho_curriculo),
        "cover_path": str(caminho_cover),
        "keywords_injetadas": curriculo_adaptado.get("keywords_injetadas", [])
    }


if __name__ == "__main__":
    # Teste com primeira vaga do pipeline
    vagas_path = DATA_DIR / "vagas.json"
    if vagas_path.exists():
        with open(vagas_path, "r", encoding="utf-8") as f:
            vagas = json.load(f)
        pipeline = [v for v in vagas if v.get("score", 0) >= 80]
        if pipeline:
            resultado = processar_vaga(pipeline[0])
            print(f"\nResultado: {resultado}")
        else:
            print("Nenhuma vaga no pipeline principal. Execute buscador.py primeiro.")
    else:
        print("Arquivo vagas.json não encontrado. Execute buscador.py primeiro.")
