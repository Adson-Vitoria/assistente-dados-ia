import json
import unittest
from pathlib import Path

from engine import EXAMPLES, load_csv, parse_plan, query


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.dataset = load_csv(Path("data/vendas_demo.csv").read_bytes())

    def test_examples_match_independent_answers(self):
        expected = {
            "regiao": ["Centro-Oeste", 24600.0],
            "produto": ["Teclado", 30.0],
            "mes": ["2026-01", 16800.0],
            "ticket": [5275.0],
        }
        for item in EXAMPLES:
            with self.subTest(item=item["id"]):
                self.assertEqual(query(self.dataset, item["sql"])["rows"][0], expected[item["id"]])

    def test_blocks_writes_files_and_system_tables(self):
        attacks = [
            "DROP TABLE dados", "DELETE FROM dados", "UPDATE dados SET valor_venda=0",
            "ATTACH DATABASE '/tmp/test.db' AS outro", "PRAGMA table_info(dados)",
            "SELECT * FROM sqlite_master", "SELECT load_extension('x')",
            "SELECT randomblob(1000000000)", "SELECT * FROM dados; DELETE FROM dados",
            "WITH RECURSIVE t(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM t) SELECT * FROM t",
        ]
        for sql in attacks:
            with self.subTest(sql=sql), self.assertRaises(ValueError):
                query(self.dataset, sql)
        self.assertEqual(query(self.dataset, "SELECT COUNT(*) FROM dados")["rows"], [[12]])

    def test_numeric_import_preserves_identifiers(self):
        data = load_csv('código;valor\n0012;12,50\n0023;\n'.encode())
        self.assertEqual(data["schema"][0]["type"], "TEXT")
        self.assertEqual(data["rows"], [["0012", 12.5], ["0023", None]])

    def test_rejects_duplicate_headers_and_wrong_rows(self):
        for raw in [b"a,a\n1,2", b"a,b\n1,2,3", b"a,b\n", b""]:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                load_csv(raw)

    def test_result_limit(self):
        data = load_csv(("id\n" + "\n".join(str(i) for i in range(250))).encode())
        result = query(data, "SELECT * FROM dados ORDER BY id")
        self.assertEqual(len(result["rows"]), 200)
        self.assertTrue(result["truncated"])

    def test_plan_refusal_incomplete_and_ambiguity(self):
        for value in [{"status":"incomplete"}, {"status":"completed","output":[
            {"content":[{"type":"refusal"}]}]}]:
            with self.assertRaises(ValueError):
                parse_plan(value)
        plan = {"sql": "", "clarification": "Melhor por faturamento ou quantidade?"}
        response = {"status":"completed","output":[{"content":[
            {"type":"output_text","text":json.dumps(plan)}]}]}
        self.assertEqual(parse_plan(response), plan)
        plan["sql"] = "SELECT 1"
        response["output"][0]["content"][0]["text"] = json.dumps(plan)
        with self.assertRaises(ValueError):
            parse_plan(response)


if __name__ == "__main__":
    unittest.main()
