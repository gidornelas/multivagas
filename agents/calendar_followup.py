"""
Google Calendar Follow-up — Fase 3
Cria eventos de lembrete no Google Calendar para cada candidatura enviada.

Fluxo:
  executar_candidatura() chama criar_evento_followup() ao registrar uma candidatura.
  O evento é criado 7 dias após o envio, das 09:00 às 09:30, com alerta por e-mail.

Comandos via orchestrator:
  py orchestrator.py calendario              — simula criação de eventos pendentes
  py orchestrator.py calendario --confirmar  — cria eventos de verdade
"""

import json
from datetime import datetime, timedelta, date
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
CANDIDATURAS_PATH = DATA_DIR / "candidaturas.json"

TIMEZONE = "America/Sao_Paulo"


# ──────────────────────────────────────────────
# Criar evento único
# ──────────────────────────────────────────────

def criar_evento_followup(candidatura: dict, dry_run: bool = True) -> bool:
    """
    Cria um evento de follow-up no Google Calendar para uma candidatura.

    Args:
        candidatura: dict com dados da candidatura
        dry_run: True = apenas simula (padrão)

    Returns:
        True se criado (ou simulado com sucesso)
    """
    empresa       = candidatura.get("empresa", "Empresa")
    vaga          = candidatura.get("vaga_titulo", candidatura.get("titulo", "Vaga"))
    data_followup = candidatura.get("data_followup", "")
    url_vaga      = candidatura.get("url_vaga", "")
    score         = candidatura.get("score", 0)
    pcd           = candidatura.get("pcd_detectado", False)

    if not data_followup:
        print(f"  Sem data de follow-up para {empresa}")
        return False

    try:
        data_dt = datetime.strptime(data_followup[:10], "%Y-%m-%d")
    except ValueError:
        print(f"  Data inválida: {data_followup}")
        return False

    titulo   = f"Follow-up — {empresa} ({vaga[:35]})"
    pcd_nota = " [VAGA PCD]" if pcd else ""
    descricao = (
        f"Score: {score}/100{pcd_nota}\n"
        f"Candidatura enviada em: {candidatura.get('data_aplicacao', '')[:10]}\n"
        f"URL da vaga: {url_vaga}\n\n"
        "Ações sugeridas:\n"
        "• Se não houve resposta: envie e-mail de follow-up gentil\n"
        "• Modelo: 'Gostaria de reafirmar meu interesse na vaga de [cargo]...'\n"
        "• Aguarde mais 7 dias antes de um segundo contato"
    )

    inicio = data_dt.strftime("%Y-%m-%dT09:00:00")
    fim    = data_dt.strftime("%Y-%m-%dT09:30:00")

    if dry_run:
        print(f"  [DRY RUN] {titulo}")
        print(f"    Data: {data_followup} 09:00–09:30")
        return True

    try:
        from googleapiclient.discovery import build
        from agents.google_auth import obter_credenciais

        creds   = obter_credenciais()
        service = build("calendar", "v3", credentials=creds)

        evento = {
            "summary":     titulo,
            "description": descricao,
            "start": {"dateTime": inicio, "timeZone": TIMEZONE},
            "end":   {"dateTime": fim,    "timeZone": TIMEZONE},
            "colorId": "5",  # banana (amarelo) — fácil de localizar
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email",  "minutes": 60 * 24},  # 1 dia antes
                    {"method": "popup",  "minutes": 30},
                ],
            },
        }

        result = service.events().insert(calendarId="primary", body=evento).execute()
        link   = result.get("htmlLink", "")
        print(f"  Evento criado: {titulo}")
        if link:
            print(f"    {link}")

        _marcar_evento_criado(candidatura["id"], result["id"])
        return True

    except Exception as e:
        print(f"  Erro ao criar evento Calendar: {e}")
        return False


# ──────────────────────────────────────────────
# Criação em lote
# ──────────────────────────────────────────────

def criar_eventos_pendentes(dry_run: bool = True) -> int:
    """
    Cria eventos de follow-up para todas as candidaturas que ainda não têm evento.

    Returns:
        Número de eventos criados (ou simulados)
    """
    if not CANDIDATURAS_PATH.exists():
        print("  candidaturas.json não encontrado")
        return 0

    with open(CANDIDATURAS_PATH, encoding="utf-8") as f:
        candidaturas = json.load(f)

    pendentes = [
        c for c in candidaturas
        if c.get("status") in ("aplicada", "enviada")
        and not c.get("calendar_event_id")
        and c.get("data_followup")
    ]

    if not pendentes:
        print("  Nenhuma candidatura pendente de evento Calendar")
        return 0

    print(f"  {len(pendentes)} candidatura(s) sem evento Calendar:")
    criados = 0
    for c in pendentes:
        if criar_evento_followup(c, dry_run=dry_run):
            criados += 1

    if not dry_run:
        print(f"\n  {criados}/{len(pendentes)} evento(s) criado(s) no Calendar")
    return criados


# ──────────────────────────────────────────────
# Follow-ups pendentes hoje
# ──────────────────────────────────────────────

def listar_followups_hoje() -> list[dict]:
    """Retorna candidaturas com follow-up vencido hoje ou atrasado."""
    if not CANDIDATURAS_PATH.exists():
        return []

    hoje = date.today().isoformat()
    with open(CANDIDATURAS_PATH, encoding="utf-8") as f:
        candidaturas = json.load(f)

    return [
        c for c in candidaturas
        if c.get("data_followup", "") <= hoje
        and c.get("status") in ("aplicada", "enviada")
    ]


def imprimir_followups_hoje() -> None:
    """Imprime follow-ups pendentes no terminal."""
    pendentes = listar_followups_hoje()
    hoje = date.today().isoformat()

    print(f"\n{'='*50}")
    print("  FOLLOW-UPS PENDENTES")
    print(f"  (hoje: {hoje})")
    print(f"{'='*50}")

    if not pendentes:
        print("  Nenhum follow-up pendente hoje.")
        print(f"{'='*50}")
        return

    print(f"  {len(pendentes)} candidatura(s) aguardando follow-up:\n")
    for c in pendentes:
        pcd = " [PCD]" if c.get("pcd_detectado") else ""
        atrasado = " ⚠ ATRASADO" if c.get("data_followup", "") < hoje else ""
        print(f"  · {c.get('empresa',''):<25} {c.get('vaga_titulo','')[:35]}")
        print(f"    Follow-up: {c.get('data_followup','')}{pcd}{atrasado}")
        print(f"    Score: {c.get('score',0)}  |  Status: {c.get('status','')}")

    print(f"{'='*50}")
    print("  Use: py orchestrator.py calendario --confirmar")
    print("  para criar eventos de acompanhamento no Google Calendar.")
    print(f"{'='*50}")


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _marcar_evento_criado(candidatura_id: str, event_id: str) -> None:
    """Registra o calendar_event_id na candidatura."""
    if not CANDIDATURAS_PATH.exists():
        return
    with open(CANDIDATURAS_PATH, encoding="utf-8") as f:
        candidaturas = json.load(f)
    for c in candidaturas:
        if c["id"] == candidatura_id:
            c["calendar_event_id"] = event_id
            break
    with open(CANDIDATURAS_PATH, "w", encoding="utf-8") as f:
        json.dump(candidaturas, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    imprimir_followups_hoje()
