"""Shared JSON file I/O helpers."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def write_json_atomic(path: Path, data: Any, *, indent: int | None = 2) -> None:
    """Write JSON to *path* using fsync plus atomic replacement."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=path.name + ".",
        suffix=".tmp",
    )

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=indent, ensure_ascii=False)
            file.flush()
            os.fsync(file.fileno())
        Path(tmp_path).replace(path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
        raise
