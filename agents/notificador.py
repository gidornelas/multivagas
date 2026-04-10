"""
Notificador — Fase 4
Envia digest diário por e-mail (para si mesmo) com:
  · Top 5 novas vagas do dia (score + link)
  · Follow-ups vencidos / pendentes
  · Resumo de candidaturas ativas

Comando:
  py orchestrator.py digest              — simula (dry run)
  py orchestrator.py digest --confirmar  — envia de verdade
"""

import base64
import json
import os
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
VAGAS_PATH        = DATA_DIR / "vagas.json"
CANDIDATURAS_PATH = DATA_DIR / "candidaturas.json"


# ──────────────────────────────────────────────
# Coleta de dados
# ──────────────────────────────────────────────

def _vagas_hoje() -> list[dict]:
    """Top 5 vagas novas de hoje com score >= 80."""
    if not VAGAS_PATH.exists():
        return []
    hoje = date.today().isoformat()
    with open(VAGAS_PATH, encoding="utf-8") as f:
        vagas = json.load(f)
    novas = [
        v for v in vagas
        if v.get("score", 0) >= 80
        and v.get("data_processamento", "")[:10] == hoje
    ]
    novas.sort(key=lambda v: v.get("score", 0), reverse=True)
    return novas[:5]


def _followups_pendentes() -> list[dict]:
    """Candidaturas com follow-up vencido ou hoje."""
    if not CANDIDATURAS_PATH.exists():
        return []
    hoje = date.today().isoformat()
    with open(CANDIDATURAS_PATH, encoding="utf-8") as f:
        cands = json.load(f)
    return [
        c for c in cands
        if c.get("data_followup", "") <= hoje
        and c.get("status") in ("aplicada", "enviada")
    ]


def _resumo_candidaturas() -> dict:
    """Métricas rápidas de candidaturas."""
    if not CANDIDATURAS_PATH.exists():
        return {}
    with open(CANDIDATURAS_PATH, encoding="utf-8") as f:
        cands = json.load(f)
    from collections import Counter
    por_status = Counter(c.get("status", "nova") for c in cands)
    return {
        "total": len(cands),
        "por_status": dict(por_status),
        "em_processo": por_status.get("em_processo", 0),
    }


# ──────────────────────────────────────────────
# Montagem do HTML
# ──────────────────────────────────────────────

def _tag(cor_bg: str, cor_txt: str, texto: str) -> str:
    return (f'<span style="background:{cor_bg};color:{cor_txt};'
            f'padding:2px 7px;border-radius:4px;font-size:11px;'
            f'font-weight:700">{texto}</span>')


def _html_digest(vagas: list[dict], followups: list[dict], resumo: dict) -> str:
    hoje_fmt = date.today().strftime("%d/%m/%Y")

    # ── Vagas ────────────────────────────────
    if vagas:
        linhas_vagas = ""
        for v in vagas:
            tags = ""
            if v.get("pcd_detectado"):
                tags += " " + _tag("#dff2f3", "#2e6e73", "PCD")
            if v.get("idioma_vaga") == "pt":
                tags += " " + _tag("#e5f4ef", "#5f9889", "PT-BR")
            linhas_vagas += f"""
            <tr style="border-bottom:1px solid #e8ddd4">
              <td style="padding:10px 8px;font-size:24px;font-weight:800;
                         color:#2e6e73;text-align:center">{v.get('score',0)}</td>
              <td style="padding:10px 8px">
                <strong style="font-size:14px">{v.get('titulo','')}</strong><br>
                <span style="color:#888;font-size:12px">
                  {v.get('empresa','')} &middot; {v.get('plataforma','')}
                </span><br>
                {tags}
              </td>
              <td style="padding:10px 8px;text-align:right">
                <a href="{v.get('url','#')}"
                   style="color:#2e6e73;font-weight:700;font-size:13px">
                  Ver →
                </a>
              </td>
            </tr>"""
        bloco_vagas = f"""
        <h2 style="color:#2e6e73;margin-bottom:8px">
          ⭐ Top Vagas do Dia ({len(vagas)})
        </h2>
        <table style="width:100%;border-collapse:collapse;
                      background:#fff;border-radius:8px;overflow:hidden;
                      border:1px solid #e8ddd4">
          {linhas_vagas}
        </table>"""
    else:
        bloco_vagas = """
        <h2 style="color:#2e6e73;margin-bottom:8px">⭐ Top Vagas do Dia</h2>
        <p style="color:#aaa;font-style:italic">Nenhuma vaga nova hoje.</p>"""

    # ── Follow-ups ───────────────────────────
    if followups:
        items_fu = "".join(
            f'<li style="margin-bottom:6px">'
            f'<strong>{f.get("empresa","")}</strong> — '
            f'{f.get("vaga_titulo","")[:50]} '
            f'<span style="color:#d8ae62;font-size:12px">'
            f'(due {f.get("data_followup","")})</span></li>'
            for f in followups
        )
        bloco_fu = f"""
        <h2 style="color:#d8ae62;margin-bottom:8px">
          ⏰ Follow-ups Pendentes ({len(followups)})
        </h2>
        <ul style="line-height:1.8;padding-left:18px">{items_fu}</ul>"""
    else:
        bloco_fu = ""

    # ── Resumo ───────────────────────────────
    status_html = " &nbsp;·&nbsp; ".join(
        f"{k}: <strong>{v}</strong>"
        for k, v in resumo.get("por_status", {}).items()
    )
    bloco_resumo = f"""
        <p style="font-size:13px;color:#888;margin-top:18px">
          Total candidaturas: <strong>{resumo.get('total',0)}</strong>
          &nbsp;·&nbsp; {status_html}
        </p>"""

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;max-width:640px;
             margin:auto;background:#f4e8dd;padding:24px">

  <!-- Header -->
  <div style="background:#2e6e73;color:#fff;padding:24px 32px;
              border-radius:16px 16px 0 0">
    <h1 style="margin:0;font-size:22px;font-weight:800">
      🎯 Multivagas — Digest Diário
    </h1>
    <p style="margin:6px 0 0;opacity:.8;font-size:13px">{hoje_fmt}</p>
  </div>

  <!-- Corpo -->
  <div style="background:#faf4ee;padding:28px 32px;
              border:2px solid #d8c3ae;border-top:none;border-radius:0 0 16px 16px">
    {bloco_vagas}
    <div style="margin-top:24px">{bloco_fu}</div>
    {bloco_resumo}
    <hr style="border:none;border-top:1px solid #e8ddd4;margin:20px 0">
    <p style="font-size:11px;color:#bbb;text-align:center">
      Multivagas · digest automático ·
      <code>py orchestrator.py digest --confirmar</code>
    </p>
  </div>
</body>
</html>"""


# ──────────────────────────────────────────────
# Envio
# ──────────────────────────────────────────────

def enviar_digest(dry_run: bool = True) -> bool:
    """
    Envia o digest diário para EMAIL_REMETENTE (para si mesmo).

    Args:
        dry_run: True = apenas simula

    Returns:
        True se enviado (ou simulado) com sucesso
    """
    from dotenv import load_dotenv
    load_dotenv()

    vagas    = _vagas_hoje()
    followups = _followups_pendentes()
    resumo   = _resumo_candidaturas()

    if not vagas and not followups:
        print("  Nada a notificar hoje — nenhuma vaga nova e sem follow-ups.")
        return True

    destinatario = os.getenv("EMAIL_REMETENTE", "")
    if not destinatario:
        print("  EMAIL_REMETENTE não configurado no .env")
        return False

    assunto = (
        f"Multivagas {date.today().strftime('%d/%m')} "
        f"— {len(vagas)} vaga(s) nova(s)"
        + (f", {len(followups)} follow-up(s)" if followups else "")
    )

    html = _html_digest(vagas, followups, resumo)

    if dry_run:
        print(f"  [DRY RUN] Digest para: {destinatario}")
        print(f"  Assunto: {assunto}")
        print(f"  Vagas do dia: {len(vagas)}")
        print(f"  Follow-ups:   {len(followups)}")
        print("  Use --confirmar para enviar de verdade.")
        return True

    try:
        from googleapiclient.discovery import build
        from agents.google_auth import obter_credenciais

        msg = MIMEMultipart("alternative")
        msg["From"]    = destinatario
        msg["To"]      = destinatario
        msg["Subject"] = assunto
        msg.attach(MIMEText(html, "html", "utf-8"))

        raw     = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        creds   = obter_credenciais()
        service = build("gmail", "v1", credentials=creds)
        result  = service.users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()

        print(f"  Digest enviado! ID: {result.get('id')}")
        return True

    except Exception as e:
        print(f"  Erro ao enviar digest: {e}")
        return False


if __name__ == "__main__":
    enviar_digest(dry_run=True)
