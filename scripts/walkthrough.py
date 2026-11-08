"""Live demo: show, for one CruxEval task, the original and a mutant, the
ground-truth trace from real execution, and (optionally) a model's traces.

  python scripts/walkthrough.py --task CruxEval_0 --variant random+for2while
  python scripts/walkthrough.py --task CruxEval_0 --variant random+for2while --model Qwen/Qwen2.5-Coder-1.5B-Instruct
"""
import argparse, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from mureco.tasks import load_cruxeval
from mureco.suite import build_task
from mureco.oracle import score_variant, compare


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default="CruxEval_0")
    ap.add_argument("--variant", default=None)
    ap.add_argument("--model", default=None)
    a = ap.parse_args()
    task = next(t for t in load_cruxeval() if t["id"] == a.task)
    item, why = build_task(task)
    if item is None:
        sys.exit(f"Task not usable: {why}")
    names = [v["variant"] for v in item["variants"]]
    var = next((v for v in item["variants"] if v["variant"] == a.variant), item["variants"][-1])
    orig = item["variants"][0]
    print(f"Task {item['id']} ({item['orig_id']}); available variants: {', '.join(names)}\n")
    print("ORIGINAL\n" + orig["code"] + "\n")
    print(f"MUTANT ({var['variant']}, built with MuCoCo's operators; passes the original test)\n" + var["code"] + "\n")
    print(f"Call: f({item['input_str']})  expected: {item['expected']!r}")
    print(f"Tracked variables: {item['tracked']} (in mutant: {var['tracked_names']})")
    for v in item["tracked"]:
        print(f"  ground truth {v}: {item['gt_trace'][v]}")
    print(f"  trace invariant across versions: {var['trace_invariant']}\n")
    print("PROMPT SENT TO THE MODEL (mutant)\n" + var["prompt"] + "\n")
    if a.model:
        from mureco.models import HFModel
        m = HFModel(a.model, max_new_tokens=512, batch_size=2)
        ro, rm = m.generate([orig["prompt"], var["prompt"]])
        so, sm = score_variant(orig, ro, item), score_variant(var, rm, item)
        for lbl, s in (("original", so), (var["variant"], sm)):
            print(f"MODEL on {lbl}: output={s['output']} ({s['outcome']}), traces={s['traces']}, trace correct={s['trace_correct']}")
        c = compare(so, sm)
        print(f"\nMuCoCo answer-level verdict: {'INCONSISTENT' if c['answer_inconsistent'] else 'consistent'}")
        print(f"MuReCo reasoning-level verdict: {'INCONSISTENT' if c['reasoning_inconsistent'] else 'consistent' if c['comparable'] else 'not comparable'}")


if __name__ == "__main__":
    main()
