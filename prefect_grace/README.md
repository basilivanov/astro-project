# Prefect Grace Scaffold

This directory contains a phase-1 file-backed scaffold for Prefect-driven GRACE execution.

## Structure

- `flows/` — Prefect flows.
- `tasks/` — task helpers for file-backed orchestration.
- `prompts/` — role prompts in English.
- `roles/` — role contracts and responsibility docs.
- `templates/` — feature and packet templates.
- `packets/` — generated packet workspace placeholder.
- `state/` — YAML/JSON state for features, packets, reviews, and decisions.
- `state/` — YAML/JSON state for features, packets, reviews, verifications, and decisions.

## Current purpose

Phase 1 is intentionally conservative:
- define the operating model;
- define role contracts;
- define prompt templates;
- define file-backed state layout;
- provide Prefect entry scaffold;
- provide a Codex subprocess launcher wired through `codexN` and cliproxy.

The scaffold can already dry-run or execute a packet through a configured `codexN` wrapper.
It now parses verifier, reviewer, and architect-wave outputs and injects dependency context into downstream agent prompts.
It also supports live Prefect deployments, a scheduled state dashboard artifact, a YAML business-feature intake contract, and an LLM-driven verifier that executes packet contracts through Codex.

## Runtime portability

The orchestration layer is portable across projects if you keep the runtime boundary explicit:
- Prefect server/API/UI can stay shared infrastructure;
- the project gets its own process worker, work pool, queues, and working directory;
- project-specific values can be overridden through `prefect_grace/runtime.yaml` or environment variables.

See `prefect_grace/runtime.yaml.example` for the minimal knobs.
