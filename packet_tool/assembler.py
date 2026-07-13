from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict

from packet_tool.counter import next_sequence

ASSEMBLER_VERSION = "test-assembler-v0.1"


def utc_now_iso_z() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_packet(component: Dict[str, Any], db_path: str) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    date_key = now.strftime("%Y%m%d")
    sequence = next_sequence(db_path, date_key)

    packet = {
        "packet_id": f"BAP-{date_key}-{sequence:03d}",
        "component_id": component.get("id"),
        "component_name": component.get("name"),
        "release": component.get("release"),
        "owns": component.get("owns"),
        "does_not_own": component.get("does_not_own"),
        "fail_closed_behaviour": component.get("fail_closed_behaviour"),
        "cr_authority": component.get("cr_authority"),
        "zones": component.get("zones"),
        "acceptance_tests": component.get("acceptance_tests"),
        "assembled_at": now.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "assembler_version": ASSEMBLER_VERSION,
    }
    return packet


def packet_hash(packet: Dict[str, Any]) -> str:
    serialized = json.dumps(packet, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
