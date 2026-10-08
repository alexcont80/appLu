import unittest

from learning_app.learning_session import summarize_guided_path, validate_document_type, validate_final_path


class GuidedSessionTests(unittest.TestCase):
    def setUp(self):
        self.specimen = {
            "name": "lettera-01.txt",
            "type": "Lettera di incarico",
            "variant": "Docente esterno, tariffa oraria",
            "fields": [{"name": "Email", "status": "Presente e chiaro", "value": "docente@example.org"}],
        }

    def test_unresolved_field_blocks_next_document_even_when_question_is_written(self):
        self.specimen["fields"][0].update({"status": "Presente ma ambiguo", "issue_type": "Significato del campo", "question": "È l’email del docente?"})
        blockers = validate_document_type([self.specimen], coverage_confirmed=True)
        self.assertTrue(any("non confermato" in item for item in blockers))

    def test_clear_all_fields_and_coverage_allows_next_step(self):
        self.assertEqual(validate_document_type([self.specimen], coverage_confirmed=True), [])

    def test_missing_specimen_keeps_type_blocked(self):
        self.assertTrue(validate_document_type([], coverage_confirmed=True))

    def test_final_path_requires_every_type_closed_and_logs_specimens(self):
        states = {"Lettera di incarico": "Tipologia chiusa", "Programma Edizione": "In attesa del documento"}
        self.assertEqual(validate_final_path(states), ["Programma Edizione"])
        summary = summarize_guided_path(list(states), states, [self.specimen])
        self.assertEqual(summary[0]["specimen_count"], 1)
        self.assertEqual(summary[1]["specimen_count"], 0)


if __name__ == "__main__":
    unittest.main()
