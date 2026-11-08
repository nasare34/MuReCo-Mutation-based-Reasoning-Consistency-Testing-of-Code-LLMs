"""Pipeline validation with test doubles (no LLM needed).
1) Oracle model -> must give 0% inconsistency and 100% trace accuracy.
2) Corrupting oracle (drops one trace step on ~30% of mutants, answer kept
   correct) -> MuReCo must flag these as reasoning inconsistencies, while
   MuCoCo's answer-level oracle sees 0%."""
import os, sys, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
from mureco.tasks import load_cruxeval
from mureco.suite import build_suite
from mureco.models import OracleModel, CorruptingOracle
from mureco.pipeline import run
from mureco.report import fmt


from scripts_selftest_helpers import corrupt


suite = build_suite(load_cruxeval(), n_tasks=int(os.environ.get("N", 40)))
answers = {v["prompt"]: v["gt_answer"] for it in suite for v in it["variants"]}
s1, _, _ = run(suite, OracleModel(answers), reruns=1, out_dir="results_selftest", log=lambda *a: None)
assert s1["all_mutants"]["answer_inconsistency"][1] == 0, s1
assert s1["all_mutants"]["reasoning_inconsistency"][1] == 0, s1
assert s1["original"]["trace_accuracy"][0] == 100.0, s1
print("Oracle model: answer inc.", fmt(s1["all_mutants"]["answer_inconsistency"]),
      "| reasoning inc.", fmt(s1["all_mutants"]["reasoning_inconsistency"]),
      "| trace acc.", fmt(s1["original"]["trace_accuracy"]))

bad = {v["prompt"]: corrupt(v["gt_answer"]) for it in suite for v in it["variants"] if v["variant"] != "original"}
s2, rows, _ = run(suite, CorruptingOracle(answers, bad, p=0.3), reruns=0, out_dir="results_selftest", log=lambda *a: None)
injected = sum(1 for r in rows if not r["trace_correct"])
caught = sum(1 for r in rows if r["hidden_reasoning"])
print("Corrupting oracle: answer inc.", fmt(s2["all_mutants"]["answer_inconsistency"]),
      "| reasoning inc.", fmt(s2["all_mutants"]["reasoning_inconsistency"]),
      f"| injected {injected}, detected {caught}")
assert s2["all_mutants"]["answer_inconsistency"][1] == 0
comparable_injected = sum(1 for r in rows if not r["trace_correct"] and r["comparable"])
assert caught == comparable_injected, (caught, comparable_injected)
print("SELF-TEST PASSED")
