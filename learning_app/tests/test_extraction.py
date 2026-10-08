import tempfile
import unittest
from pathlib import Path

from learning_app.extractors import find_candidates, read_document


class ExtractionTests(unittest.TestCase):
    def test_literal_candidates_have_provenance(self):
        text = "Prot. n. 123/2026 Docente: a.b@example.org compenso € 120,50 il 15/10/2026 dalle 09:00–10:30"
        results = find_candidates(text, [(text, "pagina 2")])
        pairs = {(item.kind, item.value) for item in results}
        self.assertIn(("Email", "a.b@example.org"), pairs)
        self.assertIn(("Protocollo", "Prot. n. 123/2026"), pairs)
        self.assertIn(("Importo", "€ 120,50"), pairs)
        self.assertTrue(all(item.location == "pagina 2" for item in results))

    def test_text_file_read_stays_explicit(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "lettera.txt"
            path.write_text("Contatto: demo@example.test", encoding="utf-8")
            parsed = read_document(path)
            self.assertEqual(parsed.pages, 1)
            self.assertEqual(parsed.candidates[0].kind, "Email")


if __name__ == "__main__":
    unittest.main()

