# Review 0001 - FEAT-GRACE-PACKET-YAML-CONTRACT

**Verdict:** `accepted`
**Timestamp:** `2026-05-28T18:34:15Z`

## Review Notes

- `parse_packet_markdown(Path(.../EXECUTION_PACKET.md))` now discovers canonical `EXECUTION_PACKET.yaml` sidecars while raw-string and markdown-only parsing remain compatible.
- Sidecar fields override markdown metadata and list sections, including `depends_on`, scopes, verification, and evidence fields.
- Sidecar-aware packets include the normalized YAML payload in `source_hash`; markdown-only packet hashes remain unchanged.
- Invalid sidecars, packet id mismatches, and unknown top-level YAML fields fail closed in strict and legacy warning modes.
- Bootstrap dependency planning now consumes YAML sidecar `depends_on` through the existing parser API.

## Verification

- `pytest`: 67 passed.
- `compileall`: passed for `prefect_grace/platform/packet_parser.py`.
- `grace_lint`: passed for `prefect_grace/platform/packet_parser.py`.
- `validate-packet --strict`: ok=true.
- `validate-evidence-manifest`: ok=true, artifact validation ok; existing contract parser emitted a non-blocking `unknown_evidence_id` warning.
- `git diff --check`: passed.
- Scope check: outside_allowed=[].
- Real `bootstrap-backlog --dry-run` infers this packet as `ready` before review acceptance.

## Residual Notes

- Evidence validation remains `degraded-but-expected` only because this repository's current evidence contract parser returns an empty requirement set for this packet shape.
