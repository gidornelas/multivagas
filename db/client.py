"""
Cliente Supabase — Multivagas
Usado pelo api_server e pelos agentes Python.

Configure no .env:
    SUPABASE_URL=https://xxxx.supabase.co
    SUPABASE_KEY=sua_service_role_key   # service role para acesso total pelo backend
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

_client = None


def get_client():
    """Retorna instância lazy do cliente Supabase. None se não configurado."""
    global _client
    if _client is not None:
        return _client

    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_KEY", "").strip()

    if not url or not key:
        return None

    try:
        from supabase import create_client
        _client = create_client(url, key)
        return _client
    except Exception as e:
        print(f"[Supabase] Erro ao conectar: {e}")
        return None


# ── Vagas ─────────────────────────────────────────

def upsert_vagas(vagas: list[dict]) -> bool:
    """
    Insere ou atualiza vagas no Supabase.
    Campos não presentes no schema são ignorados.
    """
    sb = get_client()
    if not sb or not vagas:
        return False

    CAMPOS = {
        "id", "titulo", "empresa", "descricao", "url", "score", "plataforma",
        "idioma_vaga", "pcd_detectado", "curriculo_path", "cover_path", "tags",
        "localidade", "salario", "data_publicacao", "status",
        "skills_presentes", "gaps", "recomendacao",
    }

    def _limpar(v: dict) -> dict:
        out = {k: val for k, val in v.items() if k in CAMPOS}
        # tags, skills_presentes, gaps devem ser listas (json)
        for campo_lista in ("tags", "skills_presentes", "gaps"):
            if campo_lista not in out:
                out[campo_lista] = []
        return out

    lote_size = 200
    for i in range(0, len(vagas), lote_size):
        lote = [_limpar(v) for v in vagas[i:i + lote_size]]
        try:
            sb.table("vagas").upsert(lote, on_conflict="id").execute()
        except Exception as e:
            print(f"[Supabase] Erro upsert vagas lote {i}: {e}")
            return False

    return True


def get_vagas() -> list[dict]:
    sb = get_client()
    if not sb:
        return []
    try:
        res = sb.table("vagas").select("*").order("score", desc=True).execute()
        return res.data or []
    except Exception as e:
        print(f"[Supabase] Erro ao buscar vagas: {e}")
        return []


def marcar_curriculo_gerado(vaga_id: str, curriculo_path: str, cover_path: str) -> bool:
    sb = get_client()
    if not sb:
        return False
    try:
        sb.table("vagas").update({
            "curriculo_path": curriculo_path,
            "cover_path": cover_path,
        }).eq("id", vaga_id).execute()
        return True
    except Exception as e:
        print(f"[Supabase] Erro ao marcar curriculo gerado: {e}")
        return False


# ── Candidaturas ──────────────────────────────────

def upsert_candidatura(cand: dict) -> bool:
    sb = get_client()
    if not sb:
        return False

    CAMPOS = {
        "id", "vaga_id", "vaga_titulo", "titulo", "empresa", "url_vaga",
        "plataforma", "score", "pcd_detectado", "idioma_vaga", "tipo_candidatura",
        "status", "data_aplicacao", "data_followup", "curriculo_path", "cover_path",
        "ats", "keywords", "email_gerado", "historico",
    }
    payload = {k: v for k, v in cand.items() if k in CAMPOS}
    # Garante campos JSON
    for campo in ("keywords", "email_gerado", "historico"):
        if campo not in payload:
            payload[campo] = [] if campo != "email_gerado" else {}

    try:
        sb.table("candidaturas").upsert(payload, on_conflict="id").execute()
        return True
    except Exception as e:
        print(f"[Supabase] Erro upsert candidatura: {e}")
        return False


def get_candidaturas() -> list[dict]:
    sb = get_client()
    if not sb:
        return []
    try:
        res = (
            sb.table("candidaturas")
            .select("*")
            .order("data_aplicacao", desc=True)
            .execute()
        )
        return res.data or []
    except Exception as e:
        print(f"[Supabase] Erro ao buscar candidaturas: {e}")
        return []


# ── Currículo ─────────────────────────────────────

def get_curriculo() -> dict | None:
    sb = get_client()
    if not sb:
        return None
    try:
        res = sb.table("curriculo").select("dados").eq("id", 1).limit(1).execute()
        if res.data:
            return res.data[0]["dados"]
        return None
    except Exception as e:
        print(f"[Supabase] Erro ao buscar curriculo: {e}")
        return None


def save_curriculo(dados: dict) -> bool:
    sb = get_client()
    if not sb:
        return False
    try:
        sb.table("curriculo").upsert({"id": 1, "dados": dados}, on_conflict="id").execute()
        return True
    except Exception as e:
        print(f"[Supabase] Erro ao salvar curriculo: {e}")
        return False


# ── Config ────────────────────────────────────────

def get_config() -> dict | None:
    sb = get_client()
    if not sb:
        return None
    try:
        res = sb.table("config").select("*").eq("id", 1).limit(1).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        print(f"[Supabase] Erro ao buscar config: {e}")
        return None


def save_config(dados: dict) -> bool:
    sb = get_client()
    if not sb:
        return False
    CAMPOS = {"score_minimo", "cap_por_empresa", "idioma_preferencial", "termos_busca", "fontes_ativas"}
    payload = {"id": 1, **{k: v for k, v in dados.items() if k in CAMPOS}}
    try:
        sb.table("config").upsert(payload, on_conflict="id").execute()
        return True
    except Exception as e:
        print(f"[Supabase] Erro ao salvar config: {e}")
        return False


# ── Vaga Status ───────────────────────────────────

def upsert_vaga_status(vaga_key: str, status: str) -> bool:
    sb = get_client()
    if not sb:
        return False
    try:
        sb.table("vaga_status").upsert(
            {"vaga_key": vaga_key, "status": status},
            on_conflict="vaga_key"
        ).execute()
        return True
    except Exception as e:
        print(f"[Supabase] Erro ao salvar vaga_status: {e}")
        return False


def get_all_vaga_status() -> dict:
    """Retorna dict {vaga_key: status} para todos os registros."""
    sb = get_client()
    if not sb:
        return {}
    try:
        res = sb.table("vaga_status").select("vaga_key,status").execute()
        return {r["vaga_key"]: r["status"] for r in (res.data or [])}
    except Exception as e:
        print(f"[Supabase] Erro ao buscar vaga_status: {e}")
        return {}
