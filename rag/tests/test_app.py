import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch, Mock
import json

spec = importlib.util.spec_from_file_location("rag_app", Path(__file__).resolve().parents[1] / "app.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

class DemoTests(unittest.TestCase):
    def test_grounded_response_format(self):
        runtime = Mock()
        for payload in ({"id": "TRANSFER_POLICY"},
                        {"answer": "Claim", "citations": ["INVENTED"]},
                        {"answer": "", "citations": []}):
            runtime.converse.return_value = {"output": {"message": {"content": [{"text": json.dumps(payload)}]}}}
            with self.assertRaises(ValueError):
                app.core.generate(runtime, "model", "question", app.core.DOCUMENTS)
        runtime.converse.return_value = {"output": {"message": {"content": [{"text": json.dumps({"answer": "37 hours", "citations": ["TRANSFER_POLICY"]})}]}}}
        self.assertEqual(app.core.generate(runtime, "model", "question", app.core.DOCUMENTS), "37 hours [TRANSFER_POLICY]")

    def test_bounded_question_rejected_before_services(self):
        with patch.object(app.core.boto3, "Session") as session:
            with self.assertRaises(ValueError):
                app.ask("drop all tables")
            session.assert_not_called()

    def test_fixture_and_questions(self):
        self.assertEqual(len(app.QUESTIONS), 4)
        self.assertEqual(len(app.core.DOCUMENTS), 3)
        self.assertTrue(all("Synthetic" in x["text"] for x in app.core.DOCUMENTS))
        self.assertNotIn("Aspen", str(app.core.DOCUMENTS))

    def test_sql_is_bound_and_read_only(self):
        sql = app.core.RETRIEVAL_SQL.upper()
        self.assertIn(":DOCUMENTS", sql)
        self.assertIn(":QUERY_VECTOR", sql)
        self.assertIn("VECTOR_DISTANCE", sql)
        self.assertIn("FETCH FIRST 2 ROWS ONLY", sql)
        self.assertFalse(any(word in sql for word in ["DELETE ", "UPDATE ", "INSERT ", "CREATE "]))

    def test_answer_assertion(self):
        app.core.verify_answer("37 hours [TRANSFER_POLICY]")
        with self.assertRaises(ValueError):
            app.core.verify_answer("48 hours [WARRANTY_POLICY]")

if __name__ == "__main__":
    unittest.main()
