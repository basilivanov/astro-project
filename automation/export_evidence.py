#!/usr/bin/env python3
"""Export evidence files into revisioned bundles under ``test-results/evidence``.

Supports copying recent files from one or more sources, preserving optional
directory structure inside the bundle, and maintaining a root manifest with a
per-revision index for controller packets and nightly automation.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
TASK_LOGS_DIR = ROOT / ".task-logs"
EVIDENCE_DIR = ROOT / "test-results" / "evidence"
DEFAULT_WINDOW_HOURS = 24
DEFAULT_DEST = f"rev-{dt.date.today().isoformat()}"
MANIFEST_NAME = "manifest.json"
REVISION_INDEX_NAME = "manifest.revisions.json"


@dataclass(frozen=True)
class ExportSource:
    path: Path
    mode: str
    flatten: bool
    label: str


@dataclass(frozen=True)
class ExportedFile:
    source: str
    destination: str
    modified_at: str
    size_bytes: int
    label: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Copy fresh evidence files into test-results/evidence")
    parser.add_argument(
        "--hours",
        type=float,
        default=DEFAULT_WINDOW_HOURS,
        help=f"Include files modified within the last N hours (default: {DEFAULT_WINDOW_HOURS})",
    )
    parser.add_argument(
        "--dest",
        default=DEFAULT_DEST,
        help="Destination folder name inside test-results/evidence (default: rev-YYYY-MM-DD)",
    )
    parser.add_argument(
        "--source",
        dest="sources",
        action="append",
        default=[],
        help="Source directory or file to scan; can be passed multiple times (default: .task-logs)",
    )
    parser.add_argument(
        "--copy",
        dest="copy_sources",
        action="append",
        default=[],
        help="Extra file or directory to copy as-is into the revision bundle; can be passed multiple times",
    )
    parser.add_argument(
        "--preserve-tree",
        action="store_true",
        help="Preserve relative source paths inside the revision bundle instead of flattening them",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be copied without writing files",
    )
    return parser.parse_args()


def normalize_path(path: Path) -> str:
    return str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)


def build_sources(args: argparse.Namespace) -> list[ExportSource]:
    configured = args.sources or [str(TASK_LOGS_DIR)]
    sources = [
        ExportSource(path=Path(item).resolve(), mode="fresh", flatten=not args.preserve_tree, label="fresh")
        for item in configured
    ]
    sources.extend(
        ExportSource(path=Path(item).resolve(), mode="copy", flatten=False, label="copy")
        for item in args.copy_sources
    )
    return sources


def iter_source_files(source: ExportSource, window_hours: float) -> list[Path]:
    if not source.path.exists():
        return []
    if source.path.is_file():
        return [source.path]

    candidates: list[Path] = []
    cutoff = dt.datetime.now(dt.UTC) - dt.timedelta(hours=window_hours)
    for path in source.path.rglob("*"):
        if not path.is_file():
            continue
        if source.mode == "fresh":
            modified = dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.UTC)
            if modified < cutoff:
                continue
        candidates.append(path)
    candidates.sort(key=lambda item: item.stat().st_mtime, reverse=True)
    return candidates


def relative_destination(source: ExportSource, file_path: Path) -> Path:
    if source.path.is_file():
        return Path(file_path.name)
    if source.flatten:
        return Path(file_path.relative_to(source.path).as_posix().replace("/", "__"))
    return file_path.relative_to(source.path)


def unique_destination(destination: Path) -> Path:
    if not destination.exists():
        return destination

    stem = destination.stem
    suffix = destination.suffix
    counter = 2
    while True:
        candidate = destination.with_name(f"{stem}-{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def copy_files(sources: Iterable[ExportSource], destination_dir: Path, window_hours: float, dry_run: bool) -> list[ExportedFile]:
    exported: list[ExportedFile] = []
    if not dry_run:
        destination_dir.mkdir(parents=True, exist_ok=True)

    for source in sources:
        for path in iter_source_files(source, window_hours):
            target = unique_destination(destination_dir / relative_destination(source, path))
            modified = dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.UTC).isoformat()
            if not dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
            exported.append(
                ExportedFile(
                    source=normalize_path(path),
                    destination=normalize_path(target),
                    modified_at=modified,
                    size_bytes=path.stat().st_size,
                    label=source.label,
                )
            )
    return exported


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict, dry_run: bool) -> None:
    if dry_run:
        return
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_manifests(destination_dir: Path, sources: list[ExportSource], window_hours: float, exported: list[ExportedFile], dry_run: bool) -> None:
    revision = destination_dir.name
    manifest_payload = {
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "revision": revision,
        "window_hours": window_hours,
        "sources": [
            {
                "path": normalize_path(source.path),
                "mode": source.mode,
                "flatten": source.flatten,
                "label": source.label,
            }
            for source in sources
        ],
        "file_count": len(exported),
        "files": [asdict(item) for item in exported],
    }
    write_json(destination_dir / MANIFEST_NAME, manifest_payload, dry_run)

    revision_entry = {
        "generated_at": manifest_payload["generated_at"],
        "manifest": normalize_path(destination_dir / MANIFEST_NAME),
        "file_count": len(exported),
        "sources": manifest_payload["sources"],
    }
    revisions_path = EVIDENCE_DIR / REVISION_INDEX_NAME
    revisions_payload = load_json(revisions_path) or {"generated_at": revision_entry["generated_at"], "revisions": {}}
    revisions_payload["generated_at"] = revision_entry["generated_at"]
    revisions_payload.setdefault("revisions", {})[revision] = revision_entry
    write_json(revisions_path, revisions_payload, dry_run)


def main() -> int:
    args = parse_args()
    sources = build_sources(args)
    destination_dir = EVIDENCE_DIR / args.dest
    exported = copy_files(sources, destination_dir, args.hours, args.dry_run)
    write_manifests(destination_dir, sources, args.hours, exported, args.dry_run)

    print(f"Destination: {destination_dir}")
    print(f"Sources: {', '.join(normalize_path(source.path) for source in sources)}")
    print(f"Files exported: {len(exported)}")
    for item in exported:
        print(f"- [{item.label}] {item.source} -> {item.destination}")
    if not exported:
        print("No matching evidence files found.")
    if not args.dry_run:
        print(f"Revision manifest: {normalize_path(destination_dir / MANIFEST_NAME)}")
        print(f"Revision index: {normalize_path(EVIDENCE_DIR / REVISION_INDEX_NAME)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
