#!/usr/bin/env python3
"""Read-only legality check of routing examples against an exported registry.

Input: JSON with a top-level taxonomy array of active nodes, each carrying id,
level and parent_id. An explicit active=false node is rejected too. No question
or database is modified; passing does not establish semantic tagging accuracy.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate(policy, registry):
    errors = []
    if policy.get("policy_version") != "study-tagging-v1":
        errors.append("Unsupported policy version")
    if policy.get("candidate_review_status") != "pending":
        errors.append("Model candidates must remain pending")
    nodes = {}
    for node in registry["taxonomy"]:
        if node["id"] in nodes:
            errors.append(f"Duplicate registry ID: {node['id']}")
        nodes[node["id"]] = node
    keys = set()
    for route in policy["routes"]:
        key, path = route["key"], route["path"]
        if key in keys:
            errors.append(f"Duplicate route: {key}")
        keys.add(key)
        if not path.get("subject_id"):
            errors.append(f"{key}: subject is required")
        if path.get("subtopic_id") and not path.get("topic_id"):
            errors.append(f"{key}: subtopic requires a topic")
        parent = None
        for level in ("subject", "topic", "subtopic"):
            node_id = path.get(f"{level}_id")
            if not node_id:
                continue
            if node_id == "gk-gs" or node_id.startswith(("gk-gs:", "gk-gs/")):
                errors.append(f"{key}: display alias cannot be stored: {node_id}")
            node = nodes.get(node_id)
            if not node or node.get("active") is False:
                errors.append(f"{key}: missing/inactive node: {node_id}")
            elif node.get("level") != level or node.get("parent_id") != parent:
                errors.append(f"{key}: invalid level/parent: {node_id}")
            parent = node_id
    for gap in policy.get("taxonomy_gaps", []):
        if gap["key"] not in keys:
            errors.append(f"Gap has no fallback route: {gap['key']}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--policy", type=Path,
                        default=ROOT / "docs/question-tagging-policy.json")
    args = parser.parse_args()
    try:
        policy = json.loads(args.policy.read_text())
        registry = json.loads(args.registry.read_text())
        errors = validate(policy, registry)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        parser.error(str(exc))
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print(f"PASS: {len(policy['routes'])} routes against "
          f"{len(registry['taxonomy'])} registry nodes")
    print("Legal paths only; no questions reviewed or changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
