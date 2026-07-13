from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from packet_tool.assembler import build_packet, packet_hash
from packet_tool.parser import InputError, load_component_yaml
from packet_tool.policies import evaluate_policies


def _print_json(payload: dict) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def run(input_path: str, db_path: str) -> int:
    try:
        component = load_component_yaml(input_path)
    except InputError as exc:
        _print_json(
            {
                "status": "error",
                "errors": [{"rule": "INPUT-001", "reason": str(exc)}],
            }
        )
        return 1

    packet = build_packet(component, db_path)
    failures = evaluate_policies(packet)
    if failures:
        _print_json({"status": "error", "errors": failures})
        return 1

    final_packet = dict(packet)
    final_packet["packet_hash"] = packet_hash(packet)
    _print_json(final_packet)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Minimal policy-gated packet assembler")
    parser.add_argument("input", help="Path to YAML input file")
    parser.add_argument(
        "--db",
        default="packet_counter.db",
        help="Path to SQLite counter database (default: packet_counter.db)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    exit_code = run(args.input, args.db)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
