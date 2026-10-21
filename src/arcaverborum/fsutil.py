"""Atomic file replacement for build outputs."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def atomic_path(path: Path) -> Iterator[Path]:
    """Yield a temporary path next to *path*; on success rename it over *path*.

    Readers, and a build interrupted half-way, see either the old file or
    the new one, never a truncated one. On an exception the temporary
    file is removed and *path* is left as it was.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    os.close(fd)
    tmp = Path(name)
    try:
        umask = os.umask(0)
        os.umask(umask)
        os.chmod(tmp, 0o666 & ~umask)  # mkstemp creates 0600
        yield tmp
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def write_text_atomic(path: Path, text: str) -> None:
    with atomic_path(path) as tmp:
        tmp.write_text(text, encoding="utf-8")
