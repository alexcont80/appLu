"""Append-only, local JSONL log for reviewed learning rounds."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
import uuid


def default_data_dir() -> Path:
    """Use the current user's writable profile; never requires elevation."""
    import os
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return root / "AppLu" / "Apprendimento"


def append_round(documents: list[dict[str, Any]], *, include_values: bool, data_dir: Path | None = None) -> Path:
    folder = (data_dir or default_data_dir())
    folder.mkdir(parents=True, exist_ok=True)
    log_path = folder / "learning-log.jsonl"
    record = {
        "schema_version": 1,
        "round_id": str(uuid.uuid4()),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "application": "AppLu local learning workbench",
        "evidence_detail_included": include_values,
        "documents": documents,
    }
    with log_path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    return log_path


def read_rounds(log_path: Path) -> list[dict[str, Any]]:
    if not log_path.exists():
        return []
    result = []
    with log_path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                result.append(json.loads(line))
    return result

