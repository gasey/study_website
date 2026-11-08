"""Phase A/B CLI: five local drafts maximum, explicit hosted inference gates."""
import argparse
from dataclasses import replace
import json
import os
from pathlib import Path
import re
import shlex
import signal
import sqlite3
import subprocess
import sys
import time
import uuid

from .adapters.base import Question
from .adapters.project import RecoveryBank
from .auth.siwc import Credentials, login
from .config import Config
from .errors import SolverError
from .inference.openai import OpenAIPlan
from .jobs import Ledger, status
from .progress import export_review, write_export
from .prompts import VERSION
from .storage import atomic_json, digest, locked, read_private
from .validate import strict_json, validate
from .worker import run


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, default=Path.home() / ".config/mcq-solver/config.toml")
    p.add_argument("--credentials-dir", type=Path, default=Path.home() / ".config/mcq-solver/credentials")
    p.add_argument("--state-dir", type=Path, default=Path.home() / ".local/share/mcq-solver")
    p.add_argument("--bank", type=Path, help="Explicit read-only mpsc_bank_v2.json snapshot")
    p.add_argument("--model", help="Explicit selection; requires catalog check and fresh probe")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    sub.add_parser("init-host")
    l = sub.add_parser("login")
    l.add_argument("--approve-plan-sharing", action="store_true")
    l.add_argument("--reconsent", action="store_true")
    sub.add_parser("models")
    sub.add_parser("test-inference")
    for name in ("sync", "run", "export-packet", "import-results"):
        s = sub.add_parser(name)
        s.add_argument("--limit", type=int, default=5)
        s.add_argument("--dry-run", action="store_true")
        s.add_argument("--no-write", action="store_true", help="Read-only preview; makes no inference requests")
        if name == "export-packet":
            s.add_argument("--out", type=Path, required=True)
        if name == "import-results":
            s.add_argument("--file", type=Path, required=True)
    sub.add_parser("status")
    sub.add_parser("resume")
    sub.add_parser("stop")
    s = sub.add_parser("export-review")
    s.add_argument("--out", type=Path, required=True)
    s = sub.add_parser("export-credentials")
    s.add_argument("--ssh-host", required=True)
    s.add_argument("--remote-python", required=True, help="Absolute path to installed worker venv Python")
    s.add_argument("--remote-credentials-dir", required=True)
    sub.add_parser("import-credentials", help=argparse.SUPPRESS)
    return p


def bank_for(args):
    if args.bank is None:
        raise SolverError("missing_bank")
    holds_path = args.state_dir / 'source-holds.json'
    held = []
    if holds_path.exists():
        holds = read_private(holds_path)
        if not isinstance(holds, dict) or holds.get('version') != 1 or not isinstance(holds.get('question_ids'), list):
            raise SolverError('invalid_question')
        held = holds['question_ids']
        if any(not isinstance(qid, str) or not qid or len(qid) > 200 for qid in held):
            raise SolverError('invalid_question')
    return RecoveryBank(args.bank, held_ids=held)


def preflight_key(store, config):
    d = store.read()
    return digest([d.get("subject"), d.get("client_id"), config.model, config.reasoning])


def transfer(args, store):
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.@-]*", args.ssh_host):
        raise SolverError("invalid_request")
    for path in (args.remote_python, args.remote_credentials_dir):
        if not path.startswith("/") or "\n" in path:
            raise SolverError("invalid_request")
    command = shlex.join([args.remote_python, "-m", "mcq_solver", "--credentials-dir", args.remote_credentials_dir, "import-credentials"])
    with locked(store.root / "auth.lock", blocking=False):
        d = store.read()
        if d.get("transferred"):
            raise SolverError("session_transferred")
        if not d.get("access_token"):
            raise SolverError("auth_required")
        # Suspend the laptop before transferring a rotating refresh session.
        # If SSH is ambiguous, keep it suspended; do not replay or refresh here.
        store.write({**d, "transferred": True})
        try:
            result = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
                                     "-o", "ConnectTimeout=10", args.ssh_host, command],
                                    input=json.dumps(d), text=True, capture_output=True, timeout=30)
            if result.returncode or json.loads(result.stdout) != {"imported": True}:
                raise SolverError("transfer_uncertain")
        except (subprocess.SubprocessError, OSError, ValueError):
            raise SolverError("transfer_uncertain") from None
        store.write({k: v for k, v in {**d, "transferred": True}.items() if k not in {"access_token", "refresh_token", "id_token"}})
    return {"transferred": True, "local_session_suspended": True}


def execute(args):
    for name in ("config", "credentials_dir", "state_dir", "bank"):
        value = getattr(args, name, None)
        if value is not None:
            # Make SQLite read-only URIs and paths independent of the next cwd.
            setattr(args, name, value.expanduser().absolute())
    config = Config.read(args.config)
    if args.model:
        config = replace(config, model=args.model)
    store = Credentials(args.credentials_dir)
    command = args.command
    if command == "doctor":
        eligibility = config.eligibility
        result = {"python": sys.version.split()[0], "billing_mode": config.billing_mode,
                  "api_key_adapter": "disabled", "eligibility": eligibility, "auth": store.status(),
                  "credits_disabled_confirmed": config.credits_disabled_confirmed,
                  "production_draft_writer": "not_configured", "published_writes": "unavailable"}
        if args.bank:
            bank = bank_for(args)
            result["bank"] = {"questions": len(bank.rows), "source": "read_only_recovery_snapshot", "pilot_candidates": len(bank.pending(5))}
        return result
    if command == "init-host":
        return {"ext_agent_host_id": store.host()}
    if command == "login":
        return login(store, config, approved=args.approve_plan_sharing, reconsent=args.reconsent)
    if command == "export-credentials":
        return transfer(args, store)
    if command == "import-credentials":
        if sys.stdin.isatty():
            raise SolverError("invalid_request")
        raw = sys.stdin.read(65537)
        if len(raw) > 65536:
            raise SolverError("invalid_credentials")
        store.import_transfer(json.loads(raw))
        return {"imported": True}
    if command == "status":
        return status(args.state_dir)
    if command == "export-review":
        return export_review(args.state_dir, args.out)
    if command == "stop":
        atomic_json(args.state_dir / "stop.json", {"requested": True})
        return {"stop_requested": True}
    if command == "models":
        models = OpenAIPlan(config, store).models()
        return {"models": [{"slug": m.get("slug"), "display_name": m.get("display_name")} for m in models if isinstance(m, dict) and m.get("visibility") == "list"]}
    if command == "test-inference":
        with locked(args.state_dir / "worker.lock", blocking=False):
            if status(args.state_dir)["pause_reason"]:
                raise SolverError("queue_paused")
            try:
                OpenAIPlan(config, store).probe()
            except SolverError as exc:
                if exc.pauses:
                    ledger = Ledger(args.state_dir)
                    ledger.pause(exc.code)
                    ledger.close()
                raise
            atomic_json(args.state_dir / "preflight.json", {"key": preflight_key(store, config), "at": time.time()})
        return {"completed": True, "model": config.model, "reasoning": config.reasoning}
    if command == "resume":
        with locked(args.state_dir / "worker.lock", blocking=False):
            ledger = Ledger(args.state_dir)
            try:
                ledger.resume()
                (args.state_dir / "stop.json").unlink(missing_ok=True)
            finally:
                ledger.close()
        return {"resumed": True, "note": "Run test-inference again after reauthorization; no requests made by resume."}
    if not 1 <= args.limit <= 5:
        raise SolverError("limit_exceeds_phase")
    bank = bank_for(args)
    candidates = bank.pending(args.limit)
    if args.dry_run or args.no_write:
        return {"dry_run": True, "candidates": [{"question_id": q.id, "question_version_hash": q.fingerprint} for q in candidates],
                "queue": status(args.state_dir), "model_requests": 0, "writes": 0}
    if command == "export-packet":
        packet = {"format": "mcq-solver-blind-v1", "prompt_version": VERSION,
                  "model_id": config.model, "reasoning": config.reasoning,
                  "items": [{"question_id": q.id, "question_version_hash": q.fingerprint, "input": q.blind_input()} for q in candidates]}
        write_export(args.out, json.dumps(packet, ensure_ascii=False, indent=2) + "\n")
        return {"exported": len(candidates), "published_writes": 0}
    with locked(args.state_dir / "worker.lock", blocking=False):
        ledger = Ledger(args.state_dir)
        try:
            if command == "sync":
                keys = [ledger.enqueue(q, config.model, config.reasoning) for q in candidates]
                return {"queued_ids": keys, "candidates": len(keys), "published_writes": 0}
            if command == "import-results":
                results = strict_json(args.file.read_text())
                if not isinstance(results, list) or not 1 <= len(results) <= args.limit:
                    raise SolverError("invalid_packet")
                checked = []
                seen = set()
                for item in results:
                    if not isinstance(item, dict) or set(item) != {"question_id", "question_version_hash", "response"}:
                        raise SolverError("invalid_packet")
                    if item["question_id"] in seen:
                        raise SolverError("duplicate_id")
                    seen.add(item["question_id"])
                    q = bank.current(item["question_id"])
                    if q is None or q.fingerprint != item["question_version_hash"]:
                        raise SolverError("stale_source")
                    draft = validate(json.dumps(item["response"]), q)
                    draft["review_reasons"].append("offline_import_unverified_model")
                    checked.append((q, draft))
                saved = 0
                for q, draft in checked:
                    key = ledger.enqueue(q, "offline-import", "not_verified")
                    job = ledger.claim(str(uuid.uuid4()), "offline-import", "not_verified", job_id=key)
                    if job:
                        current = bank.current(q.id)
                        if current is None or current.fingerprint != q.fingerprint:
                            ledger.finish(job, "permanent_failed", code="stale_source")
                            raise SolverError("stale_source")
                        ledger.save_draft(job, draft)
                        saved += 1
                return {"valid_drafts": saved, "flagged": saved, "model_requests": 0, "published_writes": 0}
            if command == "run":
                if ledger.pause_reason():
                    raise SolverError("queue_paused")
                if (args.state_dir / "stop.json").exists():
                    return {"stopped": True, "valid_drafts": 0}
                config.require_inference()
                try:
                    preflight = read_private(args.state_dir / "preflight.json")
                except FileNotFoundError:
                    raise SolverError("preflight_required") from None
                if preflight.get("key") != preflight_key(store, config) or time.time() - preflight.get("at", 0) > 86400:
                    raise SolverError("preflight_required")
                inference = OpenAIPlan(config, store)
                try:
                    inference.check_model()
                except SolverError as exc:
                    if exc.pauses:
                        ledger.pause(exc.code)
                    raise
                stopping = [False]
                old = {sig: signal.getsignal(sig) for sig in (signal.SIGTERM, signal.SIGINT)}
                for sig in old:
                    signal.signal(sig, lambda *_: stopping.__setitem__(0, True))
                try:
                    return run(ledger, bank, inference, config, args.limit,
                               lambda: stopping[0] or (args.state_dir / "stop.json").exists())
                finally:
                    for sig, handler in old.items():
                        signal.signal(sig, handler)
        finally:
            ledger.close()
    raise SolverError("invalid_request")


def main(argv=None):
    os.umask(0o077)
    args = parser().parse_args(argv)
    try:
        result = execute(args)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except SolverError as exc:
        print(json.dumps({"error": exc.code, "http_status": exc.status, "published_writes": 0}), file=sys.stderr)
        return 2
    except (Exception, KeyboardInterrupt):
        # Never print raw provider bodies, traceback locals, tokens or bank text.
        print(json.dumps({"error": "internal_error", "published_writes": 0}), file=sys.stderr)
        return 2
