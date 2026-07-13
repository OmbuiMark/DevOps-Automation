# Minimal Policy-Gated Packet Assembler

A Python CLI tool that:
1. Parses a YAML component definition.
2. Assembles a micro-packet with a SQLite-backed atomic sequence ID.
3. Runs explicit policy-gate rules (RULE-001..RULE-007).
4. Emits either a valid packet JSON with `packet_hash` or a structured error JSON.

## Requirements

- Python 3.10+
- PyYAML

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py <path-to-yaml> [--db packet_counter.db]
```

Example:

```bash
python main.py test_inputs/test1_valid.yaml
```

## Implementation Notes

- Atomic packet sequence is stored in SQLite table `packet_counters` keyed by `YYYYMMDD`.
- Sequence allocation uses a transaction with `BEGIN IMMEDIATE`, `INSERT OR IGNORE`, then `UPDATE seq = seq + 1`, preventing duplicate IDs under overlapping executions.
- Policy gate is implemented as explicit named rule functions in `packet_tool/policies.py`.
- Deterministic hash is SHA-256 over sorted-key JSON of the assembled packet (before adding `packet_hash`).

## Test Inputs

- `test_inputs/test1_valid.yaml`
- `test_inputs/test2_does_not_own_none.yaml`
- `test_inputs/test3_empty_acceptance_tests.yaml`
- `test_inputs/test4_release2.yaml`

## Commands Run and Outputs

Note: outputs below are captured from actual runs on 2026-07-13.

### Test 1
Input: valid C-007 YAML  
Expected: pass with packet and hash

Command:

```bash
python main.py test_inputs/test1_valid.yaml
```

Output:

```json
{
  "packet_id": "BAP-20260713-001",
  "component_id": "C-007",
  "component_name": "Sentinel Request Gateway",
  "release": "Release1-MVP",
  "owns": "Inbound request authentication, rate limiting, structured request logging",
  "does_not_own": "Downstream service routing, payload transformation, response caching",
  "fail_closed_behaviour": "If the gateway is unavailable, all inbound requests are rejected with HTTP 503. No requests are passed downstream without gateway validation.",
  "cr_authority": "BFS-SPEC-003 Section 4.2",
  "zones": [
    "Zone-External"
  ],
  "acceptance_tests": [
    "AT-REQ-001",
    "AT-REQ-002",
    "AT-REQ-004"
  ],
  "assembled_at": "2026-07-13T04:42:31Z",
  "assembler_version": "test-assembler-v0.1",
  "packet_hash": "131bac2a859bb0fe370cd4dc6aec85560f8062ab40abfbee6ad7b28997affd18"
}
```

Exit code: `0`

### Test 2
Input: `does_not_own: "None"`  
Expected: RULE-004 fails

Command:

```bash
python main.py test_inputs/test2_does_not_own_none.yaml
```

Output:

```json
{
  "status": "error",
  "errors": [
    {
      "rule": "RULE-004",
      "reason": "does_not_own cannot be 'None'"
    }
  ]
}
```

Exit code: `1`

### Test 3
Input: `acceptance_tests: []`  
Expected: RULE-006 fails

Command:

```bash
python main.py test_inputs/test3_empty_acceptance_tests.yaml
```

Output:

```json
{
  "status": "error",
  "errors": [
    {
      "rule": "RULE-006",
      "reason": "acceptance_tests must be a non-empty list"
    }
  ]
}
```

Exit code: `1`

### Test 4
Input: `release: "Release2"`  
Expected: RULE-002 fails

Command:

```bash
python main.py test_inputs/test4_release2.yaml
```

Output:

```json
{
  "status": "error",
  "errors": [
    {
      "rule": "RULE-002",
      "reason": "release must be exactly 'Release1-MVP'"
    }
  ]
}
```

Exit code: `1`

### Test 5
Input: run Test 1 twice rapidly from a clean database  
Expected: packet IDs increment from `...-001` then `...-002`

Command:

```bash
rm -f packet_counter.db
python main.py test_inputs/test1_valid.yaml
python main.py test_inputs/test1_valid.yaml
```

Output excerpts:

```json
{
  "packet_id": "BAP-20260713-001",
  "assembled_at": "2026-07-13T04:42:46Z",
  "packet_hash": "f3fac7eca63f59eaa514a861bf5444158e918e9039c31e7b3f2bbe92c3cc6d16"
}
{
  "packet_id": "BAP-20260713-002",
  "assembled_at": "2026-07-13T04:42:46Z",
  "packet_hash": "c72395232bc68cc18b5a45b8a9c52b4f522e821ddc71b6422c9fd18223d73d48"
}
```

Exit codes: `0`, `0`

## Assumptions

- YAML has a top-level `component` object.
- `packet_hash` should be calculated over the assembled packet payload before appending `packet_hash` itself.
- Sequence is scoped per UTC date (`YYYYMMDD`) as implied by packet format.
- If input YAML is malformed or missing required structure, tool returns structured error with rule `INPUT-001` and exit code 1.

## Design Decisions

- Kept solution intentionally small and modular:
  - `packet_tool/parser.py` for ingestion
  - `packet_tool/counter.py` for SQLite atomic sequencing
  - `packet_tool/assembler.py` for packet construction + hash
  - `packet_tool/policies.py` for explicit rule functions
  - `main.py` for CLI orchestration
- Explicit policy functions improve readability, traceability, and ease of extension.
- Structured JSON error format includes all failing rules in one response.

## Deliberate Simplifications

- No external config system: constants are hardcoded per spec.
- No formal unit test framework added since the task requested command-line test case outputs and straightforward implementation.
- No containerization or packaging metadata added to keep submission focused.

## Time Spent (Self-Reported)

- Start: 2026-07-13 04:20 UTC
- Submit: 2026-07-13 04:50 UTC
- Total: 30 minutes

## What Was Straightforward vs Harder

- Straightforward: YAML parsing, policy function structure, deterministic hash.
- Harder than expected: ensuring SQLite sequence allocation remains atomic under overlapping executions while keeping implementation minimal.
