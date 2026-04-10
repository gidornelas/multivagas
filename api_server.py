"""
API Server local — Multi-Vagas Dashboard
Expõe endpoints para o dashboard.html disparar o orchestrator.py sem terminal.

Uso:
    py api_server.py

Endpoints:
    POST /api/busca                      — inicia busca em background
    GET  /api/status                     — estado da busca
    GET  /api/vagas                      — data/vagas.json (+ Supabase)
    GET  /api/candidaturas               — data/candidaturas.json (+ Supabase)
    GET  /api/curriculo                  — data/curriculo.json (+ Supabase)
    POST /api/curriculo                  — salva curriculo.json + Supabase
    GET  /api/config                     — config atual (Supabase)
    POST /api/config                     — salva config no Supabase
    GET  /api/vaga-status                — {vaga_key: status} do Supabase
    POST /api/vaga-status                — {"vaga_key":"...", "status":"..."} → Supabase
    GET  /api/output/pdf?f=arquivo       — serve HTML de currículo de output/pdfs/
    GET  /api/output/cover?f=arq        — serve cover letter de output/covers/
    POST /api/gerar-curriculo            — {"vaga_id":"..."} gera currículo para vaga
    GET  /api/gerar-curriculo/status?vaga_id=... — estado da geração
    POST /api/candidatura                — registra / atualiza candidatura
"""

import json
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Import Supabase (opcional — funciona sem ele)
try:
    from db.client import (
        get_vagas, upsert_vagas,
        get_candidaturas, upsert_candidatura,
        get_curriculo, save_curriculo,
        get_config, save_config,
        upsert_vaga_status, get_all_vaga_status,
        marcar_curriculo_gerado,
    )
    _SB_DISPONIVEL = True
except ImportError:
    _SB_DISPONIVEL = False
    print("[API] supabase não instalado — usando apenas JSON local.")

BASE              = Path(__file__).parent
VAGAS_PATH        = BASE / "data" / "vagas.json"
CANDIDATURAS_PATH = BASE / "data" / "candidaturas.json"
CURRICULO_PATH    = BASE / "data" / "curriculo.json"
PDFS_DIR          = BASE / "output" / "pdfs"
COVERS_DIR        = BASE / "output" / "covers"
PORT              = 5001

# ── Estado da busca ────────────────────────────────────
_busca_state: dict = {"running": False, "started_at": None, "finished_at": None, "error": None}
_busca_lock = threading.Lock()

# ── Estado por geração de currículo ───────────────────
_gerar_states: dict = {}
_gerar_lock   = threading.Lock()


# ── Workers ───────────────────────────────────────────

def _run_busca() -> None:
    cmd = [sys.executable, str(BASE / "orchestrator.py"), "busca"]
    with _busca_lock:
        _busca_state.update(running=True, started_at=time.time(), finished_at=None, error=None)
    try:
        proc = subprocess.run(cmd, cwd=str(BASE), capture_output=False, text=True)
        err = None if proc.returncode == 0 else f"Exit code {proc.returncode}"
    except Exception as exc:
        err = str(exc)
    with _busca_lock:
        _busca_state.update(running=False, finished_at=time.time(), error=err)
    # Após busca concluída, sincroniza vagas locais com Supabase
    if not err and _SB_DISPONIVEL:
        _sincronizar_vagas_para_supabase()


def _sincronizar_vagas_para_supabase() -> None:
    if not VAGAS_PATH.exists():
        return
    try:
        with open(VAGAS_PATH, "r", encoding="utf-8") as f:
            vagas = json.load(f)
        if vagas:
            ok = upsert_vagas(vagas)
            if ok:
                print(f"[API] {len(vagas)} vagas sincronizadas com Supabase.")
    except Exception as e:
        print(f"[API] Erro ao sincronizar vagas com Supabase: {e}")


def _run_gerar_curriculo(vaga_id: str) -> None:
    cmd = [sys.executable, str(BASE / "orchestrator.py"), "curriculo", vaga_id]
    with _gerar_lock:
        _gerar_states[vaga_id] = {
            "running": True, "started_at": time.time(),
            "finished_at": None, "error": None, "curriculo_path": None,
        }
    err = None
    try:
        proc = subprocess.run(cmd, cwd=str(BASE), capture_output=False, text=True)
        err = None if proc.returncode == 0 else f"Exit code {proc.returncode}"
    except Exception as exc:
        err = str(exc)

    curriculo_path = None
    cover_path     = None
    cover_text     = ""
    try:
        if VAGAS_PATH.exists():
            with open(VAGAS_PATH, "r", encoding="utf-8") as f:
                vagas = json.load(f)
            vaga = next((v for v in vagas if v["id"] == vaga_id), None)
            if vaga:
                curriculo_path = vaga.get("curriculo_path")
                cover_path     = vaga.get("cover_path")
    except Exception:
        pass

    # Lê texto da cover letter gerada
    if cover_path:
        try:
            from pathlib import Path as _Path
            cp = _Path(cover_path)
            if not cp.is_absolute():
                cp = ROOT / cp
            if cp.exists():
                cover_text = cp.read_text(encoding="utf-8")
        except Exception:
            pass

    # Sincroniza com Supabase
    if not err and curriculo_path and _SB_DISPONIVEL:
        marcar_curriculo_gerado(vaga_id, curriculo_path or "", cover_path or "", cover_text)

    with _gerar_lock:
        _gerar_states[vaga_id].update(
            running=False, finished_at=time.time(),
            error=err, curriculo_path=curriculo_path,
        )


# ── Handler ───────────────────────────────────────────

class _Handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    # ── GET ──────────────────────────────────────────

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path
        params = parse_qs(parsed.query)

        if path == "/api/status":
            with _busca_lock:
                self._json(dict(_busca_state))

        elif path == "/api/vagas":
            # Tenta Supabase; fallback JSON local
            if _SB_DISPONIVEL:
                dados = get_vagas()
                if dados:
                    self._json(dados); return
            self._serve_json_file(VAGAS_PATH)

        elif path == "/api/candidaturas":
            if _SB_DISPONIVEL:
                dados = get_candidaturas()
                if dados:
                    self._json(dados); return
            self._serve_json_file(CANDIDATURAS_PATH)

        elif path == "/api/curriculo":
            if _SB_DISPONIVEL:
                dados = get_curriculo()
                if dados:
                    self._json(dados); return
            self._serve_json_file(CURRICULO_PATH)

        elif path == "/api/config":
            if _SB_DISPONIVEL:
                dados = get_config()
                if dados:
                    self._json(dados); return
            self._json({"error": "config não encontrada"}, 404)

        elif path == "/api/vaga-status":
            if _SB_DISPONIVEL:
                self._json(get_all_vaga_status())
            else:
                self._json({})

        elif path == "/api/output/pdf":
            fname = params.get("f", [""])[0]
            self._serve_output_file(PDFS_DIR, fname, "text/html; charset=utf-8")

        elif path == "/api/output/cover":
            fname = params.get("f", [""])[0]
            self._serve_output_file(COVERS_DIR, fname, "text/plain; charset=utf-8")

        elif path == "/api/gerar-curriculo/status":
            vaga_id = params.get("vaga_id", [""])[0]
            with _gerar_lock:
                state = dict(_gerar_states.get(vaga_id, {"running": False}))
            self._json(state)

        else:
            self._json({"error": "not found"}, 404)

    # ── POST ─────────────────────────────────────────

    def do_POST(self):
        body_bytes = b""
        cl = self.headers.get("Content-Length")
        if cl:
            body_bytes = self.rfile.read(int(cl))

        parsed = urlparse(self.path)
        path   = parsed.path

        if path == "/api/busca":
            with _busca_lock:
                if _busca_state["running"]:
                    self._json({"ok": False, "msg": "Busca já em andamento"}); return
            threading.Thread(target=_run_busca, daemon=True).start()
            self._json({"ok": True, "msg": "Busca iniciada"})

        elif path == "/api/curriculo":
            try:
                dados = json.loads(body_bytes or b"{}")
            except Exception:
                self._json({"ok": False, "msg": "JSON inválido"}, 400); return
            if not dados:
                self._json({"ok": False, "msg": "Body vazio"}, 400); return
            # Salva local
            try:
                CURRICULO_PATH.parent.mkdir(parents=True, exist_ok=True)
                with open(CURRICULO_PATH, "w", encoding="utf-8") as f:
                    json.dump(dados, f, ensure_ascii=False, indent=2)
            except Exception as exc:
                self._json({"ok": False, "msg": f"Erro ao salvar local: {exc}"}); return
            # Salva Supabase
            sb_ok = save_curriculo(dados) if _SB_DISPONIVEL else False
            self._json({"ok": True, "supabase": sb_ok})

        elif path == "/api/config":
            try:
                dados = json.loads(body_bytes or b"{}")
            except Exception:
                self._json({"ok": False, "msg": "JSON inválido"}, 400); return
            sb_ok = save_config(dados) if _SB_DISPONIVEL else False
            self._json({"ok": True, "supabase": sb_ok})

        elif path == "/api/vaga-status":
            try:
                dados = json.loads(body_bytes or b"{}")
            except Exception:
                self._json({"ok": False, "msg": "JSON inválido"}, 400); return
            vaga_key = dados.get("vaga_key", "").strip()
            status   = dados.get("status", "nova").strip()
            if not vaga_key:
                self._json({"ok": False, "msg": "vaga_key obrigatório"}, 400); return
            sb_ok = upsert_vaga_status(vaga_key, status) if _SB_DISPONIVEL else False
            self._json({"ok": True, "supabase": sb_ok})

        elif path == "/api/gerar-curriculo":
            try:
                data = json.loads(body_bytes or b"{}")
            except Exception:
                self._json({"ok": False, "msg": "JSON inválido"}, 400); return
            vaga_id = data.get("vaga_id", "").strip()
            if not vaga_id:
                self._json({"ok": False, "msg": "vaga_id obrigatório"}, 400); return
            with _gerar_lock:
                if _gerar_states.get(vaga_id, {}).get("running"):
                    self._json({"ok": False, "msg": "Já gerando para esta vaga"}); return
            threading.Thread(target=_run_gerar_curriculo, args=(vaga_id,), daemon=True).start()
            self._json({"ok": True, "msg": f"Gerando currículo para {vaga_id}"})

        elif path == "/api/candidatura":
            try:
                nova = json.loads(body_bytes or b"{}")
            except Exception:
                self._json({"ok": False, "msg": "JSON inválido"}, 400); return
            # Salva local
            try:
                lista: list = []
                if CANDIDATURAS_PATH.exists():
                    with open(CANDIDATURAS_PATH, "r", encoding="utf-8") as f:
                        lista = json.load(f)
                idx = next((i for i, c in enumerate(lista)
                            if c.get("vaga_id") == nova.get("vaga_id")), None)
                if idx is not None:
                    lista[idx].update(nova)
                else:
                    lista.append(nova)
                CANDIDATURAS_PATH.parent.mkdir(parents=True, exist_ok=True)
                with open(CANDIDATURAS_PATH, "w", encoding="utf-8") as f:
                    json.dump(lista, f, ensure_ascii=False, indent=2)
            except Exception as exc:
                self._json({"ok": False, "msg": str(exc)}, 500); return
            # Salva Supabase
            sb_ok = upsert_candidatura(nova) if _SB_DISPONIVEL else False
            self._json({"ok": True, "supabase": sb_ok})

        else:
            self._json({"error": "not found"}, 404)

    # ── Helpers ──────────────────────────────────────

    def _serve_json_file(self, fpath: Path) -> None:
        if fpath.exists():
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            body = content.encode("utf-8")
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self._json({"error": f"{fpath.name} não encontrado"}, 404)

    def _serve_output_file(self, directory: Path, filename: str, content_type: str) -> None:
        if not filename:
            self._json({"error": "parâmetro f obrigatório"}, 400); return
        safe_name = Path(filename).name
        fpath = directory / safe_name
        if not fpath.exists():
            self._json({"error": "arquivo não encontrado"}, 404); return
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        body = content.encode("utf-8")
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, data: dict | list, code: int = 200):
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):  # noqa: N802
        print(f"[API] {self.address_string()} {fmt % args}")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("localhost", PORT), _Handler)
    sb_status = "conectado" if _SB_DISPONIVEL else "não configurado (usando JSON local)"
    print(f"API server rodando em http://localhost:{PORT}")
    print(f"Supabase: {sb_status}")
    print("  POST /api/busca                     — inicia a busca")
    print("  GET  /api/status                    — estado da busca")
    print("  GET  /api/vagas                     — vagas (Supabase ou JSON)")
    print("  GET  /api/candidaturas              — candidaturas (Supabase ou JSON)")
    print("  GET  /api/curriculo                 — currículo (Supabase ou JSON)")
    print("  POST /api/curriculo                 — salva currículo")
    print("  GET  /api/config                    — config de busca")
    print("  POST /api/config                    — salva config de busca")
    print("  GET  /api/vaga-status               — status das vagas")
    print("  POST /api/vaga-status               — atualiza status de vaga")
    print("  GET  /api/output/pdf?f=arquivo      — serve HTML de currículo")
    print("  GET  /api/output/cover?f=arq        — serve cover letter")
    print("  POST /api/gerar-curriculo           — gera currículo para vaga")
    print("  POST /api/candidatura               — registra/atualiza candidatura")
    print("\nPressione Ctrl+C para parar.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
