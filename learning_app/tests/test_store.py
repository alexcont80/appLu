import json
import tempfile
import unittest
from pathlib import Path

from learning_app.learning_store import append_round


class StoreTests(unittest.TestCase):
    def test_append_round_records_detail_setting(self):
        with tempfile.TemporaryDirectory() as folder:
            result = append_round([{"document_name": "x.pdf", "expected_fields": []}], include_values=False, data_dir=Path(folder))
            row = json.loads(result.read_text(encoding="utf-8"))
            self.assertFalse(row["evidence_detail_included"])
            self.assertEqual(row["documents"][0]["document_name"], "x.pdf")


if __name__ == "__main__":
    unittest.main()

