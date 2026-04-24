#!/usr/bin/env python3
"""Strict backend Python size guard for GRACE refactor packets."""

from __future__ import annotations

# START_MODULE_CONTRACT
# module: scripts.check_size_limits
# feature_ref: FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424
# responsibility: Enforce backend/app physical line and function token limits.
# inputs: Python source tree path, strict mode, transitional known-oversized paths.
# outputs: Human-readable violation report and process exit status.
# invariants:
#   - Scans only configured roots, never implicit whole-repository dependency checks.
#   - Excludes generated, cache, virtualenv, build, and migration snapshot artifacts.
#   - Reports AST function spans and exact tokenize counts when source parses.
# END_MODULE_CONTRACT

# MODULE_MAP
# - CLI parsing: parse_args, main
# - Source discovery: iter_python_files, should_exclude_path, normalize_relative_path
# - File checks: count_physical_lines, check_file, check_root
# - Function checks: collect_function_metrics, count_python_tokens
# - Reporting: format_violation, print_report
# END_MODULE_MAP

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
import sys
import tokenize
from io import BytesIO
from typing import Iterable, Sequence

MAX_FILE_LINES = 1000
MAX_FUNCTION_TOKENS = 4000

EXCLUDED_DIR_NAMES = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "cache",
        "dist",
        "generated",
        "htmlcov",
        "node_modules",
        "test-results",
        "venv",
    }
)

EXCLUDED_FILE_SUFFIXES = (
    "_pb2.py",
    "_pb2_grpc.py",
    ".generated.py",
    ".gen.py",
)

EXCLUDED_FILE_NAMES = frozenset(
    {
        "alembic_version.py",
    }
)

EXCLUDED_PATH_PARTS = frozenset(
    {
        "migrations",
        "migration_snapshots",
    }
)


@dataclass(frozen=True)
class FunctionMetric:
    name: str
    qualname: str
    start_line: int
    end_line: int
    span_lines: int
    token_count: int | None


@dataclass(frozen=True)
class Violation:
    path: Path
    kind: str
    message: str
    allowed: bool = False


# START_BLOCK: path-normalization
# Contract: Compare paths consistently across container, host, and relative CLI inputs.
def normalize_relative_path(path: Path, base: Path) -> str:
    """Return a stable POSIX relative path for reports and allow-list matching."""
    try:
        relative_path = path.resolve().relative_to(base.resolve())
    except ValueError:
        relative_path = path.resolve()
    return relative_path.as_posix()


# END_BLOCK: path-normalization


# START_BLOCK: exclusion-policy
# Contract: Keep scans backend-scoped and avoid generated/cache artifacts by policy.
def should_exclude_path(path: Path) -> bool:
    """Return whether a Python path is outside the meaningful source-size contract."""
    if path.name in EXCLUDED_FILE_NAMES:
        return True
    if path.name.endswith(EXCLUDED_FILE_SUFFIXES):
        return True
    parts = set(path.parts)
    if parts & EXCLUDED_PATH_PARTS:
        return True
    return any(part in EXCLUDED_DIR_NAMES for part in path.parts)


# END_BLOCK: exclusion-policy


# START_BLOCK: source-discovery
# Contract: Walk only the requested root and yield sorted non-excluded Python files.
def iter_python_files(root: Path) -> Iterable[Path]:
    """Yield Python files under root, excluding generated/cache/venv artifacts."""
    if root.is_file():
        if root.suffix == ".py" and not should_exclude_path(root):
            yield root
        return

    for path in sorted(root.rglob("*.py")):
        if not should_exclude_path(path):
            yield path


# END_BLOCK: source-discovery


# START_BLOCK: line-count
# Contract: Count physical lines without interpreting source semantics.
def count_physical_lines(path: Path) -> int:
    """Count physical lines in a source file using newline boundaries."""
    with path.open("rb") as source_file:
        return sum(1 for _ in source_file)


# END_BLOCK: line-count


# START_BLOCK: token-count
# Contract: Use Python's tokenizer for exact lexical token counts where possible.
def count_python_tokens(source: str) -> int | None:
    """Return an exact tokenize count, or None when tokenization fails."""
    try:
        tokens = tokenize.tokenize(BytesIO(source.encode("utf-8")).readline)
        return sum(
            1
            for token in tokens
            if token.type
            not in {
                tokenize.ENCODING,
                tokenize.ENDMARKER,
                tokenize.NL,
                tokenize.NEWLINE,
                tokenize.INDENT,
                tokenize.DEDENT,
            }
        )
    except tokenize.TokenError:
        return None


# END_BLOCK: token-count


# START_BLOCK: ast-function-metrics
# Contract: Report AST spans and exact token counts for function bodies.
def collect_function_metrics(path: Path) -> list[FunctionMetric]:
    """Collect function span and token metrics from a Python source file."""
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    source_lines = source.splitlines()
    metrics: list[FunctionMetric] = []
    parents: list[str] = []

    def visit(node: ast.AST) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start_line = node.lineno
            end_line = getattr(node, "end_lineno", node.lineno)
            function_source = "\n".join(source_lines[start_line - 1 : end_line])
            qualname = ".".join([*parents, node.name]) if parents else node.name
            metrics.append(
                FunctionMetric(
                    name=node.name,
                    qualname=qualname,
                    start_line=start_line,
                    end_line=end_line,
                    span_lines=end_line - start_line + 1,
                    token_count=count_python_tokens(function_source),
                )
            )
            parents.append(node.name)
            for child in ast.iter_child_nodes(node):
                visit(child)
            parents.pop()
            return

        if isinstance(node, ast.ClassDef):
            parents.append(node.name)
            for child in ast.iter_child_nodes(node):
                visit(child)
            parents.pop()
            return

        for child in ast.iter_child_nodes(node):
            visit(child)

    visit(tree)
    return metrics


# END_BLOCK: ast-function-metrics


# START_BLOCK: file-check
# Contract: Produce violations without printing, making tests and CLI share semantics.
def check_file(
    path: Path,
    *,
    base: Path,
    allow_known_oversized: set[str],
    max_file_lines: int = MAX_FILE_LINES,
    max_function_tokens: int = MAX_FUNCTION_TOKENS,
) -> list[Violation]:
    """Check a single Python file for file and function size violations."""
    report_path = normalize_relative_path(path, base)
    is_allowed = report_path in allow_known_oversized or path.as_posix() in allow_known_oversized
    violations: list[Violation] = []

    physical_lines = count_physical_lines(path)
    if physical_lines > max_file_lines:
        violations.append(
            Violation(
                path=path,
                kind="file-lines",
                message=(
                    f"{report_path}: {physical_lines} physical lines "
                    f"(limit: {max_file_lines})"
                ),
                allowed=is_allowed,
            )
        )

    try:
        function_metrics = collect_function_metrics(path)
    except SyntaxError as exc:
        violations.append(
            Violation(
                path=path,
                kind="parse-error",
                message=f"{report_path}: unable to parse AST for function metrics: {exc}",
                allowed=is_allowed,
            )
        )
        return violations

    for metric in function_metrics:
        if metric.token_count is not None and metric.token_count <= max_function_tokens:
            continue
        token_text = "unavailable" if metric.token_count is None else str(metric.token_count)
        violations.append(
            Violation(
                path=path,
                kind="function-tokens",
                message=(
                    f"{report_path}:{metric.start_line}: function {metric.qualname} spans "
                    f"{metric.span_lines} AST lines and {token_text} tokens "
                    f"(limit: {max_function_tokens})"
                ),
                allowed=is_allowed,
            )
        )

    return violations


# END_BLOCK: file-check


# START_BLOCK: root-check
# Contract: Aggregate requested-root results and keep allow-list matching explicit.
def check_root(
    root: Path,
    *,
    allow_known_oversized: Sequence[str] = (),
    max_file_lines: int = MAX_FILE_LINES,
    max_function_tokens: int = MAX_FUNCTION_TOKENS,
) -> list[Violation]:
    """Check all non-excluded Python files under a configured root."""
    base = Path.cwd()
    allowed_paths = {
        allowed_path
        for item in allow_known_oversized
        for allowed_path in (Path(item).as_posix(), Path(item).resolve().as_posix())
    }
    violations: list[Violation] = []
    for path in iter_python_files(root):
        violations.extend(
            check_file(
                path,
                base=base,
                allow_known_oversized=allowed_paths,
                max_file_lines=max_file_lines,
                max_function_tokens=max_function_tokens,
            )
        )
    return violations


# END_BLOCK: root-check


# START_BLOCK: report-formatting
# Contract: Make strict failures and transitional allowed findings obvious to reviewers.
def format_violation(violation: Violation) -> str:
    """Format one size finding for CLI output."""
    prefix = "ALLOWED" if violation.allowed else "VIOLATION"
    return f"{prefix} [{violation.kind}] {violation.message}"


def print_report(violations: Sequence[Violation]) -> None:
    """Print a deterministic size-check report."""
    if not violations:
        print("size-check: PASS no violations")
        return
    for violation in violations:
        print(format_violation(violation))
    blocking_count = sum(1 for violation in violations if not violation.allowed)
    allowed_count = len(violations) - blocking_count
    print(
        "size-check: "
        f"{blocking_count} blocking violation(s), {allowed_count} allowed known oversized finding(s)"
    )


# END_BLOCK: report-formatting


# START_BLOCK: cli
# Contract: Strict mode returns non-zero on blocking violations; audit mode reports only.
def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse size-check CLI arguments."""
    default_root = "backend/app" if Path("backend/app").exists() else "."
    parser = argparse.ArgumentParser(description="Check backend Python file and function size limits.")
    parser.add_argument("--root", default=default_root, help="Python source root or file to scan.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on blocking violations.")
    parser.add_argument(
        "--allow-known-oversized",
        nargs="*",
        default=(),
        help="Transitional W01 allow-list paths for known oversized files.",
    )
    parser.add_argument("--max-file-lines", type=int, default=MAX_FILE_LINES)
    parser.add_argument("--max-function-tokens", type=int, default=MAX_FUNCTION_TOKENS)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the size guard CLI."""
    args = parse_args(argv)
    root = Path(args.root)
    violations = check_root(
        root,
        allow_known_oversized=args.allow_known_oversized,
        max_file_lines=args.max_file_lines,
        max_function_tokens=args.max_function_tokens,
    )
    print_report(violations)
    if args.strict and any(not violation.allowed for violation in violations):
        return 1
    return 0


# END_BLOCK: cli


if __name__ == "__main__":
    sys.exit(main())
