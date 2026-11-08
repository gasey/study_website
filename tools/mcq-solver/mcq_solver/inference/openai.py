import json
import time

from ..errors import SolverError
from ..transport import RESOURCE, Transport, provider_error


def events(response):
    """Bounded SSE reader; only completed response payloads become drafts."""
    pending = []
    size = 0
    deadline = time.monotonic() + 300
    while True:
        line = response.readline(262145)
        if not line:
            return
        size += len(line)
        if len(line) > 262144 or size > 2_000_000 or time.monotonic() > deadline:
            raise SolverError("stream_too_large")
        try:
            line = line.decode("utf-8").rstrip("\r\n")
        except UnicodeError:
            raise SolverError("invalid_response") from None
        if line == "":
            if pending:
                raw = "\n".join(pending)
                pending = []
                if raw == "[DONE]":
                    return
                try:
                    event = json.loads(raw)
                except ValueError:
                    raise SolverError("invalid_response") from None
                if not isinstance(event, dict):
                    raise SolverError("invalid_response")
                yield event
        elif line.startswith("data:"):
            pending.append(line[5:].lstrip(" "))


def completed_text(stream, model):
    finished_items = {}
    for event in events(stream):
        kind = event.get("type")
        if kind == "response.output_item.done":
            index, item = event.get("output_index"), event.get("item")
            if type(index) is not int or not 0 <= index <= 100 or not isinstance(item, dict):
                raise SolverError("invalid_response")
            if item.get("status", "completed") != "completed":
                raise SolverError("invalid_response")
            if index in finished_items and finished_items[index] != item:
                raise SolverError("invalid_response")
            finished_items[index] = item
        if kind in {"response.failed", "error"}:
            response = event.get("response", event)
            if not isinstance(response, dict):
                raise SolverError("invalid_response")
            if response.get("error") or event.get("code"):
                raise provider_error(response if response.get("error") else {"error": event})
            raise SolverError("response_failed")
        if kind == "response.incomplete":
            raise SolverError("response_incomplete")
        if kind == "response.completed":
            response = event.get("response", {})
            if not isinstance(response, dict):
                raise SolverError("invalid_response")
            if response.get("status") != "completed" or response.get("error"):
                raise SolverError("invalid_response")
            # Do not accept an unexpected model as a silent fallback.
            actual = response.get("model")
            if actual != model:
                raise SolverError("model_unavailable")
            output = response.get("output", [])
            # This route can send finalized message items separately and an
            # empty terminal output array. Keep only output_item.done snapshots;
            # deltas and partially emitted messages are never draft material.
            if output == []:
                output = [finished_items[index] for index in sorted(finished_items)]
            if not isinstance(output, list) or any(not isinstance(item, dict) or not isinstance(item.get("content", []), list) or any(not isinstance(part, dict) for part in item.get("content", [])) for item in output):
                raise SolverError("invalid_response")
            texts = [part["text"] for item in output if item.get("type") == "message" and item.get("role") == "assistant"
                     for part in item.get("content", []) if part.get("type") == "output_text" and isinstance(part.get("text"), str)]
            if not texts:
                raise SolverError("invalid_response")
            return "".join(texts)
    raise SolverError("stream_truncated")


class OpenAIPlan:
    def __init__(self, config, credentials, transport=None):
        self.config, self.credentials = config, credentials
        self.transport = transport or Transport()

    def models(self):
        # Discovery is read-only and must remain available before the operator
        # confirms credit settings. Actual Responses requests keep that gate.
        self.config.require_eligibility()
        data = self.transport.json(RESOURCE + "/models", token=self.credentials.access_token())
        if not isinstance(data, dict) or not isinstance(data.get("models"), list):
            raise SolverError("invalid_catalog")
        return data["models"]

    def check_model(self):
        entries = [m for m in self.models() if isinstance(m, dict) and m.get("slug") == self.config.model]
        if len(entries) != 1:
            raise SolverError("model_unavailable")
        # High is documented for Sol. Overrides require a fresh successful probe;
        # unsupported reasoning is a stop, never an automatic quality downgrade.
        return entries[0]

    def respond(self, body):
        self.config.require_inference()
        allowed = {"model", "input", "instructions", "reasoning", "store", "stream"}
        if set(body) - allowed or body.get("store") is not False or body.get("stream") is not True or not isinstance(body.get("input"), list):
            raise SolverError("invalid_request")
        if body.get("model") != self.config.model or body.get("reasoning") != {"effort": self.config.reasoning}:
            raise SolverError("invalid_request")
        if any(item.get("role") == "system" for item in body["input"]):
            raise SolverError("invalid_request")
        with self.transport.open(RESOURCE + "/responses", body=body, token=self.credentials.access_token()) as response:
            return completed_text(response, self.config.model)

    def probe(self):
        self.check_model()
        result = self.respond({"model": self.config.model, "reasoning": {"effort": self.config.reasoning},
            "input": [{"role": "user", "content": "Return exactly the text MCQ_SOLVER_OK."}], "store": False, "stream": True})
        if result.strip() != "MCQ_SOLVER_OK":
            raise SolverError("invalid_probe")
