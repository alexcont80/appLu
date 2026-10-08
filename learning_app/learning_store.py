"""Append-only, local JSONL log for reviewed learning rounds."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
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


def append_round(documents: list[dict[str, Any]], *, include_values: bool, guided_path: list[dict[str, Any]] | None = None, completion_state: str = "COMPLETO", data_dir: Path | None = None) -> Path:
    folder = (data_dir or default_data_dir())
    folder.mkdir(parents=True, exist_ok=True)
    log_path = folder / "learning-log.jsonl"
    record = {
        "schema_version": 1,
        "round_id": str(uuid.uuid4()),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "application": "AppLu local learning workbench",
        "evidence_detail_included": include_values,
        "completion_state": completion_state,
        "guided_path": guided_path or [],
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


def session_path(data_dir: Path | None = None) -> Path:
    return (data_dir or default_data_dir()) / "session-progress.json"


def save_session(documents: list[dict[str, Any]], step_states: dict[str, str], active_type: str, *, step_notes: dict[str, str] | None = None, data_dir: Path | None = None) -> Path:
    """Persist labels and review state, never source document text."""
    target = session_path(data_dir)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "active_type": active_type,
        "step_states": step_states,
        "step_notes": step_notes or {},
        "documents": [
            {
                "path": doc["path"],
                "name": doc["name"],
                "type": doc["type"],
                "variant": doc.get("variant", ""),
                "note": doc.get("note", ""),
                "fields": doc.get("fields", []),
            }
            for doc in documents
        ],
    }
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, target)
    return target


def load_session(*, data_dir: Path | None = None) -> dict[str, Any] | None:
    path = session_path(data_dir)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def clear_session(*, data_dir: Path | None = None) -> None:
    path = session_path(data_dir)
    try:
        path.unlink()
    except FileNotFoundError:
        pass

