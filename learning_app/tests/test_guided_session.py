import unittest

from learning_app.learning_session import add_shared_field, field_names_for_type, summarize_guided_path, validate_document_type, validate_final_path


class GuidedSessionTests(unittest.TestCase):
    def setUp(self):
        self.specimen = {
            "name": "lettera-01.txt",
            "type": "Lettera di incarico",
            "variant": "Docente esterno, tariffa oraria",
            "fields": [{"name": "Email", "status": "Presente e chiaro", "value": "docente@example.org", "source_location": "pagina 1"}],
        }

    def test_unresolved_field_blocks_next_document_even_when_question_is_written(self):
        self.specimen["fields"][0].update({"status": "Presente ma ambiguo", "issue_type": "Significato del campo", "question": "È l’email del docente?"})
        blockers = validate_document_type([self.specimen], coverage_confirmed=True)
        self.assertTrue(any("non confermato" in item for item in blockers))

    def test_clear_all_fields_and_coverage_allows_next_step(self):
        self.assertEqual(validate_document_type([self.specimen], coverage_confirmed=True), [])

    def test_missing_specimen_keeps_type_blocked(self):
        self.assertTrue(validate_document_type([], coverage_confirmed=True))

    def test_final_path_allows_skipping_with_a_note_and_logs_pending_fields(self):
        states = {"Lettera di incarico": "Tipologia chiusa", "Programma Edizione": "Da riprendere"}
        notes = {"Programma Edizione": "Manca il programma in PDF"}
        self.assertEqual(validate_final_path(states, notes), [])
        self.assertEqual(validate_final_path(states), ["Programma Edizione"])
        pending_sample = {**self.specimen, "type": "Programma Edizione", "fields": [{"name": "Orario", "status": "Presente ma ambiguo", "question": "Quale orario è quello del docente?", "issue_type": "Associazione a docente o corso"}]}
        summary = summarize_guided_path(list(states), states, [self.specimen, pending_sample], notes)
        self.assertEqual(summary[0]["specimen_count"], 1)
        self.assertEqual(summary[1]["specimen_count"], 1)
        self.assertEqual(summary[1]["note_to_resume"], "Manca il programma in PDF")
        summary = summarize_guided_path(list(states), states, [pending_sample], notes)
        self.assertEqual(summary[1]["outstanding_fields"][0]["question"], "Quale orario è quello del docente?")

    def test_new_variable_is_added_to_every_sample_and_blocks_until_reviewed(self):
        second = {
            "name": "lettera-02.txt",
            "type": "Lettera di incarico",
            "variant": "Docente interno, fuori orario",
            "fields": [{"name": "Email", "status": "Presente e chiaro", "value": "interno@example.org"}],
        }
        specimens = [self.specimen, second]
        self.assertEqual(add_shared_field(specimens, "Protocollo"), 2)
        self.assertEqual([len(sample["fields"]) for sample in specimens], [2, 2])
        self.assertEqual(field_names_for_type(["Email"], specimens), ["Email", "Protocollo"])
        self.assertTrue(validate_document_type(specimens, coverage_confirmed=True))

    def test_different_field_lists_block_type_closure(self):
        second = {**self.specimen, "name": "lettera-02.txt", "fields": self.specimen["fields"] + [{"name": "Protocollo", "status": "Presente e chiaro", "value": "1/2"}]}
        blockers = validate_document_type([self.specimen, second], coverage_confirmed=True)
        self.assertTrue(any("Allineare l’elenco" in blocker for blocker in blockers))


if __name__ == "__main__":
    unittest.main()
