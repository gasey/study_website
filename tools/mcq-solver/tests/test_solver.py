import base64
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import replace
import io
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from urllib.parse import parse_qs, urlencode, urlsplit
from unittest.mock import patch

from mcq_solver.adapters.project import RecoveryBank
from mcq_solver.auth.siwc import Attempt, Credentials, DIRECT_SCOPE, IdentityVerifier, login
from mcq_solver.cli import execute, main, parser
from mcq_solver.config import Config
from mcq_solver.errors import SolverError
from mcq_solver.inference.openai import completed_text, OpenAIPlan
from mcq_solver.jobs import Ledger, status
from mcq_solver.progress import export_review
from mcq_solver.prompts import request
from mcq_solver.storage import atomic_json, digest, locked, read_private
from mcq_solver.transport import DISCOVERY, ISSUER, JWKS, RESOURCE, TOKEN, provider_error
from mcq_solver.validate import validate
from mcq_solver.worker import run


def bank_data(count=5):
    return {"schemaVersion": "2.0", "papers": [{"id": "paper", "year": 2020}],
            "questions": [{"id": f"q{i}", "paperId": "paper", "type": "mcq", "qnum": i + 1,
                           "question": f"What is {i} plus 2?", "options": [str(i+2), str(i+3), str(i+4)],
                           "answerIndex": -1, "answerSource": "none", "explanation": "", "page": 1}
                          for i in range(count)], "figureGroups": {}, "passageGroups": {}}


def response(qid="q0", **overrides):
    return {"question_id": qid, "selected_option_id": "0", "explanation": "Adding two to the stated integer gives the value printed in the first option.",
            "certainty": "confident", "review_required": False, "review_reasons": [], "topic": "Arithmetic", **overrides}


def event(kind="response.completed", text=None, **overrides):
    payload = {"type": kind, "response": {"status": "completed", "model": "gpt-6.1-sol",
               "output": [{"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": text or json.dumps(response())}]}]}}
    payload.update(overrides)
    return payload


def sse(*items):
    return io.BytesIO(b"".join(("data: " + json.dumps(e) + "\n\n").encode() for e in items))


class FakeTransport:
    def __init__(self, outputs=()):
        self.outputs = list(outputs)
        self.calls = []

    def json(self, url, **kw):
        self.calls.append((url, kw))
        value = self.outputs.pop(0)
        if isinstance(value, Exception):
            raise value
        return value

    @contextmanager
    def open(self, url, **kw):
        yield self.json(url, **kw)


class FakeIdentity:
    def verify(self, token, client, nonce=None):
        return {"sub": "subject", "iss": ISSUER}


class FakeInference:
    def __init__(self, action=None):
        self.calls = []
        self.action = action

    def respond(self, body):
        self.calls.append(body)
        if self.action:
            return self.action(body)
        q = json.loads(body["input"][0]["content"])
        return json.dumps(response(q["question_id"]))


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.bank_path = self.root / "bank.json"
        self.bank_path.write_text(json.dumps(bank_data()))
        self.bank = RecoveryBank(self.bank_path)
        self.state = self.root / "state"
        self.ledger = Ledger(self.state)
        self.config = Config()

    def tearDown(self):
        self.ledger.close()
        self.tmp.cleanup()

    def enqueue(self, n=5):
        return [self.ledger.enqueue(q, self.config.model, self.config.reasoning) for q in self.bank.pending(n)]

    def assertCode(self, code, fn, *args, **kw):
        with self.assertRaises(SolverError) as cm:
            fn(*args, **kw)
        self.assertEqual(cm.exception.code, code)


class ValidationTests(Base):
    def test_invalid_response_cases(self):
        q = self.bank.pending(1)[0]
        cases = [(response(selected_option_id="Z"), "invalid_option"),
                 (response(selected_option_id=0), "invalid_option"),
                 (response(question_id="attacker-id"), "invalid_question_id"),
                 (response(explanation=""), "invalid_explanation"),
                 (response(selected_option_id=None), "invalid_option"),
                 (response(review_required="yes"), "invalid_response"),
                 (response(certainty="99%"), "invalid_response"),
                 (response(certainty="cannot_determine"), "invalid_option"),
                 (response(extra="field"), "invalid_response")]
        for value, code in cases:
            with self.subTest(value=value):
                self.assertCode(code, validate, json.dumps(value), q)
        for text in ("not json", "```json\n{}\n```", '{"a":1,"a":2}', '{"a":NaN}'):
            self.assertCode("invalid_json", validate, text, q)

    def test_null_is_flagged(self):
        draft = validate(json.dumps(response(selected_option_id=None, certainty="cannot_determine", review_reasons=["Missing diagram"])), self.bank.pending(1)[0])
        self.assertTrue(draft["review_required"])
        self.assertIsNone(draft["human_approval"])

    def test_key_comparison_blind_prompt_and_unchanged_source(self):
        data = bank_data(1)
        data["questions"][0].update(answerSource="official", answerIndex=1, key_disputed=True, explanation="SECRET_EXISTING_EXPLANATION", answerKeyRef="SECRET_KEY_REF")
        self.bank_path.write_text(json.dumps(data))
        q = self.bank.current("q0")
        original = self.bank_path.read_bytes()
        body = request(q, self.config.model, self.config.reasoning)
        self.assertNotIn("SECRET_", json.dumps(body))
        self.assertNotIn("answerIndex", json.dumps(body))
        draft = validate(json.dumps(response()), q)
        self.assertFalse(draft["official_key_agreement"])
        self.assertIn("official_key_disagreement", draft["review_reasons"])
        self.assertEqual(original, self.bank_path.read_bytes())

    def test_media_and_duplicate_options_flagged(self):
        q = self.bank.pending(1)[0]
        q.record.update(hasDiagram=True, options=["A", "A"], passageId="missing")
        draft = validate(json.dumps(response()), q)
        self.assertTrue({"media_not_supplied", "duplicate_options", "passage_not_supplied"} <= set(draft["review_reasons"]))

    def test_credentials_in_model_output_rejected(self):
        self.assertCode("invalid_json", validate, json.dumps(response(explanation="Bearer FAKE_TEST_ONLY_CREDENTIAL must never be exported.")), self.bank.pending(1)[0])

    def test_zero_based_and_unknown_sentinel(self):
        data = bank_data(3)
        data["questions"][0]["answerIndex"] = 0
        data["questions"][1]["answerIndex"] = None
        self.bank_path.write_text(json.dumps(data))
        bank = RecoveryBank(self.bank_path)
        self.assertEqual([q.id for q in bank.pending(5)], ["q1", "q2"])

    def test_full_fingerprint_includes_media_and_key(self):
        q = self.bank.pending(1)[0]
        initial = q.fingerprint
        q.media["figure"] = {"sha256": "changed"}
        self.assertNotEqual(initial, q.fingerprint)
        initial = q.fingerprint
        q.record["answerIndex"] = 1
        self.assertNotEqual(initial, q.fingerprint)

    def test_duplicate_source_ids_rejected(self):
        data = bank_data(2)
        data["questions"][1]["id"] = "q0"
        self.bank_path.write_text(json.dumps(data))
        self.assertCode("duplicate_id", RecoveryBank, self.bank_path)

    def test_reviewed_format_holds_excluded_and_cannot_be_inferred(self):
        original = self.bank_path.read_bytes()
        held = RecoveryBank(self.bank_path, held_ids=['q0', 'q1'])
        self.assertEqual([q.id for q in held.pending(5)], ['q2', 'q3', 'q4'])
        self.assertIsNone(held.current('q0'))
        self.enqueue(1)
        inference = FakeInference()
        run(self.ledger, held, inference, self.config, 1)
        self.assertEqual(inference.calls, [])
        self.assertEqual(status(self.state)['drafts'], 0)
        self.assertEqual(original, self.bank_path.read_bytes())


class StreamTests(unittest.TestCase):
    def test_finalized_items_with_empty_terminal_output(self):
        message = event()["response"]["output"][0]
        done = {"type": "response.output_item.done", "output_index": 0, "item": message}
        terminal = event()
        terminal["response"]["output"] = []
        self.assertEqual(completed_text(sse(done, terminal), "gpt-6.1-sol"), json.dumps(response()))
        with self.assertRaisesRegex(SolverError, "stream_truncated"):
            completed_text(sse(done), "gpt-6.1-sol")
        with self.assertRaisesRegex(SolverError, "response_incomplete"):
            completed_text(sse(done, event("response.incomplete")), "gpt-6.1-sol")

    def test_conflicting_or_partial_finalized_items_rejected(self):
        message = event()["response"]["output"][0]
        done = {"type": "response.output_item.done", "output_index": 0, "item": message}
        changed = {**done, "item": {**message, "status": "in_progress"}}
        with self.assertRaisesRegex(SolverError, "invalid_response"):
            completed_text(sse(changed, event()), "gpt-6.1-sol")
        changed["item"] = {**message, "id": "changed"}
        with self.assertRaisesRegex(SolverError, "invalid_response"):
            completed_text(sse(done, changed, event()), "gpt-6.1-sol")

    def test_completed_required_and_deltas_ignored(self):
        delta = {"type": "response.output_text.delta", "delta": "untrusted partial"}
        self.assertEqual(completed_text(sse(delta, event()), "gpt-6.1-sol"), json.dumps(response()))
        with self.assertRaisesRegex(SolverError, "stream_truncated"):
            completed_text(sse(delta), "gpt-6.1-sol")

    def test_failure_and_incomplete_are_never_solved(self):
        for e, expected in [(event("response.failed", response={"error": {"code": "subscription_sharing_usage_limit_exceeded", "message": "SECRET"}}), "subscription_sharing_usage_limit_exceeded"),
                            (event("response.incomplete"), "response_incomplete"),
                            ({"type": "error", "code": "subscription_sharing_usage_unavailable"}, "subscription_sharing_usage_unavailable")]:
            with self.subTest(expected=expected), self.assertRaisesRegex(SolverError, expected):
                completed_text(sse(e), "gpt-6.1-sol")

    def test_wrong_model_and_bad_terminal_rejected(self):
        e = event()
        e["response"]["model"] = "another-model"
        with self.assertRaisesRegex(SolverError, "model_unavailable"):
            completed_text(sse(e), "gpt-6.1-sol")
        e["response"]["status"] = "in_progress"
        with self.assertRaisesRegex(SolverError, "invalid_response"):
            completed_text(sse(e), "gpt-6.1-sol")

    def test_done_and_unframed_completion_are_truncated(self):
        for raw in (b"data: [DONE]\n\n", b"data: " + json.dumps(event()).encode()):
            with self.assertRaisesRegex(SolverError, "stream_truncated"):
                completed_text(io.BytesIO(raw), "gpt-6.1-sol")


class QueueTests(Base):
    def test_five_question_end_to_end_and_no_overwrite(self):
        original = self.bank_path.read_bytes()
        self.enqueue()
        inference = FakeInference()
        result = run(self.ledger, self.bank, inference, self.config)
        self.assertEqual(result["valid_drafts"], 5)
        self.assertEqual(result["flagged"], 5)
        self.assertEqual(original, self.bank_path.read_bytes())
        self.enqueue()
        again = run(self.ledger, self.bank, inference, self.config)
        self.assertEqual(again["valid_drafts"], 0)
        self.assertEqual(len(inference.calls), 5)
        self.assertEqual(status(self.state)["drafts"], 5)
        rows = self.ledger.db.execute("SELECT payload,human_approval FROM drafts").fetchall()
        self.assertTrue(all(r[1] is None and json.loads(r[0])["prompt_version"] == "mcq-blind-v1" for r in rows))

    def test_atomic_claim_and_expired_lease_fencing(self):
        self.enqueue(1)
        other = Ledger(self.state)
        try:
            first = self.ledger.claim("first", self.config.model, self.config.reasoning, lease_seconds=1)
            self.assertIsNone(other.claim("second", self.config.model, self.config.reasoning))
            self.ledger.db.execute("UPDATE jobs SET lease_deadline=0")
            self.ledger.db.commit()
            new = other.claim("third", self.config.model, self.config.reasoning)
            self.assertEqual(new["attempt_count"], 2)
            self.assertNotEqual(first["lease_token"], new["lease_token"])
            self.assertCode("lost_lease", self.ledger.save_draft, first, response())
        finally:
            other.close()

    def test_stale_after_inference_requeues_no_draft(self):
        self.enqueue(1)
        def mutate(body):
            data = bank_data()
            data["questions"][0]["question"] += " changed"
            self.bank_path.write_text(json.dumps(data))
            return json.dumps(response())
        result = run(self.ledger, self.bank, FakeInference(mutate), self.config, limit=1)
        self.assertEqual(result["failed"], 1)
        self.assertEqual(status(self.state)["drafts"], 0)
        self.assertEqual(status(self.state)["counts"]["pending"], 1)

    def test_limits_pause_across_restart_and_explicit_resume(self):
        for code in ("subscription_sharing_usage_limit_exceeded", "subscription_sharing_usage_unavailable", "auth_required"):
            with self.subTest(code=code):
                self.ledger.resume()
                self.enqueue()
                def fail(_):
                    raise SolverError(code)
                inf = FakeInference(fail)
                result = run(self.ledger, self.bank, inf, self.config)
                self.assertEqual(result["paused"], 1)
                self.assertEqual(len(inf.calls), 1)
                self.assertEqual(status(self.state)["pause_reason"], code)
                self.assertCode("queue_paused", run, self.ledger, self.bank, inf, self.config)
        self.ledger.resume()
        self.assertIsNone(status(self.state)["pause_reason"])

    def test_network_retries_bounded_and_retry_after_honored(self):
        self.enqueue(1)
        def fail(_):
            raise SolverError("network_error", retry_after=120)
        inf = FakeInference(fail)
        before = time.time()
        run(self.ledger, self.bank, inf, self.config)
        row = self.ledger.db.execute("SELECT * FROM jobs").fetchone()
        self.assertGreaterEqual(row["next_eligible_at"], before + 120)
        run(self.ledger, self.bank, inf, self.config)
        self.assertEqual(len(inf.calls), 1)
        for _ in range(3):
            self.ledger.db.execute("UPDATE jobs SET next_eligible_at=0")
            self.ledger.db.commit()
            run(self.ledger, self.bank, inf, self.config)
        self.assertEqual(len(inf.calls), 3)
        self.assertEqual(status(self.state)["counts"], {"permanent_failed": 1})

    def test_stop_and_limit(self):
        self.enqueue()
        inf = FakeInference()
        self.assertTrue(run(self.ledger, self.bank, inf, self.config, stopping=lambda: True)["stopped"])
        self.assertEqual(inf.calls, [])
        self.assertCode("limit_exceeds_phase", run, self.ledger, self.bank, inf, self.config, 20)

    def test_worker_lock(self):
        with locked(self.state / "worker.lock"):
            with self.assertRaisesRegex(SolverError, "worker_busy"):
                with locked(self.state / "worker.lock", blocking=False):
                    pass


class AuthTests(Base):
    def token_payload(self, **kw):
        return {"access_token": "unit-test-access", "refresh_token": "unit-test-refresh", "id_token": "unit-test-id",
                "token_type": "Bearer", "expires_in": 3600, "scope": DIRECT_SCOPE, **kw}

    def store(self, outputs=()):
        return Credentials(self.root / "auth", FakeTransport(outputs), FakeIdentity())

    def test_pkce_state_nonce_and_registration(self):
        store = self.store([self.token_payload()])
        host = store.host()
        self.assertEqual(host, store.host())
        attempt = Attempt(host, "http://127.0.0.1:2222/auth/callback")
        params = parse_qs(urlsplit(attempt.url()).query)
        self.assertEqual(params["client_id"], ["dynamic_agent_client"])
        self.assertEqual(params["code_challenge_method"], ["S256"])
        self.assertEqual(len(params["code_challenge"][0]), 43)
        self.assertNotEqual(attempt.state, Attempt(host, attempt.redirect_uri).state)
        path = "/auth/callback?" + urlencode({"code": "test-code", "state": attempt.state, "client_id": "issued-client"})
        record = store.complete(attempt, path)
        self.assertEqual(record["client_id"], "issued-client")
        self.assertEqual(store.transport.calls[0][1]["form"]["redirect_uri"], attempt.redirect_uri)
        self.assertEqual(store.transport.calls[0][1]["form"]["code_verifier"], attempt.verifier)
        self.assertEqual((store.root / "registration.json").stat().st_mode & 0o777, 0o600)
        self.assertEqual(store.root.stat().st_mode & 0o777, 0o700)
        returning = Attempt(host, attempt.redirect_uri, record["client_id"])
        params = parse_qs(urlsplit(returning.url(record)).query)
        self.assertNotIn("agent_name_hint", params)
        self.assertEqual(params["id_token_hint"], ["unit-test-id"])

    def test_callback_state_client_and_error(self):
        a = Attempt("urn:uuid:example", "http://127.0.0.1:2222/auth/callback")
        for path in ("/auth/callback?state=wrong", "/wrong?state="+a.state,
                     "/auth/callback?state="+a.state+"&code=a", "/auth/callback?state="+a.state+"&state=x"):
            self.assertCode("invalid_callback", a.callback, path)
        self.assertCode("access_denied", a.callback, "/auth/callback?state="+a.state+"&error=access_denied")

    def test_missing_scope_retains_identity_but_blocks_inference(self):
        store = self.store([self.token_payload(scope="openid")])
        a = Attempt(store.host(), "http://127.0.0.1:2222/auth/callback")
        path = "/auth/callback?"+urlencode({"state": a.state, "code": "test", "client_id": "issued-client"})
        self.assertCode("missing_plan_scope", store.complete, a, path)
        self.assertEqual(store.read()["subject"], "subject")
        self.assertCode("missing_plan_scope", store.access_token)

    def test_no_implicit_consent_or_api_key(self):
        self.assertCode("api_key_disabled", Config, billing_mode="api_key")
        store = self.store()
        self.assertCode("eligibility_unconfirmed", login, store, Config(), approved=True)
        cfg = replace(Config(), eligibility="oss_self_hosted", eligibility_evidence="Operator verified public licensed worker repository.")
        self.assertCode("plan_approval_required", login, store, cfg)
        self.assertCode("credits_not_confirmed_disabled", cfg.require_inference)
        with patch.dict(os.environ, {"OPENAI_API_KEY": "unit-test-never-used"}):
            self.assertCode("auth_required", store.access_token)

    def test_refresh_replaces_rotating_token_atomically(self):
        store = self.store([self.token_payload(access_token="new-test-access", refresh_token="new-test-refresh")])
        host = store.host()
        old = store.token_record(self.token_payload(), {}, "issued-client", host, {"iss": ISSUER, "sub": "subject"})
        old["expires_at"] = 0
        store.write(old)
        self.assertEqual(store.access_token(), "new-test-access")
        self.assertEqual(store.read()["refresh_token"], "new-test-refresh")
        form = store.transport.calls[0][1]["form"]
        self.assertEqual(form["grant_type"], "refresh_token")
        self.assertNotIn("scope", form)
        self.assertEqual(store.access_token(), "new-test-access")
        self.assertEqual(len(store.transport.calls), 1)

    def test_revocation_clears_tokens_temporary_failure_does_not(self):
        for code, cleared in (("invalid_grant", True), ("network_error", False)):
            store = self.store([SolverError(code)])
            d = store.token_record(self.token_payload(), {}, "issued-client", store.host(), {"iss": ISSUER, "sub": "subject"})
            d["expires_at"] = 0
            store.write(d)
            self.assertCode(code, store.access_token)
            self.assertEqual("access_token" not in store.read(), cleared)
            self.assertEqual(store.read()["client_id"], "issued-client")

    def test_identity_mismatch_preserves_credentials(self):
        store = self.store()
        old = {"subject": "expected", "refresh_token": "test-refresh"}
        self.assertCode("invalid_identity", store.token_record, self.token_payload(), old, "client", "host", {"sub": "wrong", "iss": ISSUER})

    def test_vm_transfer_preserves_distinct_host(self):
        local = self.store()
        d = local.token_record(self.token_payload(), {}, "issued-client", local.host(), {"sub": "subject", "iss": ISSUER})
        remote = Credentials(self.root / "vm")
        self.assertCode("host_not_initialized", remote.import_transfer, d)
        host = remote.host()
        remote.import_transfer(d)
        self.assertEqual(remote.read()["ext_agent_host_id"], host)
        self.assertNotEqual(host, d["ext_agent_host_id"])
        self.assertCode("invalid_credentials", remote.import_transfer, d)

    def test_unsafe_permissions_and_symlink(self):
        store = self.store()
        store.host()
        store.write({"value": "test"})
        (store.root / "registration.json").chmod(0o644)
        self.assertCode("unsafe_permissions", store.read)
        other = self.root / "link"
        other.symlink_to(store.root, target_is_directory=True)
        self.assertCode("unsafe_path", Credentials(other).host)


class IdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import jwt
        from cryptography.hazmat.primitives.asymmetric import rsa
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(cls.key.public_key()))
        cls.jwk["kid"] = "test-key"

    def test_signature_issuer_audience_expiry_nonce(self):
        import jwt
        valid = {"iss": ISSUER, "sub": "person", "aud": "client", "iat": time.time(), "exp": time.time()+300, "nonce": "nonce"}
        cases = [({}, "nonce", True), ({"iss": "https://wrong.example"}, "nonce", False),
                 ({"aud": "wrong"}, "nonce", False), ({"exp": time.time()-100}, "nonce", False),
                 ({}, "wrong", False), ({"azp": "wrong"}, "nonce", False)]
        for changes, nonce, accepted in cases:
            t = FakeTransport([{"issuer": ISSUER, "jwks_uri": JWKS}, {"keys": [self.jwk]}])
            token = jwt.encode({**valid, **changes}, self.key, algorithm="RS256", headers={"kid": "test-key"})
            verifier = IdentityVerifier(t)
            if accepted:
                self.assertEqual(verifier.verify(token, "client", nonce)["sub"], "person")
            else:
                with self.assertRaisesRegex(SolverError, "invalid_identity"):
                    verifier.verify(token, "client", nonce)
        from cryptography.hazmat.primitives.asymmetric import rsa
        wrong_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        token = jwt.encode(valid, wrong_key, algorithm="RS256", headers={"kid": "test-key"})
        t = FakeTransport([{"issuer": ISSUER, "jwks_uri": JWKS}, {"keys": [self.jwk]}])
        with self.assertRaisesRegex(SolverError, "invalid_identity"):
            IdentityVerifier(t).verify(token, "client", "nonce")


class ClientAndCLITests(Base):
    def authorized_client(self, outputs):
        cfg = replace(self.config, eligibility="oss_self_hosted", eligibility_evidence="Unit-test eligibility only, not a real grant", credits_disabled_confirmed=True)
        class Auth:
            def access_token(self): return "unit-test-oauth"
        transport = FakeTransport(outputs)
        return OpenAIPlan(cfg, Auth(), transport), transport

    def test_exact_public_route_and_allowed_fields(self):
        client, t = self.authorized_client([sse(event())])
        body = request(self.bank.pending(1)[0], self.config.model, self.config.reasoning)
        client.respond(body)
        self.assertEqual(t.calls[0][0], RESOURCE+"/responses")
        self.assertEqual(t.calls[0][1]["token"], "unit-test-oauth")
        self.assertEqual(set(body), {"model", "reasoning", "instructions", "input", "store", "stream"})
        for key in ("temperature", "metadata", "max_output_tokens", "previous_response_id", "tools"):
            self.assertCode("invalid_request", client.respond, {**body, key: 1})
        self.assertCode("invalid_request", client.respond, {**body, "store": True})
        self.assertCode("invalid_request", client.respond, {**body, "stream": False})
        self.assertCode("invalid_request", client.respond, {**body, "input": [{"role": "system", "content": "hi"}]})

    def test_catalog_requires_account_models_not_public_data(self):
        client, t = self.authorized_client([{"models": [{"slug": "different"}]}])
        self.assertCode("model_unavailable", client.check_model)
        self.assertEqual(len(t.calls), 1)
        client, _ = self.authorized_client([{"data": [{"id": self.config.model}]}])
        self.assertCode("invalid_catalog", client.check_model)

    def test_successful_probe(self):
        client, t = self.authorized_client([{"models": [{"slug": self.config.model}]}, sse(event(text="MCQ_SOLVER_OK"))])
        client.probe()
        self.assertEqual(len(t.calls), 2)

    def test_catalog_allowed_before_credit_confirmation_but_inference_blocked(self):
        client, transport = self.authorized_client([{"models": [{"slug": self.config.model}]}])
        client.config = replace(client.config, credits_disabled_confirmed=False)
        self.assertEqual(client.models()[0]["slug"], self.config.model)
        body = request(self.bank.pending(1)[0], self.config.model, self.config.reasoning)
        self.assertCode("credits_not_confirmed_disabled", client.respond, body)
        self.assertEqual(len(transport.calls), 1)

    def test_dry_run_creates_no_state_or_auth_and_no_inference(self):
        for command in ("sync", "run"):
            new_state = self.root / ("fresh-"+command)
            args = parser().parse_args(["--bank", str(self.bank_path), "--state-dir", str(new_state), "--credentials-dir", str(self.root/"missing-auth"), command, "--dry-run"])
            with patch("mcq_solver.cli.OpenAIPlan", side_effect=AssertionError("must not infer")):
                result = execute(args)
            self.assertEqual(result["writes"], 0)
            self.assertFalse(new_state.exists())
            self.assertFalse((self.root/"missing-auth").exists())

    def test_error_logs_and_provider_codes_are_redacted(self):
        error = provider_error({"error": {"code": "Bearer SECRET_VALUE", "message": "SECRET_VALUE"}}, 401)
        self.assertNotIn("SECRET", str(error))
        output = io.StringIO()
        with redirect_stderr(output), patch("mcq_solver.cli.execute", side_effect=error):
            self.assertEqual(main(["doctor"]), 2)
        self.assertNotIn("SECRET", output.getvalue())

    def test_offline_import_idempotency_and_export(self):
        rows = [{"question_id": q.id, "question_version_hash": q.fingerprint, "response": response(q.id)} for q in self.bank.pending(5)]
        path = self.root / "results.json"
        path.write_text(json.dumps(rows))
        args = parser().parse_args(["--bank", str(self.bank_path), "--state-dir", str(self.state), "import-results", "--file", str(path)])
        first = execute(args)
        self.assertEqual(first["valid_drafts"], 5)
        self.assertEqual(execute(args)["valid_drafts"], 0)
        out = self.root / "review.csv"
        self.assertEqual(export_review(self.state, out)["exported"], 5)
        self.assertIn("offline-import", out.read_text())
        self.assertNotIn("access_token", out.read_text())
        self.assertEqual(out.stat().st_mode & 0o777, 0o600)

    def test_export_cannot_overwrite_bank(self):
        original = self.bank_path.read_bytes()
        with self.assertRaises(FileExistsError):
            export_review(self.state, self.bank_path)
        self.assertEqual(original, self.bank_path.read_bytes())

    def test_ambiguous_transfer_suspends_local_refresh_without_logging(self):
        store = Credentials(self.root / "transfer-auth")
        store.host()
        store.write({"access_token": "unit-test-access", "refresh_token": "unit-test-refresh", "client_id": "issued-client"})
        args = parser().parse_args(["--credentials-dir", str(store.root), "export-credentials", "--ssh-host", "example-vm",
                                    "--remote-python", "/opt/worker/bin/python", "--remote-credentials-dir", "/home/worker/auth"])
        import subprocess
        with patch("mcq_solver.cli.subprocess.run", side_effect=subprocess.TimeoutExpired("ssh", 30)):
            self.assertCode("transfer_uncertain", execute, args)
        self.assertTrue(store.read()["transferred"])
        self.assertCode("session_transferred", store.access_token)

    def test_export_formula_escaping(self):
        self.enqueue(1)
        def answer(body):
            return json.dumps(response(explanation="=HYPERLINK(\"https://example.invalid\",\"formula must not execute when the reviewer opens CSV\")"))
        run(self.ledger, self.bank, FakeInference(answer), self.config, 1)
        out = self.root / "escaped.csv"
        export_review(self.state, out)
        import csv
        with out.open() as f:
            row = next(csv.DictReader(f))
        self.assertTrue(row["explanation"].startswith("'="))

    def test_cli_no_traceback_for_unexpected_provider_shape(self):
        output = io.StringIO()
        with redirect_stderr(output), patch("mcq_solver.cli.execute", side_effect=AttributeError("unit-test-secret")):
            self.assertEqual(main(["doctor"]), 2)
        self.assertNotIn("unit-test-secret", output.getvalue())
        self.assertNotIn("Traceback", output.getvalue())


if __name__ == "__main__":
    unittest.main()
