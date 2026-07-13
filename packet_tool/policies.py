from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Callable, Dict, List, Tuple

PolicyResult = Tuple[bool, str]
PolicyFn = Callable[[Dict[str, Any]], PolicyResult]


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def rule_001_component_id(packet: Dict[str, Any]) -> PolicyResult:
    value = packet.get("component_id")
    if not _is_non_empty_string(value):
        return False, "component_id is missing or empty"
    if not re.fullmatch(r"C-\d{3}", value):
        return False, "component_id must match C-NNN (example: C-007)"
    return True, "ok"


def rule_002_release(packet: Dict[str, Any]) -> PolicyResult:
    value = packet.get("release")
    if value != "Release1-MVP":
        return False, "release must be exactly 'Release1-MVP'"
    return True, "ok"


def rule_003_owns(packet: Dict[str, Any]) -> PolicyResult:
    value = packet.get("owns")
    if not _is_non_empty_string(value):
        return False, "owns must be non-empty"

    normalized = value.upper()
    if "TBD" in normalized or "TODO" in normalized:
        return False, "owns must not contain TBD or TODO"
    return True, "ok"


def rule_004_does_not_own(packet: Dict[str, Any]) -> PolicyResult:
    value = packet.get("does_not_own")
    if not _is_non_empty_string(value):
        return False, "does_not_own must be non-empty"
    if value.strip().lower() == "none":
        return False, "does_not_own cannot be 'None'"
    return True, "ok"


def rule_005_fail_closed_behaviour(packet: Dict[str, Any]) -> PolicyResult:
    value = packet.get("fail_closed_behaviour")
    if not _is_non_empty_string(value):
        return False, "fail_closed_behaviour must be non-empty"

    lowered = value.lower()
    required_tokens = ("rejected", "blocked", "denied", "refused")
    if not any(token in lowered for token in required_tokens):
        return False, "fail_closed_behaviour must include rejected/blocked/denied/refused"
    return True, "ok"


def rule_006_acceptance_tests(packet: Dict[str, Any]) -> PolicyResult:
    value = packet.get("acceptance_tests")
    if not isinstance(value, list) or len(value) == 0:
        return False, "acceptance_tests must be a non-empty list"
    return True, "ok"


def rule_007_assembled_at(packet: Dict[str, Any]) -> PolicyResult:
    value = packet.get("assembled_at")
    if not _is_non_empty_string(value):
        return False, "assembled_at is missing or empty"
    if not value.endswith("Z"):
        return False, "assembled_at must end in 'Z'"

    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False, "assembled_at must be valid ISO 8601 UTC"

    return True, "ok"


def evaluate_policies(packet: Dict[str, Any]) -> List[Dict[str, str]]:
    rules: List[Tuple[str, PolicyFn]] = [
        ("RULE-001", rule_001_component_id),
        ("RULE-002", rule_002_release),
        ("RULE-003", rule_003_owns),
        ("RULE-004", rule_004_does_not_own),
        ("RULE-005", rule_005_fail_closed_behaviour),
        ("RULE-006", rule_006_acceptance_tests),
        ("RULE-007", rule_007_assembled_at),
    ]

    failures: List[Dict[str, str]] = []
    for rule_id, rule_fn in rules:
        passed, reason = rule_fn(packet)
        if not passed:
            failures.append({"rule": rule_id, "reason": reason})

    return failures
