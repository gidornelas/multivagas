"""
LinkedIn Message Generator — Fase 5
Gera mensagem curta para enviar ao recrutador no LinkedIn
quando a vaga não tem e-mail disponível.

Comando:
  py orchestrator.py linkedin <vaga_id>   — gera mensagem para vaga específica
  py orchestrator.py linkedin             — lista candidaturas sem e-mail
"""

import json
from pathlib import Path
import anthropic

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
VAGAS_PATH        = DATA_DIR / "vagas.json"
CANDIDATURAS_PATH = DATA_DIR / "candidaturas.json"
CURRICULO_PATH    = DATA_DIR / "curriculo.json"


def gerar_mensagem_linkedin(vaga: dict, curriculo: dict | None = None) -> str:
    """
    Gera uma mensagem curta (<300 caracteres) para enviar ao recrutador no LinkedIn.
    Usa Claude Haiku para máxima velocidade e custo mínimo.
    """
    nome = ""
    skills_top = ""
    if curriculo:
        nome = curriculo.get("nome", "")
        skills_top = ", ".join(s["nome"] for s in curriculo.get("skills", [])[:3])

    pcd_nota = ""
    if vaga.get("pcd_detectado"):
        pcd_nota = " (candidata PCD — deficiência auditiva)"

    client = anthropic.Anthropic()
    prompt = f"""Escreva uma mensagem de LinkedIn para recrutador, máximo 280 caracteres.
Tom: direto, humano, sem bajulação.
Estrutura: saudação + quem sou + interesse na vaga + pedido de contato.

Vaga: {vaga.get('titulo', '')} na {vaga.get('empresa', '')}
Candidata: {nome or 'Design Engineer/UX'}{pcd_nota}
Skills-chave: {skills_top or 'Product Design, UX, Figma'}

Retorne APENAS o texto da mensagem, sem aspas nem explicações."""

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


def gerar_e_salvar(vaga_id: str) -> dict:
    """
    Gera mensagem LinkedIn para a vaga e salva na candidatura correspondente.
    Retorna dict com vaga_id, empresa, titulo, mensagem.
    """
    if not VAGAS_PATH.exists():
        return {"erro": "vagas.json não encontrado"}

    with open(VAGAS_PATH, encoding="utf-8") as f:
        vagas = json.load(f)
    vaga = next((v for v in vagas if v["id"] == vaga_id), None)
    if not vaga:
        return {"erro": f"Vaga {vaga_id} não encontrada"}

    curriculo = None
    if CURRICULO_PATH.exists():
        with open(CURRICULO_PATH, encoding="utf-8") as f:
            curriculo = json.load(f)

    print(f"  Gerando mensagem LinkedIn para: {vaga['titulo']} — {vaga['empresa']}")
    mensagem = gerar_mensagem_linkedin(vaga, curriculo)

    # Salva na candidatura (campo linkedin_msg)
    if CANDIDATURAS_PATH.exists():
        with open(CANDIDATURAS_PATH, encoding="utf-8") as f:
            cands = json.load(f)
        for c in cands:
            if c.get("vaga_id") == vaga_id:
                c["linkedin_msg"] = mensagem
                break
        with open(CANDIDATURAS_PATH, "w", encoding="utf-8") as f:
            json.dump(cands, f, ensure_ascii=False, indent=2)

    return {
        "vaga_id": vaga_id,
        "empresa": vaga.get("empresa", ""),
        "titulo": vaga.get("titulo", ""),
        "mensagem": mensagem,
    }


def listar_sem_email() -> list[dict]:
    """Lista candidaturas que não têm e-mail do recrutador configurado."""
    if not CANDIDATURAS_PATH.exists():
        return []
    with open(CANDIDATURAS_PATH, encoding="utf-8") as f:
        cands = json.load(f)
    return [
        c for c in cands
        if not c.get("email_gerado", {}).get("para", "").strip()
    ]


if __name__ == "__main__":
    sem_email = listar_sem_email()
    print(f"{len(sem_email)} candidatura(s) sem e-mail de recrutador:")
    for c in sem_email[:10]:
        print(f"  · {c.get('empresa','')} — {c.get('vaga_titulo','')}")
