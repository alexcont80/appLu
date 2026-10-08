import json
import tempfile
import unittest
from pathlib import Path

from learning_app.extractors import read_document
from learning_app.learning_session import summarize_guided_path, validate_document_type, validate_final_path
from learning_app.learning_store import append_round


class EndToEndTests(unittest.TestCase):
    def test_local_specimen_to_final_traceable_log(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            sample_path = root / "lettera.txt"
            sample_path.write_text("Docente: Lucia Esempio\nEmail: lucia@example.org\nProt. n. 123/2026", encoding="utf-8")
            parsed = read_document(sample_path)
            email = next(candidate for candidate in parsed.candidates if candidate.kind == "Email")
            specimen = {
                "name": sample_path.name,
                "type": "Lettera di incarico",
                "variant": "Esterna, compenso orario",
                "fields": [{
                    "name": "Email docente",
                    "status": "Presente e chiaro",
                    "value": email.value,
                    "source_location": email.location,
                    "issue_type": "Da tipizzare",
                    "question": "",
                }],
            }
            self.assertEqual(validate_document_type([specimen], coverage_confirmed=True), [])
            states = {"Lettera di incarico": "Tipologia chiusa"}
            self.assertEqual(validate_final_path(states), [])
            log_document = {
                "document_name": specimen["name"],
                "document_type": specimen["type"],
                "sample_variant": specimen["variant"],
                "expected_fields": [{
                    "expected_field": "Email docente",
                    "status": "Presente e chiaro",
                    "reviewed_value": email.value,
                    "source_document": specimen["name"],
                    "source_location": email.location,
                    "evidence": email.to_dict(),
                    "issue_type": "Da tipizzare",
                    "question_to_resolve": "",
                }],
                "candidates": [candidate.to_dict() for candidate in parsed.candidates],
            }
            guided = summarize_guided_path(list(states), states, [specimen])
            log_path = append_round([log_document], include_values=True, guided_path=guided, data_dir=root / "logs")
            result = json.loads(log_path.read_text(encoding="utf-8"))
            self.assertEqual(result["guided_path"][0]["specimen_count"], 1)
            self.assertEqual(result["documents"][0]["expected_fields"][0]["evidence"]["location"], "blocco 1")
            self.assertGreaterEqual(len(result["documents"][0]["candidates"]), 2)

    def test_skipped_type_is_written_as_incomplete_and_session_can_continue(self):
        with tempfile.TemporaryDirectory() as folder:
            states = {"Lettera di incarico": "Tipologia chiusa", "Programma Edizione": "Da riprendere"}
            notes = {"Programma Edizione": "Serve un programma reale del corso"}
            guided = summarize_guided_path(list(states), states, [], notes)
            path = append_round([], include_values=True, guided_path=guided, completion_state="DA COMPLETARE", data_dir=Path(folder))
            result = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(result["completion_state"], "DA COMPLETARE")
            self.assertEqual(result["guided_path"][1]["note_to_resume"], notes["Programma Edizione"])


if __name__ == "__main__":
    unittest.main()
