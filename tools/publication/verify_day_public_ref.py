#!/usr/bin/env python3
"""Fail-closed public GitHub parity gate for Day/Week proof publication."""
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
DAY_BRIEF_PATH = "frontend/lib/day-brief.ts"
DAY_PAGE_PATH = "frontend/app/page.tsx"
USER_AGENT = "astro-public-ref-verifier/2.0"
PASS_VERDICT = "PUBLICLY_VERIFIED_CLEAN"
FAIL_VERDICT = "FAIL_NO_PUBLIC_REF_PARITY"
REQUIRED_METADATA = (
    "published_from_commit",
    "branch_head",
    "evidence_generated_at",
    "proof_lane",
    "closeout_source",
    "observability_closeout",
)


@dataclass
class PublicRefResult:
    verdict: str
    checked_at: str
    branch: str
    branch_head: str | None
    expected_head: str | None
    expected_published_from: str | None
    published_from_commit: str | None
    dimensions: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, str | None] = field(default_factory=dict)
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


def raw_url(repo: str, ref: str, path: str) -> str:
    return f"https://raw.githubusercontent.com/{repo}/{ref}/{path}"


def raw_cdn_url(repo: str, ref: str, path: str) -> str:
    return f"https://cdn.jsdelivr.net/gh/{repo}@{ref}/{path}"


def blob_url(repo: str, ref: str, path: str) -> str:
    return f"https://github.com/{repo}/blob/{ref}/{path}"


def api_commit_url(repo: str, ref: str) -> str:
    return f"https://api.github.com/repos/{repo}/commits/{ref}"


def api_history_url(repo: str, branch: str) -> str:
    return f"https://api.github.com/repos/{repo}/commits?sha={branch}&per_page=10"


def history_url(repo: str, branch: str) -> str:
    return f"https://github.com/{repo}/commits/{branch}"


def visible_blob_text(html: str) -> str:
    text = html
    raw_match = re.search(r'"rawLines":\[(.*?)\],"stylingDirectives"', text, re.S)
    if raw_match:
        try:
            return "\n".join(json.loads(f"[{raw_match.group(1)}]"))
        except Exception:
            pass
    text = unescape(text)
    text = text.replace("\u003c", "<").replace("\u003e", ">").replace("\u0026", "&")
    return unescape(re.sub(r"<[^>]+>", " ", text))


def extract_metadata(text: str) -> dict[str, str | None]:
    metadata: dict[str, str | None] = {}
    for key in REQUIRED_METADATA:
        match = re.search(rf"{re.escape(key)}:\s*`?([^`\n]+)`?", text)
        metadata[key] = match.group(1).strip() if match else None
    return metadata


def extract_observability_verdict(text: str) -> str | None:
    match = re.search(r"Post-test observability gate\s+[—-]\s+(PASS_[A-Z_]+|FAIL_[A-Z_]+)", text)
    if match:
        return match.group(1)
    return extract_metadata(text).get("observability_closeout")


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



def check_day_surface_public_text(day_brief_text: str, day_page_text: str) -> tuple[bool, str]:
    forbidden_brief = [
        'title: "Сегодня"',
        'subtitle: "Четыре ключевые сферы на сегодня."',
        'Открыть неделю',
        'История разборов',
        'Открыть premium',
    ]
    forbidden_page = [
        'today-premium-block',
        'actionLabel="Открыть неделю"',
        'actionHref="/week"',
    ]
    leaked = [f"day_brief:{token}" for token in forbidden_brief if token in day_brief_text]
    leaked.extend(f"day_page:{token}" for token in forbidden_page if token in day_page_text)
    required = [
        'hero: DayBriefHero | null',
        'const cta = isRecord(source.cta)',
        'TodayCtaPanel',
    ]
    combined_text = day_brief_text + "\n" + day_page_text
    missing = [token for token in required if token not in combined_text]
    if leaked:
        return False, "old_day_surface_markers_visible"
    if missing:
        return False, "strict_day_surface_markers_missing"
    return True, "pass"

def commit_from_api(payload: Any) -> str | None:
    if isinstance(payload, dict):
        return str(payload.get("sha") or "") or None
    return None


def history_contains(history_payload: Any, commit: str | None) -> bool:
    if not commit or not isinstance(history_payload, list):
        return False
    return any(str(item.get("sha") or "").startswith(commit) for item in history_payload if isinstance(item, dict))


def same_metadata(left: dict[str, str | None], right: dict[str, str | None]) -> bool:
    return all(left.get(key) == right.get(key) and bool(left.get(key)) for key in REQUIRED_METADATA)


def same_non_head_metadata(left: dict[str, str | None], right: dict[str, str | None]) -> bool:
    keys = tuple(key for key in REQUIRED_METADATA if key != "branch_head")
    return all(left.get(key) == right.get(key) and bool(left.get(key)) for key in keys)


def same_branch_head_metadata(*metadata_sets: dict[str, str | None]) -> bool:
    values = [metadata.get("branch_head") for metadata in metadata_sets]
    return bool(values and values[0] and all(value == values[0] for value in values))


def run(repo: str, branch: str, evidence_dir: str, *, expected_head: str | None, expected_published_from: str | None) -> PublicRefResult:
    checked_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    paths = {
        "api_branch_head": api_commit_url(repo, branch),
        "api_branch_history": api_history_url(repo, branch),
        "branch_history": history_url(repo, branch),
        "raw_readme": raw_url(repo, branch, f"{evidence_dir}/{README_NAME}"),
        "raw_closeout": raw_url(repo, branch, f"{evidence_dir}/{CLOSEOUT_NAME}"),
        "raw_spec": raw_url(repo, branch, SPEC_PATH),
        "blob_readme": blob_url(repo, branch, f"{evidence_dir}/{README_NAME}"),
        "blob_closeout": blob_url(repo, branch, f"{evidence_dir}/{CLOSEOUT_NAME}"),
        "blob_spec": blob_url(repo, branch, SPEC_PATH),
        "blob_day_brief": blob_url(repo, branch, DAY_BRIEF_PATH),
        "blob_day_page": blob_url(repo, branch, DAY_PAGE_PATH),
        "raw_cdn_readme": raw_cdn_url(repo, branch, f"{evidence_dir}/{README_NAME}"),
        "raw_cdn_closeout": raw_cdn_url(repo, branch, f"{evidence_dir}/{CLOSEOUT_NAME}"),
    }
    result = PublicRefResult(
        verdict=FAIL_VERDICT,
        checked_at=checked_at,
        branch=branch,
        branch_head=None,
        expected_head=expected_head,
        expected_published_from=expected_published_from,
        published_from_commit=None,
        urls=paths,
    )
    try:
        branch_payload = json.loads(fetch_text(paths["api_branch_head"]))
        history_payload = json.loads(fetch_text(paths["api_branch_history"]))
        branch_history_page = visible_blob_text(fetch_text(paths["branch_history"]))
        raw_readme = fetch_text(paths["raw_readme"])
        raw_closeout = fetch_text(paths["raw_closeout"])
        if expected_head and raw_url(repo, expected_head, f"{evidence_dir}/{README_NAME}") != paths["raw_readme"]:
            expected_raw_readme = fetch_text(raw_url(repo, expected_head, f"{evidence_dir}/{README_NAME}"))
            if extract_metadata(raw_readme) != extract_metadata(expected_raw_readme):
                raw_readme = fetch_text(paths["raw_cdn_readme"])
        if expected_head and raw_url(repo, expected_head, f"{evidence_dir}/{CLOSEOUT_NAME}") != paths["raw_closeout"]:
            expected_raw_closeout = fetch_text(raw_url(repo, expected_head, f"{evidence_dir}/{CLOSEOUT_NAME}"))
            if extract_metadata(raw_closeout) != extract_metadata(expected_raw_closeout):
                raw_closeout = fetch_text(paths["raw_cdn_closeout"])
        raw_spec = fetch_text(paths["raw_spec"])
        blob_readme = visible_blob_text(fetch_text(paths["blob_readme"]))
        blob_closeout = visible_blob_text(fetch_text(paths["blob_closeout"]))
        blob_spec = visible_blob_text(fetch_text(paths["blob_spec"]))
        blob_day_brief = visible_blob_text(fetch_text(paths["blob_day_brief"]))
        blob_day_page = visible_blob_text(fetch_text(paths["blob_day_page"]))
    except Exception as exc:
        result.errors.append(str(exc))
        result.dimensions["fetch"] = "fail"
        return result

    result.branch_head = commit_from_api(branch_payload)
    raw_readme_meta = extract_metadata(raw_readme)
    raw_closeout_meta = extract_metadata(raw_closeout)
    blob_readme_meta = extract_metadata(blob_readme)
    blob_closeout_meta = extract_metadata(blob_closeout)

    expected_head = expected_head or result.branch_head
    expected_published_from = expected_published_from or raw_readme_meta.get("published_from_commit")
    if expected_head and result.branch_head and result.branch_head.startswith(expected_head):
        expected_head = result.branch_head
    result.expected_head = expected_head
    result.expected_published_from = expected_published_from

    result.metadata = raw_readme_meta
    result.published_from_commit = raw_readme_meta.get("published_from_commit")

    dimensions: dict[str, str] = {}
    try:
        exact_payload = json.loads(fetch_text(api_commit_url(repo, expected_published_from))) if expected_published_from else None
        exact_commit_ok = bool(commit_from_api(exact_payload))
    except Exception as exc:
        exact_commit_ok = False
        result.errors.append(f"exact_commit_fetch: {exc}")
    dimensions["exact_commit"] = "pass" if exact_commit_ok else "fail"
    dimensions["branch_head"] = "pass" if result.branch_head and expected_head and result.branch_head.startswith(expected_head) else "mismatch"
    dimensions["branch_history_api"] = "pass" if history_contains(history_payload, expected_head) else "missing_expected_head"
    dimensions["branch_history_page"] = "pass" if expected_head and expected_head[:7] in branch_history_page else "missing_expected_head"
    dimensions["metadata_complete"] = "pass" if all(raw_readme_meta.get(key) for key in REQUIRED_METADATA) else "missing_metadata"
    dimensions["readme_post_review_raw_meta"] = "pass" if same_non_head_metadata(raw_readme_meta, raw_closeout_meta) else "mismatch"
    dimensions["readme_blob_meta"] = "pass" if same_non_head_metadata(raw_readme_meta, blob_readme_meta) else "mismatch"
    dimensions["post_review_blob_meta"] = "pass" if same_non_head_metadata(raw_closeout_meta, blob_closeout_meta) else "mismatch"
    dimensions["published_from_expected"] = "pass" if expected_published_from and result.published_from_commit == expected_published_from else "mismatch"
    dimensions["branch_head_metadata"] = "pass" if same_branch_head_metadata(raw_readme_meta, raw_closeout_meta, blob_readme_meta, blob_closeout_meta) else "mismatch"
    dimensions["closeout_verdict_raw_blob"] = "pass" if extract_observability_verdict(raw_closeout) == extract_observability_verdict(blob_closeout) == "PASS_CLEAN" else "mismatch"
    dimensions["proof_lane"] = "pass" if raw_readme_meta.get("proof_lane") == "signed_telegram_today_real_backend + canonical_log_window" else "mismatch"

    raw_spec_ok, raw_spec_reason = check_spec_public_text(raw_spec)
    blob_spec_ok, blob_spec_reason = check_spec_public_text(blob_spec)
    day_surface_ok, day_surface_reason = check_day_surface_public_text(blob_day_brief, blob_day_page)
    day_finish_claim_ok = "Strict Day Surface Parity: PASS" in blob_readme
    dimensions["raw_spec"] = raw_spec_reason
    dimensions["blob_spec"] = blob_spec_reason
    dimensions["branch_day_surface"] = day_surface_reason
    dimensions["day_finish_claim"] = "pass" if day_finish_claim_ok else "missing_finish_claim"

    result.dimensions = dimensions
    result.verdict = PASS_VERDICT if all(value == "pass" for value in dimensions.values()) and raw_spec_ok and blob_spec_ok and day_surface_ok and day_finish_claim_ok else FAIL_VERDICT
    return result


def render_markdown(result: PublicRefResult) -> str:
    lines = [
        f"## Public Ref Parity — {'PASS' if result.verdict == PASS_VERDICT else 'FAIL'}",
        f"- public_ref_verified_at: `{result.checked_at}`",
        f"- public_ref_verdict: `{result.verdict}`",
        f"- branch: `{result.branch}`",
        f"- branch_head: `{result.branch_head or 'unknown'}`",
        f"- expected_head: `{result.expected_head or 'missing'}`",
        f"- published_from_commit: `{result.published_from_commit or 'missing'}`",
        f"- expected_published_from: `{result.expected_published_from or 'missing'}`",
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
    parser.add_argument("--expected-head")
    parser.add_argument("--expected-published-from")
    parser.add_argument("--format", choices=("json", "md"), default="md")
    args = parser.parse_args()
    result = run(
        args.repo,
        args.branch,
        args.evidence_dir,
        expected_head=args.expected_head,
        expected_published_from=args.expected_published_from,
    )
    if args.format == "json":
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    else:
        print(render_markdown(result))
    return 0 if result.verdict == PASS_VERDICT else 1


if __name__ == "__main__":
    sys.exit(main())
