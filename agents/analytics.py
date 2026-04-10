"""
Analytics — Fase 4
Rastreamento de performance das candidaturas.

Métricas calculadas:
  · Taxa de resposta geral e por plataforma
  · Score médio das candidaturas respondidas vs. ignoradas
  · Keywords mais presentes nas candidaturas bem-sucedidas
  · Taxa PCD vs. não-PCD
  · Tempo médio entre envio e primeiro contato
  · Snapshots históricos (data/analytics_historico.json)

Comandos:
  py orchestrator.py analytics          — imprime relatório
  py orchestrator.py analytics --salvar — salva snapshot diário
"""

import json
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
CANDIDATURAS_PATH = DATA_DIR / "candidaturas.json"
VAGAS_PATH        = DATA_DIR / "vagas.json"
HISTORICO_PATH    = DATA_DIR / "analytics_historico.json"

# Status que indicam "contato recebido"
STATUS_CONTATO = {"em_processo", "visualizada", "entrevista", "aprovada"}
STATUS_ATIVO   = {"aplicada", "enviada", "em_processo", "visualizada", "entrevista"}


# ──────────────────────────────────────────────
# Cálculo de métricas
# ──────────────────────────────────────────────

def calcular_metricas() -> dict:
    """Calcula e retorna todas as métricas de performance."""
    if not CANDIDATURAS_PATH.exists():
        return {"total_candidaturas": 0}

    with open(CANDIDATURAS_PATH, encoding="utf-8") as f:
        candidaturas = json.load(f)

    total = len(candidaturas)
    if total == 0:
        return {"total_candidaturas": 0}

    # ── Status ──────────────────────────────
    por_status: dict[str, int] = defaultdict(int)
    for c in candidaturas:
        por_status[c.get("status", "nova")] += 1

    contatos      = sum(1 for c in candidaturas if c.get("status") in STATUS_CONTATO)
    taxa_resposta = round(contatos / total * 100, 1)

    # ── Score ───────────────────────────────
    scores_contato = [
        c.get("score", 0) for c in candidaturas
        if c.get("status") in STATUS_CONTATO and c.get("score")
    ]
    scores_todos = [c.get("score", 0) for c in candidaturas if c.get("score")]
    score_medio         = round(sum(scores_todos)  / len(scores_todos),  1) if scores_todos  else 0
    score_medio_contato = round(sum(scores_contato) / len(scores_contato), 1) if scores_contato else 0

    # ── Por plataforma ───────────────────────
    por_plat: dict[str, dict] = defaultdict(lambda: {"total": 0, "contatos": 0})
    for c in candidaturas:
        plat = c.get("plataforma", "Desconhecida")
        por_plat[plat]["total"] += 1
        if c.get("status") in STATUS_CONTATO:
            por_plat[plat]["contatos"] += 1

    por_plat_final = {}
    for plat, dados in sorted(por_plat.items(), key=lambda x: x[1]["total"], reverse=True):
        t = dados["total"]
        c = dados["contatos"]
        por_plat_final[plat] = {
            "total": t,
            "contatos": c,
            "taxa_pct": round(c / t * 100, 1) if t else 0,
        }

    # ── PCD ─────────────────────────────────
    pcd_total    = sum(1 for c in candidaturas if c.get("pcd_detectado"))
    pcd_contatos = sum(1 for c in candidaturas
                       if c.get("pcd_detectado") and c.get("status") in STATUS_CONTATO)

    # ── Tempo médio até contato (dias) ──────
    tempos: list[int] = []
    for c in candidaturas:
        if c.get("status") not in STATUS_CONTATO:
            continue
        historico = c.get("historico", [])
        if len(historico) < 2:
            continue
        try:
            t0 = datetime.fromisoformat(historico[0]["data"])
            t1 = datetime.fromisoformat(historico[-1]["data"])
            dias = (t1 - t0).days
            if 0 <= dias <= 365:
                tempos.append(dias)
        except Exception:
            pass

    tempo_medio = round(sum(tempos) / len(tempos), 1) if tempos else None

    # ── Keywords efetivas ───────────────────
    kw_counts: dict[str, int] = defaultdict(int)
    for c in candidaturas:
        if c.get("status") not in STATUS_CONTATO:
            continue
        for kw in c.get("keywords", []):
            kw_counts[kw.lower().strip()] += 1

    top_keywords = [
        {"keyword": k, "ocorrencias": v}
        for k, v in sorted(kw_counts.items(), key=lambda x: x[1], reverse=True)[:15]
    ]

    # ── Follow-ups vencidos ──────────────────
    hoje = date.today().isoformat()
    followups_vencidos = sum(
        1 for c in candidaturas
        if c.get("status") in ("aplicada", "enviada")
        and c.get("data_followup", "") <= hoje
    )

    return {
        "gerado_em":             date.today().isoformat(),
        "total_candidaturas":    total,
        "taxa_resposta_pct":     taxa_resposta,
        "score_medio":           score_medio,
        "score_medio_contato":   score_medio_contato,
        "por_status":            dict(por_status),
        "por_plataforma":        por_plat_final,
        "pcd": {
            "total":    pcd_total,
            "contatos": pcd_contatos,
            "taxa_pct": round(pcd_contatos / pcd_total * 100, 1) if pcd_total else 0,
        },
        "tempo_medio_contato_dias": tempo_medio,
        "top_keywords_efetivas": top_keywords,
        "followups_vencidos":    followups_vencidos,
    }


# ──────────────────────────────────────────────
# Impressão no terminal
# ──────────────────────────────────────────────

def imprimir_relatorio() -> None:
    """Imprime relatório de analytics no terminal."""
    m = calcular_metricas()

    if not m.get("total_candidaturas"):
        print("  Sem candidaturas registradas — nada a analisar.")
        return

    print("\n" + "=" * 55)
    print("  ANALYTICS DE CANDIDATURAS")
    print("=" * 55)
    print(f"  Total candidaturas:      {m['total_candidaturas']}")
    print(f"  Taxa de resposta:        {m['taxa_resposta_pct']}%")
    print(f"  Score médio (todos):     {m['score_medio']}")
    print(f"  Score médio (contatos):  {m['score_medio_contato']}")
    if m.get("tempo_medio_contato_dias") is not None:
        print(f"  Tempo médio p/ contato:  {m['tempo_medio_contato_dias']} dias")
    if m.get("followups_vencidos"):
        print(f"  Follow-ups vencidos:     {m['followups_vencidos']} ⚠")

    print("\n  Por status:")
    for status, qtd in sorted(m["por_status"].items(), key=lambda x: x[1], reverse=True):
        barra = "█" * min(qtd, 20)
        print(f"    {status:<22} {barra} {qtd}")

    print("\n  Por plataforma (total · contatos · taxa):")
    for plat, d in m["por_plataforma"].items():
        print(f"    {plat:<22} {d['total']:3} vagas · "
              f"{d['contatos']} contatos · {d['taxa_pct']}%")

    pcd = m.get("pcd", {})
    if pcd.get("total"):
        print(f"\n  Vagas PCD: {pcd['contatos']}/{pcd['total']} contatos ({pcd['taxa_pct']}%)")

    if m.get("top_keywords_efetivas"):
        print("\n  Top keywords em candidaturas com contato:")
        for kw in m["top_keywords_efetivas"][:8]:
            print(f"    · {kw['keyword']:<28} {kw['ocorrencias']}×")

    print("=" * 55)


# ──────────────────────────────────────────────
# Snapshot histórico
# ──────────────────────────────────────────────

def salvar_snapshot() -> None:
    """
    Salva um snapshot diário das métricas em data/analytics_historico.json.
    Mantém os últimos 90 snapshots.
    """
    m = calcular_metricas()
    if not m.get("total_candidaturas"):
        return

    historico: list[dict] = []
    if HISTORICO_PATH.exists():
        with open(HISTORICO_PATH, encoding="utf-8") as f:
            historico = json.load(f)

    # Evita duplicata do mesmo dia
    historico = [h for h in historico if h.get("gerado_em") != m["gerado_em"]]
    historico.append(m)
    historico = historico[-90:]  # mantém últimos 90 dias

    with open(HISTORICO_PATH, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)

    print(f"  Snapshot salvo em data/analytics_historico.json "
          f"({len(historico)} entradas)")


def tendencia(metrica: str = "taxa_resposta_pct", ultimas: int = 7) -> list[dict]:
    """Retorna a evolução de uma métrica nos últimos N snapshots."""
    if not HISTORICO_PATH.exists():
        return []
    with open(HISTORICO_PATH, encoding="utf-8") as f:
        historico = json.load(f)
    return [
        {"data": h["gerado_em"], "valor": h.get(metrica)}
        for h in historico[-ultimas:]
    ]


if __name__ == "__main__":
    imprimir_relatorio()
