import json
import re

from .adapters.base import Question
from .errors import SolverError

FIELDS = {"question_id", "selected_option_id", "explanation", "certainty", "review_required", "review_reasons", "topic"}
SECRET = re.compile(r"(?:sk-[A-Za-z0-9_-]{8,}|Bearer\s+\S+|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)", re.I)


def unique_pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate")
        value[key] = item
    return value


def strict_json(text):
    try:
        if not isinstance(text, str) or len(text) > 24000 or SECRET.search(text):
            raise ValueError("invalid")
        return json.loads(text, object_pairs_hook=unique_pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError("constant")))
    except (ValueError, TypeError):
        raise SolverError("invalid_json") from None


def validate(text: str, question: Question):
    d = strict_json(text)
    if not isinstance(d, dict) or set(d) != FIELDS:
        raise SolverError("invalid_response")
    if d["question_id"] != question.id:
        raise SolverError("invalid_question_id")
    selected = d["selected_option_id"]
    options = question.record["options"]
    if selected is not None and (not isinstance(selected, str) or selected not in {str(i) for i in range(len(options))}):
        raise SolverError("invalid_option")
    explanation = d["explanation"]
    if not isinstance(explanation, str) or not 40 <= len(explanation.strip()) <= 12000:
        raise SolverError("invalid_explanation")
    generic = re.fullmatch(r"(?:the )?(?:correct answer|answer|option [a-h0-7]|selected option).*(?:is correct|correct option|correct answer|only correct choice|selected option)[.!\s]*", explanation.strip(), re.I)
    if generic and not re.search(r"\d{2,}|[=+*/]", explanation):
        raise SolverError("invalid_explanation")
    if d["certainty"] not in {"confident", "uncertain", "cannot_determine"} or type(d["review_required"]) is not bool:
        raise SolverError("invalid_response")
    reasons = d["review_reasons"]
    if not isinstance(reasons, list) or len(reasons) > 20 or any(not isinstance(x, str) or not 3 <= len(x.strip()) <= 1000 for x in reasons):
        raise SolverError("invalid_response")
    if not isinstance(d["topic"], str) or len(d["topic"]) > 200:
        raise SolverError("invalid_response")
    if selected is None and not reasons:
        raise SolverError("invalid_option")
    if d["certainty"] == "cannot_determine" and selected is not None:
        raise SolverError("invalid_option")
    if d["certainty"] != "confident":
        reasons.append("model_uncertain")
    if selected is None:
        reasons.append("no_determinable_option")
    r = question.record
    if r.get("hasDiagram") or r.get("figureImage") or r.get("figureGroupId"):
        reasons.append("media_not_supplied")
    if r.get("passageId") and not r.get("passage"):
        reasons.append("passage_not_supplied")
    if r.get("sourceContextRef"):
        reasons.append("original_source_context_needs_inspection")
    if r.get("key_disputed") or r.get("sourceDefect"):
        reasons.append("existing_source_or_key_flag")
    if len(set(options)) != len(options):
        reasons.append("duplicate_options")
    agreement = None
    if r.get("answerSource") in {"official", "key"}:
        answer = r.get("answerIndex")
        if type(answer) is int and 0 <= answer < len(options):
            agreement = selected == str(answer) if selected is not None else None
            if agreement is False:
                reasons.append("official_key_disagreement")
        else:
            reasons.append("invalid_official_key_mapping")
    # Semantic relevance/source correctness requires human inspection, not length
    # heuristics or a model's self-rating. All Phase B drafts remain review-only.
    reasons.append("human_source_and_reasoning_review_pending")
    return {**d, "question_id": question.id, "review_required": True,
            "review_reasons": list(dict.fromkeys(reasons)), "official_key_agreement": agreement,
            "human_approval": None}
