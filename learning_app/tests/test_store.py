import json
import tempfile
import unittest
from pathlib import Path

from learning_app.learning_store import append_round, load_session, save_session


class StoreTests(unittest.TestCase):
    def test_append_round_can_omit_values(self):
        with tempfile.TemporaryDirectory() as folder:
            result = append_round([{"document_name": "x.pdf", "expected_fields": []}], include_values=False, data_dir=Path(folder))
            row = json.loads(result.read_text(encoding="utf-8"))
            self.assertFalse(row["evidence_detail_included"])
            self.assertEqual(row["documents"][0]["document_name"], "x.pdf")

    def test_detailed_final_log_preserves_mapping_source_and_path(self):
        with tempfile.TemporaryDirectory() as folder:
            specimen = {
                "document_name": "lettera.txt",
                "document_type": "Lettera di incarico",
                "sample_variant": "Tariffa oraria, docente esterno",
                "expected_fields": [{
                    "expected_field": "Email",
                    "reviewed_value": "docente@example.org",
                    "status": "Presente e chiaro",
                    "source_document": "lettera.txt",
                    "source_location": "blocco 1",
                    "issue_type": "Da tipizzare",
                    "question_to_resolve": "",
                    "evidence": {"context": "Email: docente@example.org", "location": "blocco 1"},
                }],
                "candidates": [{"kind": "Email", "value": "docente@example.org", "location": "blocco 1", "context": "Email: docente@example.org"}],
            }
            guided = [{"document_type": "Lettera di incarico", "collection_status": "Tipologia chiusa", "specimen_count": 1, "specimens": ["lettera.txt"]}]
            path = append_round([specimen], include_values=True, guided_path=guided, data_dir=Path(folder))
            row = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(row["guided_path"][0]["collection_status"], "Tipologia chiusa")
            field = row["documents"][0]["expected_fields"][0]
            self.assertEqual(field["reviewed_value"], "docente@example.org")
            self.assertEqual(field["source_location"], "blocco 1")
            self.assertEqual(row["documents"][0]["candidates"][0]["context"], "Email: docente@example.org")

    def test_intermediate_session_resumes_labels_without_copying_source_text(self):
        with tempfile.TemporaryDirectory() as folder:
            documents = [{
                "path": "C:/docs/lettera.pdf",
                "name": "lettera.pdf",
                "type": "Lettera di incarico",
                "variant": "Esterno, orario",
                "note": "verificare protocollo",
                "fields": [{"name": "Email", "status": "Presente e chiaro", "value": "docente@example.org"}],
                "parsed": object(),
            }]
            save_session(documents, {"Lettera di incarico": "Esemplari raccolti"}, "Lettera di incarico", data_dir=Path(folder))
            restored = load_session(data_dir=Path(folder))
            self.assertEqual(restored["active_type"], "Lettera di incarico")
            self.assertEqual(restored["documents"][0]["fields"][0]["value"], "docente@example.org")
            serialized = json.dumps(restored, ensure_ascii=False)
            self.assertNotIn("parsed", serialized)


if __name__ == "__main__":
    unittest.main()

