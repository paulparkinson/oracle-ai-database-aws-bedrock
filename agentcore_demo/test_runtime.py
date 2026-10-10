import time
import unittest
from unittest.mock import patch
from agentcore_demo import runtime as r

class RuntimeTests(unittest.TestCase):
    def setUp(self):
        r._owners.clear()
        r.nl2sql.PENDING.clear()
        self.session = "a" * 36

    def test_unknown_and_extra_fields(self):
        for body in [{"operation": "delete"}, {"operation": "rag", "question": "q", "sql": "x"}]:
            with self.assertRaises(ValueError):
                r.dispatch(body, self.session)

    def test_missing_session(self):
        with self.assertRaises(ValueError):
            r.dispatch({"operation": "rag", "question": "q"}, None)

    def test_cross_session_does_not_execute_or_load_secret(self):
        r.nl2sql.PENDING["receipt"] = {"expires": time.monotonic()+100}
        r._owners["receipt"] = self.session
        with patch.object(r, "configure_database") as cfg, patch.object(r.nl2sql, "execute") as execute:
            with self.assertRaises(ValueError):
                r.dispatch({"operation": "nl2sql.execute", "receipt": "receipt"}, "b"*36)
            cfg.assert_not_called()
            execute.assert_not_called()

    def test_generate_binds_receipt_to_session(self):
        with patch.object(r.nl2sql, "generate", return_value={"receipt": "r"}) as gen:
            self.assertEqual(r.dispatch({"operation": "nl2sql.generate", "question": "risk 70"}, self.session), {"receipt":"r"})
            self.assertEqual(r._owners["r"], self.session)

    def test_execute_once(self):
        r.nl2sql.PENDING["r"] = {"expires": time.monotonic()+100}
        r._owners["r"] = self.session
        with patch.object(r, "configure_database"), patch.object(r.nl2sql, "execute", return_value={"rows":[]}) as execute:
            r.dispatch({"operation": "nl2sql.execute", "receipt": "r"}, self.session)
            with self.assertRaises(ValueError):
                r.dispatch({"operation": "nl2sql.execute", "receipt": "r"}, self.session)
            execute.assert_called_once()

    def test_errors_are_sanitized(self):
        from types import SimpleNamespace
        with patch.object(r, "dispatch", side_effect=RuntimeError("PRIVATE_SECRET")):
            result = r.invoke({}, SimpleNamespace(session_id=self.session))
            self.assertNotIn("PRIVATE_SECRET", str(result))

if __name__ == "__main__":
    unittest.main()

