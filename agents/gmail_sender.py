"""
Gmail Sender — Fase 3
Envia candidaturas por e-mail com currículo e cover letter em anexo.

IMPORTANTE: O envio só ocorre com confirmação explícita (dry_run=False).
Por padrão, apenas simula o envio (dry_run=True).
"""

import base64
import json
import os
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output" / "pdfs"
CANDIDATURAS_PATH = DATA_DIR / "candidaturas.json"


def _construir_mensagem(
    destinatario: str,
    assunto: str,
    corpo: str,
    anexos: list[str],
    remetente: str,
) -> dict:
    """Monta o objeto MIMEMultipart e retorna em formato base64 para Gmail API."""
    msg = MIMEMultipart()
    msg["From"] = remetente
    msg["To"] = destinatario
    msg["Subject"] = assunto

    msg.attach(MIMEText(corpo, "plain", "utf-8"))

    for caminho_anexo in anexos:
        p = Path(caminho_anexo)
        if not p.exists():
            print(f"  Aviso: anexo não encontrado — {p.name}")
            continue
        with open(p, "rb") as f:
            parte = MIMEBase("application", "octet-stream")
            parte.set_payload(f.read())
        encoders.encode_base64(parte)
        parte.add_header("Content-Disposition", f'attachment; filename="{p.name}"')
        msg.attach(parte)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {"raw": raw}


def enviar_email(
    destinatario: str,
    assunto: str,
    corpo: str,
    anexos: list[str] | None = None,
    dry_run: bool = True,
) -> bool:
    """
    Envia e-mail via Gmail API.

    Args:
        destinatario: e-mail do recrutador
        assunto: assunto do e-mail
        corpo: corpo em texto plano
        anexos: lista de caminhos de arquivo para anexar
        dry_run: True = apenas simula (padrão). False = envia de verdade.

    Returns:
        True se enviado (ou simulado com sucesso)
    """
    from dotenv import load_dotenv
    load_dotenv()
    remetente = os.getenv("EMAIL_REMETENTE", "")

    if not remetente:
        print("  EMAIL_REMETENTE não configurado no .env")
        return False

    anexos = anexos or []

    if dry_run:
        print(f"  [DRY RUN] Simulando envio:")
        print(f"    De:      {remetente}")
        print(f"    Para:    {destinatario}")
        print(f"    Assunto: {assunto}")
        print(f"    Anexos:  {[Path(a).name for a in anexos]}")
        return True

    try:
        from googleapiclient.discovery import build
        from agents.google_auth import obter_credenciais

        creds = obter_credenciais()
        service = build("gmail", "v1", credentials=creds)

        mensagem = _construir_mensagem(destinatario, assunto, corpo, anexos, remetente)
        result = service.users().messages().send(userId="me", body=mensagem).execute()
        print(f"  E-mail enviado! ID: {result.get('id')}")
        return True

    except Exception as e:
        print(f"  Erro ao enviar e-mail: {e}")
        return False


def enviar_candidatura(candidatura: dict, dry_run: bool = True) -> bool:
    """
    Envia a candidatura completa (e-mail + anexos) para uma vaga.

    Args:
        candidatura: dict com dados da candidatura (de candidaturas.json)
        dry_run: True = apenas simula
    """
    email_dados = candidatura.get("email_gerado", {})
    destinatario = email_dados.get("para", "")
    assunto = email_dados.get("assunto", "")
    corpo = email_dados.get("corpo", "")

    # Resolve caminhos dos anexos
    anexos = []
    for nome_arquivo in email_dados.get("anexos", []):
        caminho = OUTPUT_DIR / nome_arquivo
        if caminho.exists():
            anexos.append(str(caminho))
        else:
            # Tenta variantes de nome
            matches = list(OUTPUT_DIR.glob(f"*{Path(nome_arquivo).stem[:20]}*"))
            if matches:
                anexos.append(str(matches[0]))

    if not destinatario or "[" in destinatario:
        print(f"  E-mail do recrutador desconhecido: {destinatario}")
        print(f"  Por favor, preencha o campo 'para' em candidaturas.json")
        return False

    sucesso = enviar_email(
        destinatario=destinatario,
        assunto=assunto,
        corpo=corpo,
        anexos=anexos,
        dry_run=dry_run,
    )

    # Atualiza status na candidatura
    if sucesso and not dry_run:
        _marcar_enviada(candidatura["id"])

    return sucesso


def _marcar_enviada(candidatura_id: str):
    """Atualiza status da candidatura para 'enviada' em candidaturas.json."""
    if not CANDIDATURAS_PATH.exists():
        return
    with open(CANDIDATURAS_PATH, encoding="utf-8") as f:
        candidaturas = json.load(f)
    for c in candidaturas:
        if c["id"] == candidatura_id:
            c["status"] = "enviada"
            c["data_envio"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            break
    with open(CANDIDATURAS_PATH, "w", encoding="utf-8") as f:
        json.dump(candidaturas, f, ensure_ascii=False, indent=2)


def listar_pendentes() -> list[dict]:
    """Retorna candidaturas com e-mail gerado mas ainda não enviadas."""
    if not CANDIDATURAS_PATH.exists():
        return []
    with open(CANDIDATURAS_PATH, encoding="utf-8") as f:
        candidaturas = json.load(f)
    return [
        c for c in candidaturas
        if c.get("status") in ("aplicada", "nova")
        and c.get("email_gerado")
        and "[" not in c.get("email_gerado", {}).get("para", "[")
    ]


if __name__ == "__main__":
    print("Candidaturas com e-mail pronto para envio:")
    pendentes = listar_pendentes()
    if not pendentes:
        print("  Nenhuma candidatura com e-mail pronto.")
    for c in pendentes:
        vaga = c.get("vaga_titulo", "")
        empresa = c.get("empresa", "")
        email = c.get("email_gerado", {}).get("para", "")
        print(f"  {empresa} — {vaga} → {email}")
