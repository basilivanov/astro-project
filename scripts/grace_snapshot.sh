#!/usr/bin/env bash
set -euo pipefail

print_usage() {
  cat <<'EOF'
Usage:
  scripts/grace_snapshot.sh export [--tag TAG] [--archive-dir DIR] [--prefix NAME]
  scripts/grace_snapshot.sh rehydrate --archive FILE [--target-dir DIR] [--force]

Commands:
  export      Verify the repo is clean, optionally tag the HEAD commit, and
              emit a tar.gz archive plus manifest under DIR (default: artifacts).
  rehydrate   Expand a previously created archive into TARGET (default:
              ./rehydrated-<archive>). Use --force to replace an existing dir.

Options:
  --tag TAG         Annotated tag to create before exporting. When supplied,
                    the archive name is derived from TAG; otherwise HEAD SHA.
  --archive-dir DIR Destination directory for export artifacts.
  --prefix NAME     Prefix inside the produced archive (default astro-project).
  --archive FILE    Source archive path for rehydrate.
  --target-dir DIR  Destination directory for rehydrate.
  --force           Allow rehydrate to overwrite TARGET when it already exists.
  -h, --help        Show this help text.
EOF
}

require_clean_tree() {
  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "This script must run inside a git work tree." >&2
    exit 1
  fi

  local status
  status=$(git status --porcelain=v1)
  if [[ -n "$status" ]]; then
    echo "Working tree is not clean. Resolve the following entries before exporting:" >&2
    echo "$status" >&2
    exit 1
  fi
}

maybe_realpath() {
  if command -v realpath >/dev/null 2>&1; then
    realpath "$1"
  else
    printf '%s\n' "$1"
  fi
}

if [[ $# -lt 1 ]]; then
  print_usage >&2
  exit 1
fi

command=$1
shift

case "$command" in
  export)
    tag=""
    archive_dir="artifacts"
    prefix="astro-project"

    while [[ $# -gt 0 ]]; do
      case "$1" in
        --tag)
          tag="$2"
          shift 2
          ;;
        --archive-dir)
          archive_dir="$2"
          shift 2
          ;;
        --prefix)
          prefix="$2"
          shift 2
          ;;
        -h|--help)
          print_usage
          exit 0
          ;;
        *)
          echo "Unknown option for export: $1" >&2
          print_usage >&2
          exit 1
          ;;
      esac
    done

    require_clean_tree

    commit=$(git rev-parse --verify HEAD)
    tree=$(git rev-parse "${commit}^{tree}")
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    label="$commit"
    if [[ -n "$tag" ]]; then
      label="$tag"
      if git rev-parse -q --verify "refs/tags/$tag" >/dev/null; then
        echo "Tag '$tag' already exists." >&2
        exit 1
      fi
      git tag -a "$tag" -m "Strict GRACE snapshot for $commit" "$commit"
    fi

    safe_label=$(printf '%s' "$label" | tr '/:' '__')
    mkdir -p "$archive_dir"
    archive_path="$archive_dir/${prefix}-${safe_label}.tar.gz"
    manifest_path="${archive_path%.tar.gz}.manifest"

    git archive --format=tar --prefix="${prefix}-${safe_label}/" "$commit" | gzip >"$archive_path"

    archive_abs=$(maybe_realpath "$archive_path")

    cat >"$manifest_path" <<EOF
commit=$commit
tree=$tree
tag=${tag:-none}
archive=$archive_abs
created_at=$timestamp
EOF

    echo "✔ Snapshot created at $archive_path"
    echo "✔ Manifest written to $manifest_path"
    ;;

  rehydrate)
    archive=""
    target=""
    force=0

    while [[ $# -gt 0 ]]; do
      case "$1" in
        --archive)
          archive="$2"
          shift 2
          ;;
        --target-dir)
          target="$2"
          shift 2
          ;;
        --force)
          force=1
          shift
          ;;
        -h|--help)
          print_usage
          exit 0
          ;;
        *)
          echo "Unknown option for rehydrate: $1" >&2
          print_usage >&2
          exit 1
          ;;
      esac
    done

    if [[ -z "$archive" ]]; then
      echo "--archive path is required for rehydrate." >&2
      exit 1
    fi

    if [[ ! -f "$archive" ]]; then
      echo "Archive '$archive' does not exist." >&2
      exit 1
    fi

    if [[ -z "$target" ]]; then
      base=$(basename "$archive")
      base=${base%.tar.gz}
      target="rehydrated-$base"
    fi

    if [[ -e "$target" ]]; then
      if [[ $force -eq 1 ]]; then
        rm -rf "$target"
      else
        echo "Target '$target' already exists. Use --force to overwrite." >&2
        exit 1
      fi
    fi

    mkdir -p "$target"
    tar -xzf "$archive" -C "$target"
    echo "✔ Archive extracted into $target"
    ;;

  -h|--help)
    print_usage
    ;;

  *)
    echo "Unknown command: $command" >&2
    print_usage >&2
    exit 1
    ;;
esac
