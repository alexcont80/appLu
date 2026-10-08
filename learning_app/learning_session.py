"""Pure validation helpers for the strictly sequential learning path."""

from __future__ import annotations

from typing import Any

UNDERSTOOD_STATUSES = {
    "Presente e chiaro",
    "Assente in questa variante · confermato",
    "Non previsto · confermato",
}


def validate_document_type(specimens: list[dict[str, Any]], *, coverage_confirmed: bool) -> list[str]:
    """Return blockers; an empty list means this type can be closed."""
    blockers: list[str] = []
    if not specimens:
        return ["Caricare almeno un esemplare di questa tipologia."]
    if not any(sample.get("fields") for sample in specimens):
        blockers.append("Aggiungere almeno un campo atteso.")
    if not coverage_confirmed:
        blockers.append("Confermare di aver confrontato gli esemplari e mappato tutte le variabili.")
    for sample in specimens:
        sample_name = sample.get("name", "esemplare")
        if not sample.get("variant", "").strip():
            blockers.append(f"{sample_name}: descrivere la variante/caso rappresentato.")
        for field in sample.get("fields", []):
            status = field.get("status", "Da verificare")
            name = field.get("name", "Campo senza nome")
            if status not in UNDERSTOOD_STATUSES:
                blockers.append(f"{sample_name} · {name}: stato ancora non confermato ({status}).")
            elif status == "Presente e chiaro" and not field.get("value", "").strip():
                blockers.append(f"{sample_name} · {name}: inserire il valore revisionato o la descrizione verificata.")
            elif status == "Assente in questa variante · confermato" and not field.get("question", "").strip():
                blockers.append(f"{sample_name} · {name}: spiegare perché è confermato assente in questa variante.")
    return blockers


def validate_final_path(step_states: dict[str, str]) -> list[str]:
    return [name for name, state in step_states.items() if state != "Tipologia chiusa"]


def summarize_guided_path(step_names: list[str], step_states: dict[str, str], specimens: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "document_type": name,
            "collection_status": step_states.get(name, "Da raccogliere"),
            "specimen_count": sum(sample.get("type") == name for sample in specimens),
            "specimens": [sample.get("name", "") for sample in specimens if sample.get("type") == name],
        }
        for name in step_names
    ]

