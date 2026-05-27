#!/usr/bin/env bash
set -euo pipefail

SOLARSAGE_DIR="${SOLARSAGE_DIR:-/opt/solarsage}"
SWISSEPH_SRC_DIR="${SWISSEPH_SRC_DIR:-/tmp/swisseph-solarsage}"

if [[ ! -d "$SOLARSAGE_DIR/.git" ]]; then
  echo "SolarSage repo not found at $SOLARSAGE_DIR" >&2
  exit 1
fi

if [[ ! -d "$SWISSEPH_SRC_DIR/.git" ]]; then
  rm -rf "$SWISSEPH_SRC_DIR"
  git clone https://github.com/aloistr/swisseph.git "$SWISSEPH_SRC_DIR"
else
  git -C "$SWISSEPH_SRC_DIR" fetch origin
  git -C "$SWISSEPH_SRC_DIR" reset --hard origin/master
fi

make -C "$SWISSEPH_SRC_DIR" clean >/dev/null 2>&1 || true
make -C "$SWISSEPH_SRC_DIR" libswe.a CFLAGS='-g -Wall -fPIC -DTLSOFF'

mkdir -p "$SOLARSAGE_DIR/third_party/swisseph/ephe"

cp "$SWISSEPH_SRC_DIR"/*.c "$SOLARSAGE_DIR/third_party/swisseph/"
cp "$SWISSEPH_SRC_DIR"/*.h "$SOLARSAGE_DIR/third_party/swisseph/"
cp "$SWISSEPH_SRC_DIR"/libswe.a "$SOLARSAGE_DIR/third_party/swisseph/"
find "$SWISSEPH_SRC_DIR/ephe" -maxdepth 1 -type f -exec cp {} "$SOLARSAGE_DIR/third_party/swisseph/ephe/" \;

echo "SolarSage Swiss Ephemeris synced:"
echo "  repo: $SOLARSAGE_DIR"
echo "  source: $SWISSEPH_SRC_DIR"
echo "  files: $(find "$SOLARSAGE_DIR/third_party/swisseph/ephe" -maxdepth 1 -type f | wc -l)"
