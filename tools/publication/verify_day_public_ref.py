#!/usr/bin/env python3
"""Verify public GitHub raw/blob parity for Day/Week evidence publication."""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from html import unescape
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_REPO = "basilivanov/astro-project"
DEFAULT_BRANCH = "prod-release-20260327"
DEFAULT_EVIDENCE_DIR = "docs/review_evidence/front/day-week/2026-04-10-d479771"
README_NAME = "README.md"
CLOSEOUT_NAME = "post-test-review.md"
SPEC_PATH = "frontend/e2e/telegram-signed-auth.spec.ts"
USER_AGENT = "astro-public-ref-verifier/1.0"


@dataclass
class PublicRefResult:
    verdict: str
    checked_at: str
    branch: str
    branch_head: str | None
    published_from_commit: str | None
    dimensions: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    urls: dict[str, str] = field(default_factory=dict)


def fetch_text(url: str, *, retries: int = 3, delay: float = 1.5) -> str:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT, "Cache-Control": "no-cache"})
            with urlopen(request, timeout=20) as response:
                return response.read().decode("utf-8", errors="replace")
        except (HTTPError, URLError, TimeoutError) as exc:
            last_error = exc
            if attempt + 1 < retries:
                time.sleep(delay * (attempt + 1))
    raise RuntimeError(f"failed to fetch {url}: {last_error}")


def raw_url(repo: str, branch: str, path: str) -> str:
    return f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"


def blob_url(repo: str, branch: str, path: str) -> str:
    return f"https://github.com/{repo}/blob/{branch}/{path}"


def api_url(repo: str, branch: str) -> str:
    return f"https://api.github.com/repos/{repo}/commits/{branch}"


def extract_commit(text: str) -> str | None:
    match = re.search(r"published_from_commit:\s*`?([0-9a-f]{7,40})`?", text)
    return match.group(1) if match else None


def extract_verdict(text: str) -> str | None:
    match = re.search(r"Post-test observability gate\s+[—-]\s+(PASS_[A-Z_]+|FAIL_[A-Z_]+)", text)
    if match:
        return match.group(1)
    match = re.search(r"observability_closeout:\s*`?(PASS_[A-Z_]+|FAIL_[A-Z_]+)`?", text)
    return match.group(1) if match else None


def extract_proof_lane(text: str) -> str | None:
    match = re.search(r"proof_lane:\s*`?([^`\n]+)`?", text)
    return match.group(1).strip() if match else None


def visible_blob_text(html: str) -> str:
    return unescape(re.sub(r"<[^>]+>", " ", html))


def check_spec_public_text(text: str) -> tuple[bool, str]:
    has_real_lane = all(token in text for token in [
        "loads Today authenticated content via signed auth against real backend",
        "route.continue",
        "X-Request-ID",
        "signed-today-real",
        "/api/feed/today",
    ])
    old_mock = re.search(
        r"loads Today authenticated content via signed auth without mock mode.*?/api/feed/today.*?route\.fulfill",
        text,
        re.S,
    )
    if has_real_lane and not old_mock:
        return True, "pass"
    if old_mock:
        return False, "old_mock_today_proof_visible"
    return False, "real_backend_markers_missing"


def run(repo: str, branch: str, evidence_dir: str) -> PublicRefResult:
    checked_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    paths = {
        "raw_readme": raw_url(repo, branch, f"{evidence_dir}/{README_NAME}"),
        "raw_closeout": raw_url(repo, branch, f"{evidence_dir}/{CLOSEOUT_NAME}"),
        "raw_spec": raw_url(repo, branch, SPEC_PATH),
        "blob_closeout": blob_url(repo, branch, f"{evidence_dir}/{CLOSEOUT_NAME}"),
        "blob_spec": blob_url(repo, branch, SPEC_PATH),
        "api_commit": api_url(repo, branch),
    }
    result = PublicRefResult(
        verdict="fail",
        checked_at=checked_at,
        branch=branch,
        branch_head=None,
        published_from_commit=None,
        urls=paths,
    )
    try:
        commit_payload = json.loads(fetch_text(paths["api_commit"]))
        result.branch_head = str(commit_payload.get("sha") or "") or None
        raw_readme = fetch_text(paths["raw_readme"])
        raw_closeout = fetch_text(paths["raw_closeout"])
        raw_spec = fetch_text(paths["raw_spec"])
        blob_closeout = visible_blob_text(fetch_text(paths["blob_closeout"]))
        blob_spec = visible_blob_text(fetch_text(paths["blob_spec"]))
    except Exception as exc:
        result.errors.append(str(exc))
        result.dimensions["fetch"] = "fail"
        return result

    published = extract_commit(raw_readme)
    result.published_from_commit = published
    raw_readme_verdict = extract_verdict(raw_readme)
    raw_closeout_verdict = extract_verdict(raw_closeout)
    blob_closeout_verdict = extract_verdict(blob_closeout)
    proof_lane = extract_proof_lane(raw_readme)

    dimensions: dict[str, str] = {}
    if published and result.branch_head and result.branch_head.startswith(published):
        dimensions["commit_history"] = "pass"
    elif published and result.branch_head:
        dimensions["commit_history"] = "branch_head_after_published_commit"
    else:
        dimensions["commit_history"] = "missing_metadata"

    dimensions["raw_readme_closeout"] = "pass" if raw_readme_verdict == raw_closeout_verdict and raw_closeout_verdict else "mismatch"
    dimensions["blob_raw_closeout"] = "pass" if blob_closeout_verdict == raw_closeout_verdict and raw_closeout_verdict else "mismatch"
    dimensions["proof_lane"] = "pass" if proof_lane == "signed_telegram_today_real_backend + canonical_log_window" else "mismatch"

    raw_spec_ok, raw_spec_reason = check_spec_public_text(raw_spec)
    blob_spec_ok, blob_spec_reason = check_spec_public_text(blob_spec)
    dimensions["raw_spec"] = raw_spec_reason
    dimensions["blob_spec"] = blob_spec_reason

    result.dimensions = dimensions
    hard_pass = all(value in {"pass", "branch_head_after_published_commit"} for value in dimensions.values())
    result.verdict = "pass" if hard_pass and raw_spec_ok and blob_spec_ok else "fail"
    return result


def render_markdown(result: PublicRefResult) -> str:
    lines = [
        f"## Public Ref Parity — {'PASS' if result.verdict == 'pass' else 'FAIL'}",
        f"- public_ref_verified_at: `{result.checked_at}`",
        f"- public_ref_verdict: `{result.verdict}`",
        f"- branch: `{result.branch}`",
        f"- branch_head: `{result.branch_head or 'unknown'}`",
        f"- published_from_commit: `{result.published_from_commit or 'missing'}`",
        "- dimensions:",
    ]
    for key, value in result.dimensions.items():
        lines.append(f"  - {key}: `{value}`")
    if result.errors:
        lines.append("- errors:")
        for error in result.errors:
            lines.append(f"  - `{error}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--branch", default=DEFAULT_BRANCH)
    parser.add_argument("--evidence-dir", default=DEFAULT_EVIDENCE_DIR)
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args()
    result = run(args.repo, args.branch, args.evidence_dir)
    if args.format == "json":
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    else:
        print(render_markdown(result))
    return 0 if result.verdict == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
