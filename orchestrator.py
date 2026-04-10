"""
Orquestrador Principal — Multi-Agente de Vagas
Coordena os três agentes: Buscador → Currículo → Candidatura
"""

import json
import asyncio
from pathlib import Path

from agents.buscador import executar_busca
from agents.curriculo import processar_vaga
from agents.candidatura import executar_candidatura, imprimir_dashboard
from agents.gerador_pdf import gerar_pdf, gerar_todos_pdfs

# Fase 3 — importação condicional (só carrega se libs instaladas)
def _tem_google_libs() -> bool:
    try:
        import googleapiclient  # noqa
        return True
    except ImportError:
        return False

DATA_DIR = Path(__file__).parent / "data"
VAGAS_PATH = DATA_DIR / "vagas.json"


def carregar_pipeline(score_minimo: int = 80) -> list[dict]:
    """Carrega vagas do arquivo com score >= mínimo, ordenadas por score desc."""
    if not VAGAS_PATH.exists():
        return []
    with open(VAGAS_PATH, "r", encoding="utf-8") as f:
        vagas = json.load(f)
    pipeline = [v for v in vagas if v.get("score", 0) >= score_minimo]
    pipeline.sort(key=lambda v: v["score"], reverse=True)
    return pipeline


async def pipeline_completo(limite_vagas: int = 5) -> None:
    """
    Executa o pipeline completo:
    1. Busca vagas novas e adiciona ao banco
    2. Carrega todas as vagas do pipeline (score >= 80)
    3. Gera currículo adaptado + cover letter para cada uma
    4. Prepara rascunho de candidatura para revisão manual (NÃO envia)
    """
    print("\n" + "="*55)
    print("  MULTI-AGENTE DE VAGAS — PIPELINE COMPLETO")
    print("="*55)

    # ── Fase 1: Busca de novas vagas ───────────────────
    print("\n[FASE 1] Buscando vagas novas...")
    await executar_busca()

    # ── Carrega pipeline completo do arquivo ──────────
    pipeline = carregar_pipeline(score_minimo=80)
    print(f"\n{len(pipeline)} vaga(s) no pipeline principal (score >= 80).")

    if not pipeline:
        print("Nenhuma vaga no pipeline. Tente reduzir o score mínimo.")
        imprimir_dashboard()
        return

    # Filtra as que ainda não têm currículo gerado
    sem_curriculo = [v for v in pipeline if not v.get("curriculo_path")]
    ja_processadas = len(pipeline) - len(sem_curriculo)

    if ja_processadas:
        print(f"  {ja_processadas} já processadas anteriormente — pulando.")
    print(f"  {len(sem_curriculo)} aguardando geração de currículo.")

    vagas_processar = sem_curriculo[:limite_vagas]
    if not vagas_processar:
        print("\nTodas as vagas do pipeline já foram processadas.")
        imprimir_dashboard()
        return

    print(f"  Processando {len(vagas_processar)} agora (paralelo).\n")

    # ── Fase 2: Currículo adaptado — paralelo ──────────
    from concurrent.futures import ThreadPoolExecutor, as_completed
    MAX_WORKERS = min(4, len(vagas_processar))  # máx 4 chamadas simultâneas
    print(f"[FASE 2] Gerando currículos e cover letters ({MAX_WORKERS} em paralelo)...")
    resultados = []

    def _processar(vaga):
        resultado = processar_vaga(vaga)
        resultado["vaga"] = vaga
        _marcar_processada(vaga["id"], resultado)
        return resultado

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futuros = {ex.submit(_processar, v): v for v in vagas_processar}
        for fut in as_completed(futuros):
            vaga = futuros[fut]
            try:
                resultados.append(fut.result())
            except Exception as e:
                print(f"  Erro em {vaga['titulo']}: {e}")

    # ── Fase 3: Rascunhos de candidatura ───────────────
    print("\n[FASE 3] Preparando rascunhos de candidatura (sem envio)...")
    for item in resultados:
        try:
            res = executar_candidatura(item["vaga"], item)
            print(f"  Preparado: {res['candidatura_id']}")
        except Exception as e:
            print(f"  Erro candidatura: {e}")

    # ── Dashboard ──────────────────────────────────────
    # ── Fase 2: Gera PDFs a partir dos HTMLs ──────────
    print("\n[FASE 2.5] Gerando PDFs...")
    await gerar_todos_pdfs()

    print("\n[RESULTADO FINAL]")
    imprimir_dashboard()


def _marcar_processada(vaga_id: str, resultado: dict) -> None:
    """Atualiza vagas.json registrando os caminhos dos arquivos gerados."""
    with open(VAGAS_PATH, "r", encoding="utf-8") as f:
        vagas = json.load(f)
    for v in vagas:
        if v["id"] == vaga_id:
            v["curriculo_path"] = resultado.get("curriculo_path", "")
            v["cover_path"]     = resultado.get("cover_path", "")
            break
    with open(VAGAS_PATH, "w", encoding="utf-8") as f:
        json.dump(vagas, f, ensure_ascii=False, indent=2)


def pipeline_processar_pipeline(limite: int = 5) -> None:
    """
    Processa vagas já buscadas que ainda não têm currículo gerado.
    Útil para rodar sem repetir a busca.
    """
    print("\n" + "="*55)
    print("  GERANDO CURRICULOS — PIPELINE EXISTENTE")
    print("="*55)

    pipeline = carregar_pipeline(score_minimo=80)
    sem_curriculo = [v for v in pipeline if not v.get("curriculo_path")]

    print(f"\n{len(pipeline)} vagas no pipeline | {len(sem_curriculo)} sem currículo gerado")

    if not sem_curriculo:
        print("Todos os currículos ja foram gerados.")
        imprimir_dashboard()
        return

    vagas_processar = sem_curriculo[:limite]
    MAX_WORKERS = min(4, len(vagas_processar))
    print(f"Gerando para as top {len(vagas_processar)} vagas ({MAX_WORKERS} em paralelo)...\n")

    from concurrent.futures import ThreadPoolExecutor, as_completed

    def _processar(vaga):
        resultado = processar_vaga(vaga)
        resultado["vaga"] = vaga
        _marcar_processada(vaga["id"], resultado)
        executar_candidatura(vaga, resultado)
        return resultado

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futuros = {ex.submit(_processar, v): v for v in vagas_processar}
        for fut in as_completed(futuros):
            vaga = futuros[fut]
            try:
                fut.result()
            except Exception as e:
                print(f"  Erro em {vaga['titulo']}: {e}")

    imprimir_dashboard()


def pipeline_so_busca() -> None:
    print("\nModo: somente busca")
    asyncio.run(executar_busca())


def pipeline_so_dashboard() -> None:
    imprimir_dashboard()


def pipeline_listar_pipeline() -> None:
    """Lista todas as vagas do pipeline com score e status."""
    pipeline = carregar_pipeline(score_minimo=60)
    if not pipeline:
        print("Nenhuma vaga no pipeline. Execute a busca primeiro.")
        return

    print(f"\n{'='*60}")
    print(f"  VAGAS NO PIPELINE ({len(pipeline)} vagas, score >= 60)")
    print(f"{'='*60}")

    principal = [v for v in pipeline if v["score"] >= 80]
    media     = [v for v in pipeline if 60 <= v["score"] < 80]

    print(f"\n  PIPELINE PRINCIPAL (score >= 80) — {len(principal)} vagas")
    for v in principal:
        pcd    = " [PCD]"   if v.get("pcd_detectado") else ""
        lang   = " [PT-BR]" if v.get("idioma_vaga") == "pt" else ""
        feito  = " [OK]"    if v.get("curriculo_path") else ""
        print(f"  [{v['score']:3}]{pcd}{lang}{feito}  {v['titulo'][:45]}  —  {v['empresa'][:25]}")

    print(f"\n  MEDIA PRIORIDADE (60-79) — {len(media)} vagas")
    for v in media[:10]:
        pcd  = " [PCD]"   if v.get("pcd_detectado") else ""
        lang = " [PT-BR]" if v.get("idioma_vaga") == "pt" else ""
        print(f"  [{v['score']:3}]{pcd}{lang}  {v['titulo'][:45]}  —  {v['empresa'][:25]}")
    if len(media) > 10:
        print(f"  ... e mais {len(media)-10} vagas.")
    print(f"{'='*60}")


def pipeline_enviar_candidaturas(dry_run: bool = True) -> None:
    """
    Envia candidaturas por e-mail via Gmail API.
    Por padrão roda em dry_run=True (simulação segura).
    Para enviar de verdade: py orchestrator.py enviar --confirmar
    """
    if not _tem_google_libs():
        print("Bibliotecas Google não instaladas.")
        print("Execute: py -m pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        return

    from agents.gmail_sender import listar_pendentes, enviar_candidatura

    pendentes = listar_pendentes()

    if not pendentes:
        print("\nNenhuma candidatura com e-mail de recrutador preenchido.")
        print("Preencha o campo 'para' em data/candidaturas.json com o e-mail real.")
        return

    modo_label = "[DRY RUN — simulação]" if dry_run else "[ENVIO REAL]"
    print(f"\n{'='*55}")
    print(f"  ENVIANDO CANDIDATURAS {modo_label}")
    print(f"{'='*55}")
    print(f"  {len(pendentes)} candidatura(s) prontas para envio\n")

    enviadas = 0
    for c in pendentes:
        empresa = c.get("empresa", "")
        vaga = c.get("vaga_titulo", "")
        email = c.get("email_gerado", {}).get("para", "")
        print(f"  {empresa} — {vaga}")
        print(f"    Para: {email}")
        sucesso = enviar_candidatura(c, dry_run=dry_run)
        if sucesso:
            enviadas += 1

    print(f"\n  {enviadas}/{len(pendentes)} candidatura(s) {'simuladas' if dry_run else 'enviadas'}.")
    if dry_run:
        print("\n  Para enviar de verdade: py orchestrator.py enviar --confirmar")


def pipeline_sincronizar_sheets(dry_run: bool = True) -> None:
    """Sincroniza dados com Google Sheets."""
    if not _tem_google_libs():
        print("Bibliotecas Google não instaladas.")
        print("Execute: py -m pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        return

    from agents.sheets_dashboard import sincronizar

    modo_label = "[DRY RUN]" if dry_run else "[SINCRONIZANDO]"
    print(f"\n{'='*55}")
    print(f"  GOOGLE SHEETS {modo_label}")
    print(f"{'='*55}\n")
    sincronizar(dry_run=dry_run)
    if dry_run:
        print("\n  Para sincronizar de verdade: py orchestrator.py sheets --confirmar")


def pipeline_setup_google() -> None:
    """Guia de configuração das APIs Google."""
    print("""
=======================================================
  CONFIGURAÇÃO GOOGLE APIs — FASE 3
=======================================================

PASSO 1: Criar projeto no Google Cloud
  1. Acesse: https://console.cloud.google.com/
  2. Crie um novo projeto: "multivagas"
  3. Ative as APIs:
     - Gmail API
     - Google Sheets API
     - Google Calendar API (opcional)

PASSO 2: Criar credenciais OAuth 2.0
  1. APIs & Services → Credentials → Create Credentials
  2. OAuth client ID → Desktop app → Nome: "multivagas"
  3. Baixe o JSON → salve em: config/google_credentials.json

PASSO 3: Criar planilha de tracking
  1. Acesse: https://sheets.google.com/
  2. Crie uma planilha em branco chamada "multivagas-tracker"
  3. Copie o ID da URL (entre /d/ e /edit)
  4. Adicione ao .env: GOOGLE_SHEET_ID=seu_id_aqui

PASSO 4: Testar autenticação
  py -c "from agents.google_auth import testar_conexao; testar_conexao()"

PASSO 5: Criar abas na planilha
  py -c "from agents.sheets_dashboard import criar_estrutura_planilha; criar_estrutura_planilha()"

PASSO 6: Primeira sincronização
  py orchestrator.py sheets --confirmar

=======================================================
""")


def pipeline_so_curriculo(vaga_id: str) -> None:
    """Processa currículo para uma vaga específica pelo ID."""
    if not VAGAS_PATH.exists():
        print("vagas.json nao encontrado. Execute a busca primeiro.")
        return
    with open(VAGAS_PATH, "r", encoding="utf-8") as f:
        vagas = json.load(f)
    vaga = next((v for v in vagas if v["id"] == vaga_id), None)
    if not vaga:
        print(f"Vaga {vaga_id} nao encontrada.")
        return
    resultado = processar_vaga(vaga)
    _marcar_processada(vaga_id, resultado)
    print(f"\nCurriculo: {resultado['curriculo_path']}")
    print(f"Cover:     {resultado['cover_path']}")


def pipeline_calendario(dry_run: bool = True) -> None:
    """Cria eventos de follow-up no Google Calendar para candidaturas pendentes."""
    if not _tem_google_libs():
        print("Bibliotecas Google não instaladas.")
        print("Execute: py -m pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        return
    from agents.calendar_followup import criar_eventos_pendentes, imprimir_followups_hoje
    imprimir_followups_hoje()
    criados = criar_eventos_pendentes(dry_run=dry_run)
    if dry_run and criados:
        print("\n  Para criar de verdade: py orchestrator.py calendario --confirmar")


def pipeline_enriquecer(dry_run: bool = True) -> None:
    """Tenta preencher e-mails de recrutadores ausentes em candidaturas.json."""
    from agents.recruiter_finder import enriquecer_candidaturas
    print("\n" + "="*55)
    print("  ENRIQUECIMENTO — BUSCA DE E-MAILS")
    print("="*55)
    enriquecer_candidaturas(dry_run=dry_run)


def pipeline_digest(dry_run: bool = True) -> None:
    """Envia digest diário com vagas novas e follow-ups."""
    from agents.notificador import enviar_digest
    print("\n" + "="*55)
    print("  DIGEST DIÁRIO")
    print("="*55)
    enviar_digest(dry_run=dry_run)


def pipeline_analytics(salvar: bool = False) -> None:
    """Exibe relatório de performance das candidaturas."""
    from agents.analytics import imprimir_relatorio, salvar_snapshot
    imprimir_relatorio()
    if salvar:
        salvar_snapshot()


if __name__ == "__main__":
    import sys

    modo = sys.argv[1] if len(sys.argv) > 1 else "gerar"

    if modo == "busca":
        pipeline_so_busca()
    elif modo == "gerar":
        pipeline_processar_pipeline(limite=5)
    elif modo == "completo":
        asyncio.run(pipeline_completo())
    elif modo == "dashboard":
        pipeline_so_dashboard()
    elif modo == "listar":
        pipeline_listar_pipeline()
    elif modo == "curriculo" and len(sys.argv) > 2:
        pipeline_so_curriculo(sys.argv[2])
    elif modo == "enviar":
        pipeline_enviar_candidaturas(dry_run="--confirmar" not in sys.argv)
    elif modo == "sheets":
        pipeline_sincronizar_sheets(dry_run="--confirmar" not in sys.argv)
    elif modo == "setup-google":
        pipeline_setup_google()
    # ── Fase 3 (complemento) ──────────────────────────────
    elif modo == "calendario":
        pipeline_calendario(dry_run="--confirmar" not in sys.argv)
    # ── Fase 4 ────────────────────────────────────────────
    elif modo == "enriquecer":
        pipeline_enriquecer(dry_run="--confirmar" not in sys.argv)
    elif modo == "digest":
        pipeline_digest(dry_run="--confirmar" not in sys.argv)
    elif modo == "analytics":
        pipeline_analytics(salvar="--salvar" in sys.argv)
    else:
        print("Modos disponíveis:")
        print("  busca | gerar | completo | dashboard | listar | curriculo <id>")
        print("  enviar [--confirmar] | sheets [--confirmar] | setup-google")
        print("  calendario [--confirmar]   — follow-ups no Google Calendar (Fase 3)")
        print("  enriquecer [--confirmar]   — busca e-mails de recrutadores (Fase 4)")
        print("  digest [--confirmar]       — envia digest diário por e-mail (Fase 4)")
        print("  analytics [--salvar]       — relatório de performance (Fase 4)")
