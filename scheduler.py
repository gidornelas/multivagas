"""
Scheduler — Execução diária automatizada
Coordena todas as tarefas recorrentes do sistema.

Horários:
  08:00 — Pipeline completo (busca + geração de currículos)
  09:00 — Follow-ups pendentes + digest diário por e-mail
  09:05 — Snapshot de analytics
  Dom 20:00 — Relatório semanal de performance
"""

import schedule
import time
import asyncio
from datetime import datetime
from orchestrator import (
    pipeline_completo,
    pipeline_so_dashboard,
    pipeline_digest,
    pipeline_analytics,
    pipeline_calendario,
)


def _log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] {msg}")


# ── Tarefas agendadas ─────────────────────────────────

def tarefa_pipeline() -> None:
    """Pipeline completo: busca + geração de currículos."""
    _log("Iniciando pipeline agendado...")
    asyncio.run(pipeline_completo(limite_vagas=5))


def tarefa_followups() -> None:
    """Exibe follow-ups pendentes e envia digest por e-mail."""
    _log("Verificando follow-ups e enviando digest...")

    # Dashboard no terminal
    pipeline_so_dashboard()

    # Follow-ups no Calendar (cria eventos que ainda não existem)
    try:
        pipeline_calendario(dry_run=False)
    except Exception as e:
        _log(f"Calendar: {e}")

    # Digest diário por e-mail (envia de verdade)
    try:
        pipeline_digest(dry_run=False)
    except Exception as e:
        _log(f"Digest: {e}")


def tarefa_analytics_snapshot() -> None:
    """Salva snapshot diário de analytics."""
    try:
        from agents.analytics import salvar_snapshot
        salvar_snapshot()
        _log("Snapshot de analytics salvo.")
    except Exception as e:
        _log(f"Analytics snapshot: {e}")


def tarefa_relatorio_semanal() -> None:
    """Imprime e salva relatório semanal de performance."""
    _log("Gerando relatório semanal...")
    pipeline_analytics(salvar=True)


# ── Agendamento ───────────────────────────────────────

schedule.every().day.at("08:00").do(tarefa_pipeline)
schedule.every().day.at("09:00").do(tarefa_followups)
schedule.every().day.at("09:05").do(tarefa_analytics_snapshot)
schedule.every().sunday.at("20:00").do(tarefa_relatorio_semanal)


if __name__ == "__main__":
    print("╔══════════════════════════════════════════╗")
    print("║  Multivagas Scheduler iniciado            ║")
    print("╠══════════════════════════════════════════╣")
    print("║  08:00  Pipeline completo (busca + CV)    ║")
    print("║  09:00  Follow-ups + Digest por e-mail    ║")
    print("║  09:05  Snapshot de analytics             ║")
    print("║  Dom 20h  Relatório semanal               ║")
    print("╚══════════════════════════════════════════╝")
    print("\nPressione Ctrl+C para parar.\n")

    # Roda uma vez na inicialização
    tarefa_pipeline()

    # Loop de agendamento
    while True:
        schedule.run_pending()
        time.sleep(60)
