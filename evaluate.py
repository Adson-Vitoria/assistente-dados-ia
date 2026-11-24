"""Avalia quatro perguntas na API real e imprime um relatório JSON."""
import json
from pathlib import Path
from engine import EXAMPLES, load_csv, plan_query, query

def main():
    dataset = load_csv(Path(__file__).with_name("data").joinpath("vendas_demo.csv").read_bytes())
    cases = []
    for example in EXAMPLES:
        expected = query(dataset, example["sql"])
        try:
            plan = plan_query(example["question"], dataset["schema"])
            if plan["clarification"]:
                cases.append({"question": example["question"], "passed": False, "clarification": plan["clarification"]})
                continue
            actual = query(dataset, plan["sql"])
            # Compara valores e ordem, aceitando aliases de colunas diferentes.
            cases.append({"question": example["question"], "passed": actual["rows"] == expected["rows"],
                          "expected": expected["rows"], "actual": actual["rows"], "sql": plan["sql"]})
        except ValueError as error:
            cases.append({"question": example["question"], "passed": False, "error": str(error)})
    report = {"total": len(cases), "passed": sum(case["passed"] for case in cases), "cases": cases}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return int(report["passed"] != report["total"])

if __name__ == "__main__":
    raise SystemExit(main())
