"""
Agente 2 — Construtor de Currículo Inteligente
Transforma o currículo base em versão personalizada para cada vaga,
otimizada para o ATS específico da empresa.
"""

import json
import re
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
# Adaptação do currículo via Claude API
# ──────────────────────────────────────────────

def adaptar_curriculo(vaga: dict, curriculo_base: dict, regras_ats: dict) -> dict:
    """
    Usa a API do Claude para adaptar o currículo base para a vaga específica.
    Retorna o currículo adaptado como dicionário.
    """
    prompt = f"""Você é um especialista em currículos ATS e recrutamento de tecnologia.
Adapte o currículo base para a vaga abaixo, seguindo rigorosamente as regras do ATS.

VAGA:
Título: {vaga['titulo']}
Empresa: {vaga['empresa']}
Descrição: {vaga['descricao'][:3000]}
PCD detectado: {vaga.get('pcd_detectado', False)}

CURRÍCULO BASE:
{json.dumps(curriculo_base, ensure_ascii=False, indent=2)}

REGRAS DO ATS ({regras_ats.get('nome', 'Genérico')}):
- Colunas duplas: {'NÃO usar' if not regras_ats.get('regras', {}).get('colunas_duplas', False) else 'Permitido'}
- Ícones: {'NÃO usar' if not regras_ats.get('regras', {}).get('aceita_icones', False) else 'Permitido'}
- Keywords obrigatórias no topo: {regras_ats.get('regras', {}).get('keywords_no_topo', False)}
- Formato: {regras_ats.get('regras', {}).get('formato_ideal', 'PDF')}

INSTRUÇÕES DE ADAPTAÇÃO:
1. Extraia TODAS as keywords técnicas e comportamentais da descrição da vaga
2. Reescreva bullets de experiência para refletir as keywords mais relevantes
3. Ajuste o resumo profissional mencionando tecnologias e metodologias da vaga
4. Reordene skills para priorizar as mais relevantes para esta vaga
5. Se a vaga tem PCD, insira menção estratégica no resumo
6. Injete as top-10 keywords nas primeiras 150 palavras do resumo
7. Mantenha apenas experiências e projetos mais relevantes para esta vaga

Retorne SOMENTE JSON válido com a mesma estrutura do currículo base, mas adaptado.
Adicione os campos:
- "keywords_injetadas": ["kw1", "kw2", ...]
- "ats_nome": "nome do ATS"
- "vaga_titulo": "título da vaga"
- "vaga_empresa": "empresa"
- "adaptado_em": "ISO datetime"
"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    texto = message.content[0].text
    # Remove bloco de markdown se presente
    texto = re.sub(r'^```(?:json)?\s*', '', texto.strip())
    texto = re.sub(r'\s*```$', '', texto.strip())

    json_match = re.search(r'\{[\s\S]*\}', texto)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # Fallback: retorna currículo base com marcação de erro
    curriculo_base["erro_adaptacao"] = True
    return curriculo_base


# ──────────────────────────────────────────────
# Geração de Cover Letter
# ──────────────────────────────────────────────

def gerar_cover_letter(vaga: dict, curriculo: dict) -> str:
    """Gera cover letter personalizada para a vaga."""

    prompt = f"""Você é um especialista em candidaturas para vagas de tecnologia e design.
Escreva uma cover letter personalizada, direta e impactante.

CANDIDATO:
Nome: {curriculo.get('nome', 'Nome')}
Cargo desejado: {vaga['titulo']}
PCD: {curriculo.get('tipo_pcd', 'Não informado')}
Localidade: {curriculo.get('localidade', 'Remoto')}
Skills principais: {', '.join([s['nome'] for s in curriculo.get('skills', [])[:6]])}

VAGA:
Título: {vaga['titulo']}
Empresa: {vaga['empresa']}
Descrição: {vaga['descricao'][:2000]}
PCD detectado: {vaga.get('pcd_detectado', False)}

INSTRUÇÕES:
- Máximo 4 parágrafos, 1 página
- Tom profissional mas humano, sem ser genérico
- Parágrafo 1: abertura direta com fit imediato
- Parágrafo 2: 2-3 conquistas concretas com números quando possível
- Parágrafo 3: por que esta empresa especificamente (baseado na descrição)
- Parágrafo 4: chamada para ação clara
- Se vaga PCD: mencione deficiência auditiva + autonomia remota no parágrafo 3
- Não use frases clichê como "sou apaixonado por" ou "tenho o prazer de"

Responda APENAS com o texto da cover letter, sem markdown, sem JSON."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text


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

    # Adapta currículo
    print("  Adaptando currículo...")
    curriculo_adaptado = adaptar_curriculo(vaga, curriculo_base, ats)

    # Gera cover letter
    print("  Gerando cover letter...")
    cover_letter = gerar_cover_letter(vaga, curriculo_adaptado)

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
