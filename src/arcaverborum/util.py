from __future__ import annotations

import json
import sys
from pathlib import Path


def format_bytes(size: int) -> str:
    size_float = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if size_float < 1024.0:
            return f"{size_float:.0f} {unit}"
        size_float /= 1024.0
    return f"{size_float:.1f} TB"


def format_number(n: int) -> str:
    return f"{n:,}"


def load_state(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def save_state(state: dict, path: Path) -> None:
    path.write_text(
        json.dumps(state, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8",
    )


def die(msg: str, code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)
