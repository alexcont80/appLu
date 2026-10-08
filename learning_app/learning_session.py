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
    schema_sets = [tuple(field.get("name", "") for field in sample.get("fields", [])) for sample in specimens]
    if schema_sets and any(schema != schema_sets[0] for schema in schema_sets[1:]):
        blockers.append("Allineare l’elenco dei campi su tutti gli esemplari di questa tipologia.")
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
            elif status == "Presente e chiaro" and not field.get("source_location", "").strip():
                blockers.append(f"{sample_name} · {name}: indicare pagina o posizione della fonte.")
            elif status == "Assente in questa variante · confermato" and not field.get("question", "").strip():
                blockers.append(f"{sample_name} · {name}: spiegare perché è confermato assente in questa variante.")
    return blockers


def add_shared_field(specimens: list[dict[str, Any]], name: str) -> int:
    """Add the same new expected variable to every specimen of one type."""
    if not name.strip():
        raise ValueError("Il nome del campo non può essere vuoto.")
    added_to = 0
    for sample in specimens:
        fields = sample.setdefault("fields", [])
        if any(field.get("name", "").casefold() == name.strip().casefold() for field in fields):
            continue
        fields.append({"name": name.strip(), "status": "Da verificare", "value": "", "source_location": "", "issue_type": "Da tipizzare", "question": "", "evidence": None})
        added_to += 1
    return added_to


def field_names_for_type(preset_fields: list[str], specimens: list[dict[str, Any]]) -> list[str]:
    """Union preset and previously discovered fields, preserving their order."""
    names = list(preset_fields)
    seen = {name.casefold() for name in names}
    for sample in specimens:
        for field in sample.get("fields", []):
            name = field.get("name", "").strip()
            if name and name.casefold() not in seen:
                names.append(name)
                seen.add(name.casefold())
    return names


def validate_final_path(step_states: dict[str, str], step_notes: dict[str, str] | None = None) -> list[str]:
    notes = step_notes or {}
    pending = [name for name, state in step_states.items() if state not in {"Tipologia chiusa", "Da riprendere"}]
    pending.extend(name for name, state in step_states.items() if state == "Da riprendere" and not notes.get(name, "").strip())
    return pending


def summarize_guided_path(step_names: list[str], step_states: dict[str, str], specimens: list[dict[str, Any]], step_notes: dict[str, str] | None = None) -> list[dict[str, Any]]:
    notes = step_notes or {}
    return [
        {
            "document_type": name,
            "collection_status": step_states.get(name, "Da raccogliere"),
            "note_to_resume": notes.get(name, ""),
            "specimen_count": sum(sample.get("type") == name for sample in specimens),
            "specimens": [sample.get("name", "") for sample in specimens if sample.get("type") == name],
            "outstanding_fields": [
                {"specimen": sample.get("name", ""), "field": field.get("name", ""), "status": field.get("status", "Da verificare"), "question": field.get("question", ""), "issue_type": field.get("issue_type", "Da tipizzare")}
                for sample in specimens if sample.get("type") == name
                for field in sample.get("fields", []) if field.get("status") not in UNDERSTOOD_STATUSES
            ],
        }
        for name in step_names
    ]

