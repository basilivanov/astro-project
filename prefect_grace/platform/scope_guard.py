# ############################################################################
# AI_HEADER: scope_guard
# ROLE: Evaluates path permissions, checking allowed and frozen repo patterns.
# ############################################################################

# START_MODULE_CONTRACT
# purpose: Verify that modified file paths strictly fall inside permitted scopes and do not intersect frozen files.
# inputs: Path strings, allowed patterns, frozen patterns.
# returns: Boolean permissions decisions.
# side_effects: none.
# emitted_logs: none.
# error_behavior: none.
# END_MODULE_CONTRACT

# START_MODULE_MAP
# mapping:
#   - function: normalize_path
#   - function: glob_to_regex
#   - function: path_matches_pattern
#   - function: is_path_allowed
#   - function: is_path_frozen
#   - function: has_overlap
#   - function: evaluate_diff_scope
#   - function: should_block_diff
# END_MODULE_MAP

from __future__ import annotations

import posixpath
import re
from pathlib import Path

# START_BLOCK: path_matching

DEFAULT_REPO_ROOT = "/opt/astro-project"

# START_FUNCTION_CONTRACT
# name: normalize_path
# purpose: Normalizes a given path to a clean repository-relative POSIX path representation.
# inputs:
#   path: raw path string.
#   repo_root: repository root path (optional).
# returns: relative path string using POSIX separators.
# side_effects: none.
# emitted_logs: none.
# error_behavior: none.
# END_FUNCTION_CONTRACT
def normalize_path(path: str, repo_root: str | Path | None = None) -> str:
    root = str(repo_root or DEFAULT_REPO_ROOT).replace("\\", "/")
    root = posixpath.normpath(root)
    raw_path = posixpath.normpath(path.replace("\\", "/"))
    root_without_slash = root.lstrip("/")
    if not raw_path.startswith("/") and (
        raw_path == root_without_slash or raw_path.startswith(root_without_slash + "/")
    ):
        raw_path = "/" + raw_path
    if raw_path.startswith("/"):
        absolute_path = posixpath.normpath(raw_path)
    else:
        absolute_path = posixpath.normpath(posixpath.join(root, raw_path))

    if absolute_path == root:
        return ""
    root_prefix = root.rstrip("/") + "/"
    if absolute_path.startswith(root_prefix):
        return absolute_path[len(root_prefix):]
    return "__outside_repo__/" + absolute_path.lstrip("/")


# START_FUNCTION_CONTRACT
# name: glob_to_regex
# purpose: Translates standard glob wildcard patterns to compiled python re.Pattern instances.
# inputs:
#   pattern: glob string.
# returns: compiled re.Pattern matching the glob logic.
# side_effects: none.
# emitted_logs: none.
# error_behavior: none.
# END_FUNCTION_CONTRACT
def glob_to_regex(pattern: str) -> re.Pattern:
    escaped = re.escape(pattern)
    escaped = escaped.replace(r'\*\*/', r'(?:.*/)?')
    escaped = escaped.replace(r'\*\*', r'.*')
    escaped = escaped.replace(r'\*', r'[^/]*')
    escaped = escaped.replace(r'\?', r'[^/]')
    return re.compile(f"^{escaped}$")


# START_FUNCTION_CONTRACT
# name: path_matches_pattern
# purpose: Check whether a single path matches a given glob pattern or prefix directory.
# inputs:
#   path: raw path string.
#   pattern: pattern glob string.
#   repo_root: repository root directory (optional).
# returns: True if matching, False otherwise.
# side_effects: none.
# emitted_logs: none.
# error_behavior: none.
# END_FUNCTION_CONTRACT
def path_matches_pattern(path: str, pattern: str, repo_root: str | Path | None = None) -> bool:
    norm_path = normalize_path(path, repo_root)
    norm_pattern = normalize_path(pattern, repo_root)

    if not any(c in norm_pattern for c in ("*", "?")):
        return norm_path == norm_pattern

    regex = glob_to_regex(norm_pattern)
    return bool(regex.match(norm_path))

# END_BLOCK: path_matching

# START_BLOCK: guard_policies

# START_FUNCTION_CONTRACT
# name: is_path_allowed
# purpose: Determines if a path falls inside any allowed patterns.
# inputs:
#   path: raw path string.
#   allowed_patterns: list of allowed glob patterns.
#   repo_root: repo root directory (optional).
# returns: True if inside, False otherwise.
# side_effects: none.
# emitted_logs: none.
# error_behavior: none.
# END_FUNCTION_CONTRACT
def is_path_allowed(path: str, allowed_patterns: list[str], repo_root: str | Path | None = None) -> bool:
    if not allowed_patterns:
        return False
    return any(path_matches_pattern(path, pattern, repo_root) for pattern in allowed_patterns)


# START_FUNCTION_CONTRACT
# name: is_path_frozen
# purpose: Determines if a path matches any frozen patterns.
# inputs:
#   path: raw path string.
#   frozen_patterns: list of frozen glob patterns.
#   repo_root: repo root directory (optional).
# returns: True if frozen, False otherwise.
# side_effects: none.
# emitted_logs: none.
# error_behavior: none.
# END_FUNCTION_CONTRACT
def is_path_frozen(path: str, frozen_patterns: list[str], repo_root: str | Path | None = None) -> bool:
    if not frozen_patterns:
        return False
    return any(path_matches_pattern(path, pattern, repo_root) for pattern in frozen_patterns)


# START_FUNCTION_CONTRACT
# name: has_overlap
# purpose: Checks if two scopes of patterns overlap.
# inputs:
#   allowed_patterns_1: list of glob patterns.
#   allowed_patterns_2: list of glob patterns.
# returns: True if overlap is detected, False otherwise.
# side_effects: none.
# emitted_logs: none.
# error_behavior: none.
# END_FUNCTION_CONTRACT
def has_overlap(allowed_patterns_1: list[str], allowed_patterns_2: list[str]) -> bool:
    for p1 in allowed_patterns_1:
        for p2 in allowed_patterns_2:
            n1 = normalize_path(p1)
            n2 = normalize_path(p2)
            clean_n1 = n1.split("*")[0].rstrip("/")
            clean_n2 = n2.split("*")[0].rstrip("/")
            if clean_n1.startswith(clean_n2) or clean_n2.startswith(clean_n1):
                return True
    return False


# START_FUNCTION_CONTRACT
# name: evaluate_diff_scope
# purpose: Build a structured scope guard verdict for changed paths.
# inputs:
#   changed_paths: list of modified file paths.
#   allowed_patterns: list of allowed glob patterns.
#   frozen_patterns: list of frozen glob patterns.
#   repo_root: repo root directory (optional).
# returns: dict containing pass/fail verdict and grouped file lists.
# side_effects: none.
# emitted_logs: none.
# error_behavior: none.
# END_FUNCTION_CONTRACT
def evaluate_diff_scope(
    changed_paths: list[str],
    allowed_patterns: list[str],
    frozen_patterns: list[str],
    repo_root: str | Path | None = None,
) -> dict[str, list[str] | str]:
    allowed_changed_files: list[str] = []
    blocked_changed_files: list[str] = []
    frozen_violations: list[str] = []

    for path in changed_paths:
        normalized = normalize_path(path, repo_root)
        allowed = is_path_allowed(path, allowed_patterns, repo_root)
        frozen = is_path_frozen(path, frozen_patterns, repo_root)
        if allowed and not frozen:
            allowed_changed_files.append(normalized)
        if not allowed:
            blocked_changed_files.append(normalized)
        if frozen:
            frozen_violations.append(normalized)

    verdict = "fail" if blocked_changed_files or frozen_violations else "pass"
    return {
        "verdict": verdict,
        "allowed_changed_files": sorted(allowed_changed_files),
        "blocked_changed_files": sorted(blocked_changed_files),
        "frozen_violations": sorted(frozen_violations),
    }


# START_FUNCTION_CONTRACT
# name: should_block_diff
# purpose: Decides if a set of changed paths violates write/frozen policies.
# inputs:
#   changed_paths: list of modified file paths.
#   allowed_patterns: list of allowed glob patterns.
#   frozen_patterns: list of frozen glob patterns.
#   repo_root: repo root directory (optional).
# returns: True if diff should be blocked, False if it is clean.
# side_effects: none.
# emitted_logs: none.
# error_behavior: none.
# END_FUNCTION_CONTRACT
def should_block_diff(
    changed_paths: list[str],
    allowed_patterns: list[str],
    frozen_patterns: list[str],
    repo_root: str | Path | None = None,
) -> bool:
    return evaluate_diff_scope(
        changed_paths,
        allowed_patterns,
        frozen_patterns,
        repo_root,
    )["verdict"] == "fail"

# END_BLOCK: guard_policies
