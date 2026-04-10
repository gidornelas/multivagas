"""
Agente 3 — Candidatura e Acompanhamento
Responsável pelo envio da candidatura, registro no dashboard
e agendamento de follow-ups automáticos.
"""

import json
import os
from pathlib import Path
from datetime import datetime, date, timedelta
import anthropic

# Caminhos
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
CANDIDATURAS_PATH = DATA_DIR / "candidaturas.json"

# Inicializa cliente Anthropic
client = anthropic.Anthropic()


# ──────────────────────────────────────────────
# Registro de candidaturas
# ──────────────────────────────────────────────

def carregar_candidaturas() -> list[dict]:
    """Carrega o histórico de candidaturas."""
    if CANDIDATURAS_PATH.exists():
        with open(CANDIDATURAS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def salvar_candidaturas(candidaturas: list[dict]) -> None:
    """Salva o histórico de candidaturas em JSON local."""
    with open(CANDIDATURAS_PATH, "w", encoding="utf-8") as f:
        json.dump(candidaturas, f, ensure_ascii=False, indent=2)


def registrar_candidatura(vaga: dict, resultado_curriculo: dict, tipo: str = "email") -> dict:
    """
    Registra uma nova candidatura no histórico.
    Status inicial: 'aplicada'
    """
    # Domínio estimado como placeholder — será substituído pelo e-mail real
    empresa_slug = vaga["empresa"].lower().replace(" ", "").replace(".", "")[:20]
    email_placeholder = f"[recrutador@{empresa_slug}.com]"

    candidatura = {
        "id": f"cand_{vaga['id']}_{date.today().strftime('%Y%m%d')}",
        "vaga_id": vaga["id"],
        "vaga_titulo": vaga["titulo"],
        "titulo": vaga["titulo"],
        "empresa": vaga["empresa"],
        "url_vaga": vaga.get("url", ""),
        "plataforma": vaga.get("plataforma", ""),
        "score": vaga.get("score", 0),
        "pcd_detectado": vaga.get("pcd_detectado", False),
        "idioma_vaga": vaga.get("idioma_vaga", ""),
        "pcd": vaga.get("pcd_detectado", False),
        "tipo_candidatura": tipo,
        "status": "aplicada",
        "data_aplicacao": datetime.now().isoformat(),
        "data_followup": (date.today() + timedelta(days=7)).isoformat(),
        "curriculo_path": resultado_curriculo.get("curriculo_path", ""),
        "cover_path": resultado_curriculo.get("cover_path", ""),
        "ats": resultado_curriculo.get("ats", ""),
        "keywords": resultado_curriculo.get("keywords_injetadas", []),
        # Campo email_gerado — preencha "para" com o e-mail real do recrutador
        "email_gerado": {
            "para": email_placeholder,
            "assunto": resultado_curriculo.get("_email_assunto", ""),
            "corpo": resultado_curriculo.get("_email_corpo", ""),
            "anexos": [
                Path(resultado_curriculo.get("curriculo_path", "")).name,
                Path(resultado_curriculo.get("cover_path", "")).name,
            ],
        },
        "historico": [
            {
                "data": datetime.now().isoformat(),
                "status": "aplicada",
                "nota": "Candidatura enviada"
            }
        ]
    }

    # Salva localmente
    candidaturas = carregar_candidaturas()
    candidaturas.append(candidatura)
    salvar_candidaturas(candidaturas)

    # Sincroniza com Supabase
    try:
        from db.client import upsert_candidatura
        ok = upsert_candidatura(candidatura)
        if ok:
            print(f"Supabase: candidatura {candidatura['id']} sincronizada.")
    except Exception as e:
        print(f"Supabase: erro ao sincronizar candidatura ({e})")

    print(f"Candidatura registrada: {candidatura['id']}")
    return candidatura


def atualizar_status(candidatura_id: str, novo_status: str, nota: str = "") -> bool:
    """
    Atualiza o status de uma candidatura.
    Status válidos: aplicada, visualizada, followup_pendente, em_processo, encerrada
    """
    status_validos = ["aplicada", "visualizada", "followup_pendente", "em_processo", "encerrada"]
    if novo_status not in status_validos:
        print(f"Status inválido: {novo_status}. Use: {status_validos}")
        return False

    candidaturas = carregar_candidaturas()
    for cand in candidaturas:
        if cand["id"] == candidatura_id:
            cand["status"] = novo_status
            cand["historico"].append({
                "data": datetime.now().isoformat(),
                "status": novo_status,
                "nota": nota
            })
            salvar_candidaturas(candidaturas)
            print(f"Status atualizado: {candidatura_id} → {novo_status}")
            return True

    print(f"Candidatura não encontrada: {candidatura_id}")
    return False


# ──────────────────────────────────────────────
# Dashboard e relatórios
# ──────────────────────────────────────────────

def gerar_dashboard() -> dict:
    """Gera um resumo do estado atual das candidaturas."""
    candidaturas = carregar_candidaturas()

    por_status = {}
    for cand in candidaturas:
        status = cand["status"]
        por_status[status] = por_status.get(status, 0) + 1

    # Follow-ups pendentes hoje
    hoje = date.today().isoformat()
    followups_hoje = [
        c for c in candidaturas
        if c.get("data_followup", "") <= hoje
        and c["status"] == "aplicada"
    ]

    # Top empresas por score
    top_vagas = sorted(
        [c for c in candidaturas if c["status"] != "encerrada"],
        key=lambda x: x.get("score", 0),
        reverse=True
    )[:5]

    dashboard = {
        "total_candidaturas": len(candidaturas),
        "por_status": por_status,
        "followups_urgentes": len(followups_hoje),
        "followups_detalhes": [
            {"empresa": f["empresa"], "titulo": f["titulo"], "data": f["data_followup"]}
            for f in followups_hoje
        ],
        "top_processos_ativos": [
            {"empresa": t["empresa"], "titulo": t["titulo"], "score": t["score"], "status": t["status"]}
            for t in top_vagas
        ],
        "gerado_em": datetime.now().isoformat()
    }

    return dashboard


def imprimir_dashboard() -> None:
    """Imprime o dashboard no terminal."""
    d = gerar_dashboard()

    print("\n" + "="*50)
    print("  DASHBOARD DE CANDIDATURAS")
    print("="*50)
    print(f"  Total: {d['total_candidaturas']} candidaturas")
    print()

    print("  Por status:")
    for status, qtd in d["por_status"].items():
        barra = "|" * qtd
        print(f"    {status:<20} {barra} {qtd}")

    if d["followups_urgentes"] > 0:
        print(f"\n  ⚠ Follow-ups pendentes: {d['followups_urgentes']}")
        for f in d["followups_detalhes"]:
            print(f"    · {f['empresa']} — {f['titulo']} (desde {f['data']})")

    if d["top_processos_ativos"]:
        print("\n  Top processos ativos:")
        for t in d["top_processos_ativos"]:
            print(f"    [{t['score']}] {t['empresa']} — {t['titulo']} ({t['status']})")

    print("="*50)


# ──────────────────────────────────────────────
# Geração de e-mail de candidatura
# ──────────────────────────────────────────────

def gerar_email_candidatura(vaga: dict, curriculo: dict, cover_letter: str) -> dict:
    """
    Gera o assunto e corpo do e-mail de candidatura usando o Claude.
    Adapta o tom para vagas PCD.
    """
    prompt = f"""Escreva um e-mail de candidatura profissional e direto.

CANDIDATO: {curriculo.get('nome', 'Nome')}
VAGA: {vaga['titulo']} — {vaga['empresa']}
PCD: {vaga.get('pcd_detectado', False)} ({curriculo.get('tipo_pcd', '')})

COVER LETTER (para referência de tom):
{cover_letter[:500]}

INSTRUÇÕES:
- Assunto: claro, com nome + cargo + PCD se aplicável
- Corpo: máximo 5 linhas. Menciona o cargo, 1 conquista e solicita conversa.
- Se vaga PCD: menciona condição de PCD no primeiro parágrafo
- Tom: profissional, não robotizado
- Não repita a cover letter, seja mais direto ainda

Retorne JSON:
{{"assunto": "...", "corpo": "..."}}"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}]
    )

    import re
    texto = message.content[0].text
    json_match = re.search(r'\{[\s\S]*\}', texto)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    return {
        "assunto": f"Candidatura — {vaga['titulo']} | {curriculo.get('nome', '')}",
        "corpo": "Segue em anexo meu currículo e carta de apresentação."
    }


# ──────────────────────────────────────────────
# Pipeline de candidatura (simulado — sem envio real)
# ──────────────────────────────────────────────

def executar_candidatura(vaga: dict, resultado_curriculo: dict) -> dict:
    """
    Executa o pipeline completo de candidatura para uma vaga.
    Por segurança, NÃO envia e-mail automaticamente — exibe para revisão.
    """
    print(f"\nPreparando candidatura: {vaga['titulo']} — {vaga['empresa']}")

    # Lê currículo base para contexto
    curriculo_path = DATA_DIR / "curriculo.json"
    with open(curriculo_path, "r", encoding="utf-8") as f:
        curriculo = json.load(f)

    # Lê cover letter gerada
    cover_path = Path(resultado_curriculo.get("cover_path", ""))
    cover_letter = ""
    if cover_path.exists():
        with open(cover_path, "r", encoding="utf-8") as f:
            cover_letter = f.read()

    # Gera e-mail
    email = gerar_email_candidatura(vaga, curriculo, cover_letter)

    # Passa e-mail gerado para o registro
    resultado_curriculo["_email_assunto"] = email["assunto"]
    resultado_curriculo["_email_corpo"] = email["corpo"]

    # Exibe para revisão
    empresa_slug = vaga["empresa"].lower().replace(" ", "").replace(".", "")[:20]
    print("\n" + "-"*50)
    print("  E-MAIL GERADO (revisão antes do envio):")
    print("-"*50)
    print(f"  Para: [recrutador@{empresa_slug}.com]")
    print(f"  Assunto: {email['assunto']}")
    print(f"\n  Corpo:\n{email['corpo']}")
    print(f"\n  Anexos:")
    print(f"    · {Path(resultado_curriculo.get('curriculo_path', '')).name}")
    print(f"    · {Path(resultado_curriculo.get('cover_path', '')).name}")
    print("-"*50)

    # Registra no histórico (com email_gerado incluído)
    candidatura = registrar_candidatura(vaga, resultado_curriculo, tipo="email_manual")

    # Cria evento de follow-up no Google Calendar (silencioso se libs ausentes)
    try:
        from agents.calendar_followup import criar_evento_followup
        if _tem_google_libs():
            criar_evento_followup(candidatura, dry_run=False)
    except Exception:
        pass  # Calendar é opcional — não bloqueia o pipeline

    return {
        "candidatura_id": candidatura["id"],
        "email_assunto": email["assunto"],
        "email_corpo": email["corpo"],
        "status": "aguardando_envio_manual"
    }


def _tem_google_libs() -> bool:
    try:
        import googleapiclient  # noqa: F401
        return True
    except ImportError:
        return False


if __name__ == "__main__":
    imprimir_dashboard()
