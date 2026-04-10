"""
Google Sheets Dashboard — Fase 3
Sincroniza candidaturas com planilha Google Sheets para tracking visual.

Estrutura da planilha:
  Aba "Candidaturas": todas as candidaturas com status
  Aba "Pipeline":     vagas top por score
  Aba "Resumo":       métricas agregadas

Configure GOOGLE_SHEET_ID no .env com o ID da sua planilha.
"""

import json
import os
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
CANDIDATURAS_PATH = DATA_DIR / "candidaturas.json"
VAGAS_PATH = DATA_DIR / "vagas.json"

# Cabeçalhos da aba principal
CABECALHO_CANDIDATURAS = [
    "ID", "Data", "Empresa", "Vaga", "Score", "Plataforma",
    "Status", "PCD", "PT-BR", "URL", "Currículo", "Data Envio", "Notas"
]

CABECALHO_PIPELINE = [
    "Score", "Empresa", "Vaga", "Plataforma", "PCD", "PT-BR", "URL", "Status"
]

# Mapa de status para emoji
STATUS_EMOJI = {
    "nova": "🆕",
    "aplicada": "📤",
    "enviada": "✅",
    "visualizada": "👀",
    "em_processo": "🔄",
    "follow_up": "🔔",
    "recusada": "❌",
    "encerrada": "🏁",
}


def _get_service():
    from googleapiclient.discovery import build
    from agents.google_auth import obter_credenciais
    creds = obter_credenciais()
    return build("sheets", "v4", credentials=creds)


def _get_sheet_id() -> str:
    from dotenv import load_dotenv
    load_dotenv()
    sheet_id = os.getenv("GOOGLE_SHEET_ID", "")
    if not sheet_id:
        raise ValueError(
            "GOOGLE_SHEET_ID não configurado no .env\n"
            "Crie uma planilha em sheets.google.com e adicione o ID ao .env"
        )
    return sheet_id


def _candidaturas_para_linhas() -> list[list]:
    """Converte candidaturas.json em linhas para a planilha."""
    if not CANDIDATURAS_PATH.exists():
        return []
    with open(CANDIDATURAS_PATH, encoding="utf-8") as f:
        candidaturas = json.load(f)

    linhas = [CABECALHO_CANDIDATURAS]
    for c in candidaturas:
        status = c.get("status", "nova")
        emoji = STATUS_EMOJI.get(status, "")
        linhas.append([
            c.get("id", ""),
            c.get("data_registro", ""),
            c.get("empresa", ""),
            c.get("vaga_titulo", ""),
            c.get("score", 0),
            c.get("plataforma", ""),
            f"{emoji} {status}",
            "Sim" if c.get("pcd_detectado") else "Não",
            "Sim" if c.get("idioma_vaga") == "pt" else "Não",
            c.get("url", ""),
            c.get("curriculo_path", ""),
            c.get("data_envio", ""),
            c.get("notas", ""),
        ])
    return linhas


def _pipeline_para_linhas() -> list[list]:
    """Converte top vagas de vagas.json em linhas para a aba Pipeline."""
    if not VAGAS_PATH.exists():
        return []
    with open(VAGAS_PATH, encoding="utf-8") as f:
        vagas = json.load(f)

    pipeline = [v for v in vagas if v.get("score", 0) >= 60]
    pipeline.sort(key=lambda v: v.get("score", 0), reverse=True)

    linhas = [CABECALHO_PIPELINE]
    for v in pipeline[:100]:  # máximo 100 linhas
        linhas.append([
            v.get("score", 0),
            v.get("empresa", ""),
            v.get("titulo", ""),
            v.get("plataforma", ""),
            "Sim" if v.get("pcd_detectado") else "Não",
            "Sim" if v.get("idioma_vaga") == "pt" else "Não",
            v.get("url", ""),
            v.get("status", "nova"),
        ])
    return linhas


def _resumo_para_linhas() -> list[list]:
    """Gera aba de resumo/métricas."""
    if not CANDIDATURAS_PATH.exists() or not VAGAS_PATH.exists():
        return []

    with open(CANDIDATURAS_PATH, encoding="utf-8") as f:
        candidaturas = json.load(f)
    with open(VAGAS_PATH, encoding="utf-8") as f:
        vagas = json.load(f)

    total_vagas = len(vagas)
    pipeline = sum(1 for v in vagas if v.get("score", 0) >= 80)
    total_cand = len(candidaturas)
    enviadas = sum(1 for c in candidaturas if c.get("status") == "enviada")
    em_processo = sum(1 for c in candidaturas if c.get("status") == "em_processo")
    pcd = sum(1 for c in candidaturas if c.get("pcd_detectado"))
    pt_br = sum(1 for c in candidaturas if c.get("idioma_vaga") == "pt")
    scores = [v.get("score", 0) for v in vagas if v.get("score", 0) > 0]
    score_medio = round(sum(scores) / len(scores), 1) if scores else 0

    return [
        ["Atualizado em", datetime.now().strftime("%Y-%m-%d %H:%M")],
        [],
        ["VAGAS", ""],
        ["Total coletadas", total_vagas],
        ["No pipeline (≥80)", pipeline],
        ["Score médio", score_medio],
        [],
        ["CANDIDATURAS", ""],
        ["Total geradas", total_cand],
        ["Enviadas", enviadas],
        ["Em processo", em_processo],
        ["Vagas PCD", pcd],
        ["Vagas PT-BR", pt_br],
    ]


def sincronizar(dry_run: bool = True):
    """
    Sincroniza todos os dados com o Google Sheets.

    Args:
        dry_run: True = mostra o que seria enviado, sem alterar a planilha
    """
    linhas_cand = _candidaturas_para_linhas()
    linhas_pipe = _pipeline_para_linhas()
    linhas_resumo = _resumo_para_linhas()

    total_cand = len(linhas_cand) - 1  # descontando cabeçalho
    total_pipe = len(linhas_pipe) - 1

    print(f"  Candidaturas: {total_cand} linhas")
    print(f"  Pipeline:     {total_pipe} vagas")

    if dry_run:
        print("  [DRY RUN] Simulação — nenhuma alteração na planilha")
        return

    try:
        service = _get_service()
        sheet_id = _get_sheet_id()

        def atualizar_aba(nome_aba: str, linhas: list[list]):
            """Limpa e reescreve uma aba inteira."""
            range_aba = f"{nome_aba}!A1"
            service.spreadsheets().values().clear(
                spreadsheetId=sheet_id,
                range=nome_aba,
            ).execute()
            service.spreadsheets().values().update(
                spreadsheetId=sheet_id,
                range=range_aba,
                valueInputOption="RAW",
                body={"values": linhas},
            ).execute()
            print(f"  Aba '{nome_aba}' atualizada ({len(linhas)-1} linhas)")

        atualizar_aba("Candidaturas", linhas_cand)
        atualizar_aba("Pipeline", linhas_pipe)
        atualizar_aba("Resumo", linhas_resumo)

        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
        print(f"  Planilha: {url}")

    except Exception as e:
        print(f"  Erro ao sincronizar Sheets: {e}")


def criar_estrutura_planilha():
    """
    Cria as abas necessárias na planilha se não existirem.
    Executar apenas uma vez na configuração inicial.
    """
    try:
        service = _get_service()
        sheet_id = _get_sheet_id()

        abas_novas = [
            {"addSheet": {"properties": {"title": "Candidaturas"}}},
            {"addSheet": {"properties": {"title": "Pipeline"}}},
            {"addSheet": {"properties": {"title": "Resumo"}}},
        ]

        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body={"requests": abas_novas},
        ).execute()
        print("  Abas criadas: Candidaturas, Pipeline, Resumo")

    except Exception as e:
        if "already exists" in str(e).lower():
            print("  Abas já existem na planilha")
        else:
            print(f"  Erro ao criar abas: {e}")


if __name__ == "__main__":
    print("Sincronizando com Google Sheets (dry run)...")
    sincronizar(dry_run=True)
