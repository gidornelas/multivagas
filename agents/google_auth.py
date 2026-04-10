"""
Google OAuth 2.0 — Fase 3
Autenticação para Gmail, Sheets e Calendar APIs.

Fluxo:
  1. Primeira execução: abre browser para autorizar
  2. Salva token em config/google_token.json
  3. Execuções seguintes: reutiliza token (auto-refresh)

Pré-requisitos:
  - config/google_credentials.json (baixado do Google Cloud Console)
  - Scopes: Gmail send + Sheets read/write + Calendar events
"""

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
CREDENTIALS_PATH = ROOT / "config" / "google_credentials.json"
TOKEN_PATH = ROOT / "config" / "google_token.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/calendar.events",
]


def obter_credenciais():
    """
    Retorna credenciais Google válidas.
    Na primeira execução, abre browser para autorização OAuth.
    """
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        raise ImportError(
            "Bibliotecas Google não instaladas.\n"
            "Execute: py -m pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
        )

    if not CREDENTIALS_PATH.exists():
        raise FileNotFoundError(
            f"Arquivo de credenciais não encontrado: {CREDENTIALS_PATH}\n"
            "Siga o guia em README_FASE3.md para criar o projeto no Google Cloud."
        )

    creds = None

    # Carrega token existente
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    # Renova ou faz novo login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)

        # Salva token para próximas execuções
        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
        print(f"  Token salvo em {TOKEN_PATH}")

    return creds


def testar_conexao():
    """Verifica se as credenciais estão funcionando."""
    try:
        from googleapiclient.discovery import build
        creds = obter_credenciais()
        service = build("gmail", "v1", credentials=creds)
        profile = service.users().getProfile(userId="me").execute()
        print(f"  Conectado como: {profile.get('emailAddress')}")
        return True
    except Exception as e:
        print(f"  Erro na conexão: {e}")
        return False


if __name__ == "__main__":
    print("Testando autenticação Google...")
    testar_conexao()
