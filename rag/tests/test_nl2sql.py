import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch, MagicMock
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "rag"))
import nl2sql as n

BASE = "SELECT sku, product, warehouse, stockout_risk FROM demo_inventory WHERE stockout_risk >= 70 ORDER BY stockout_risk DESC, sku FETCH FIRST 3 ROWS ONLY"

class NL2SQLTests(unittest.TestCase):
    def setUp(self):
        n.PENDING.clear()

    def test_valid(self):
        self.assertEqual(n.validate_sql(BASE), {"minimum_risk":70,"row_limit":3})
        self.assertEqual(n.validate_sql(BASE.lower()), n.validate_sql(BASE))

    def test_reject_unsafe_sql(self):
        attacks = [BASE+"; DROP TABLE demo_inventory", BASE+" --x",
                   BASE.replace("demo_inventory","dba_users"),
                   BASE.replace("sku, product","UTL_HTTP.REQUEST('https://example.com'), product",1),
                   BASE.replace(">= 70",">= 70 OR 1=1"),
                   BASE.replace(">= 70",">= 101"), BASE.replace("FIRST 3","FIRST 99"),
                   BASE.replace("FIRST 3","FIRST 0"), BASE.replace(">= 70",">= -1"),
                   BASE+" UNION SELECT * FROM dual", "DELETE FROM demo_inventory",
                   BASE.replace(">= 70",">= ７０"), BASE.replace("FROM demo_inventory","FROM demo_inventory@remote")]
        for sql in attacks:
            with self.subTest(sql=sql), self.assertRaises(ValueError):
                n.validate_sql(sql)

    def test_unknown_receipt_never_connects(self):
        with patch.object(n.core.oracledb,"connect") as connect:
            with self.assertRaises(ValueError): n.execute("fabricated")
            connect.assert_not_called()

    def test_generate_only_does_not_connect(self):
        runtime=MagicMock()
        runtime.converse.return_value={"output":{"message":{"content":[{"text":__import__("json").dumps({"sql":BASE})}]}},
                                       "ResponseMetadata":{"RequestId":"test"}}
        with patch.object(n,"bedrock",return_value=runtime), patch.object(n.core.oracledb,"connect") as connect:
            result=n.generate("Top 3 items with risk at least 70")
            connect.assert_not_called()
            self.assertIn(result["receipt"],n.PENDING)
            self.assertEqual(result["model"],n.MODEL)

    def test_unsupported_does_not_create_receipt(self):
        runtime=MagicMock()
        runtime.converse.return_value={"output":{"message":{"content":[{"text":'{"sql":null}'}]}}}
        with patch.object(n,"bedrock",return_value=runtime):
            self.assertTrue(n.generate("Delete inventory")["rejected"])
            self.assertFalse(n.PENDING)

    def test_expired_receipt_never_connects(self):
        n.PENDING["expired"]={"sql":BASE,"expires":0}
        with patch.object(n.core.oracledb,"connect") as connect:
            with self.assertRaises(ValueError): n.execute("expired")
            connect.assert_not_called()

    def test_fixed_query_binds_not_generated_sql(self):
        self.assertIn(":inventory",n.QUERY)
        self.assertIn(":minimum_risk",n.QUERY)
        self.assertIn(":row_limit",n.QUERY)
        self.assertEqual(len(n.INVENTORY),5)

if __name__ == "__main__": unittest.main()
