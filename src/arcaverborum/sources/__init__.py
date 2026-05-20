"""Source acquisition: fetch raw data into raw/<source>/.

Each source module exposes a `fetch(raw_root, **kwargs) -> None`
function. `dispatch_fetch(name, raw_root)` is the public entry point.
"""

from __future__ import annotations

from pathlib import Path


def dispatch_fetch(source: str, raw_root: Path, **kwargs) -> None:
    if source == "lexibank":
        from arcaverborum.sources import lexibank
        lexibank.fetch(raw_root, **kwargs)
    elif source == "gled":
        from arcaverborum.sources import gled
        gled.fetch(raw_root, **kwargs)
    elif source == "wiktionary":
        from arcaverborum.sources import wiktionary
        wiktionary.fetch(raw_root, **kwargs)
    elif source == "glottolog":
        from arcaverborum.sources import glottolog as gl
        gl.fetch(raw_root, **kwargs)
    elif source == "concepticon":
        from arcaverborum.sources import concepticon as cc
        cc.fetch(raw_root, **kwargs)
    else:
        raise ValueError(f"Unknown source: {source}")
