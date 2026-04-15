#!/usr/bin/env python3
"""
build_index.py — Scans docs/architecture-maps/*.html, extracts arch-map meta
tags, and regenerates index.html using assets/index-template.html.

Usage:
    python3 scripts/build_index.py <maps-dir>

    <maps-dir>  Path to docs/architecture-maps/ in the target project.

The script is designed to be called from SKILL.md Step 9. It expects
assets/index-template.html to live alongside this script's parent directory
(i.e., skill_root/assets/index-template.html).

Exit codes:
    0  success (index.html written)
    1  usage / file-not-found error
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Locate template ───────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent.resolve()
SKILL_ROOT = SCRIPT_DIR.parent
TEMPLATE_PATH = SKILL_ROOT / "assets" / "index-template.html"


def die(msg: str) -> None:
    print(f"[build_index] ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


# ── Parse a single HTML file ──────────────────────────────────────────────────

META_RE = re.compile(
    r'<meta\s+name="arch-map-([^"]+)"\s+content="([^"]*)"',
    re.IGNORECASE,
)


def extract_meta(html: str) -> dict | None:
    """Return a dict of arch-map-* meta values, or None if the file has none."""
    found = {}
    for m in META_RE.finditer(html):
        found[m.group(1)] = m.group(2)

    required = {"component", "entry-file", "generated-at", "group"}
    if not required.issubset(found.keys()):
        return None

    return {
        "component":   found["component"],
        "entryFile":   found["entry-file"],
        "generatedAt": found["generated-at"],
        "group":       found["group"],
        "issues":      found.get("issues", ""),
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) < 2:
        die(f"Usage: python3 {Path(__file__).name} <maps-dir>")

    maps_dir = Path(sys.argv[1]).resolve()
    if not maps_dir.is_dir():
        die(f"Maps directory not found: {maps_dir}")

    if not TEMPLATE_PATH.is_file():
        die(f"index-template.html not found at: {TEMPLATE_PATH}")

    # ── Scan HTML files ───────────────────────────────────────────────────────
    entries: list[dict] = []
    legacy: list[dict] = []
    skipped: list[str] = []

    html_files = sorted(
        f for f in maps_dir.glob("*.html") if f.name != "index.html"
    )

    for path in html_files:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            skipped.append(f"{path.name}: {e}")
            continue

        meta = extract_meta(content)
        if meta is None:
            legacy.append({"file": path.name})
            continue

        meta["file"] = path.name
        entries.append(meta)

    if skipped:
        print(f"[build_index] Skipped (unreadable): {', '.join(skipped)}", file=sys.stderr)

    # ── Build payload ─────────────────────────────────────────────────────────
    now_iso = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    payload = {
        "entries":     entries,
        "legacy":      legacy,
        "generatedAt": now_iso,
    }

    # ── Inject into template ──────────────────────────────────────────────────
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    json_blob = json.dumps(payload, ensure_ascii=False, indent=None)
    output_html = template.replace("__ARCH_MAP_ENTRIES__", json_blob, 1)

    out_path = maps_dir / "index.html"
    out_path.write_text(output_html, encoding="utf-8")

    n_e = len(entries)
    n_l = len(legacy)
    print(
        f"[build_index] index.html written — "
        f"{n_e} map{'s' if n_e != 1 else ''} indexed"
        + (f", {n_l} legacy file{'s' if n_l != 1 else ''} listed" if n_l else "")
    )


if __name__ == "__main__":
    main()
