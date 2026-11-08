from dataclasses import dataclass
from pathlib import Path
import tomllib

from .errors import SolverError


@dataclass(frozen=True)
class Config:
    billing_mode: str = "chatgpt_plan"
    model: str = "gpt-6.1-sol"
    reasoning: str = "high"
    eligibility: str = "unconfirmed"
    eligibility_evidence: str = ""
    credits_disabled_confirmed: bool = False

    def __post_init__(self):
        if self.billing_mode != "chatgpt_plan":
            raise SolverError("api_key_disabled")
        if not isinstance(self.model, str) or not self.model or len(self.model) > 100:
            raise SolverError("invalid_config")
        if self.reasoning not in {"low", "medium", "high", "xhigh", "max"}:
            raise SolverError("invalid_config")

    def require_eligibility(self):
        if self.eligibility not in {"oss_self_hosted", "openai_authorized"} or not isinstance(self.eligibility_evidence, str) or len(self.eligibility_evidence.strip()) < 20:
            raise SolverError("eligibility_unconfirmed")

    def require_inference(self):
        self.require_eligibility()
        if self.credits_disabled_confirmed is not True:
            raise SolverError("credits_not_confirmed_disabled")

    @classmethod
    def read(cls, path: Path):
        if not path.exists():
            return cls()
        try:
            return cls(**tomllib.loads(path.read_text()))
        except (ValueError, TypeError):
            raise SolverError("invalid_config") from None
