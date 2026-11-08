"""Task 3, part 2: the MuReCo prototype.

Example (Colab GPU):
  python scripts/run_mureco.py --models Qwen/Qwen2.5-Coder-1.5B-Instruct Qwen/Qwen2.5-Coder-3B-Instruct --n 40
  python scripts/run_mureco.py --models deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B --n 20 --max-new-tokens 2048
"""
import argparse, json, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
from mureco.tasks import load_cruxeval
from mureco.suite import build_suite
from mureco.bridge import OPERATORS
from mureco.pipeline import run
from mureco.report import tables, examples, charts, write_report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=["Qwen/Qwen2.5-Coder-1.5B-Instruct"])
    ap.add_argument("--n", type=int, default=40, help="number of CruxEval tasks")
    ap.add_argument("--ops", nargs="+", default=OPERATORS)
    ap.add_argument("--reruns", type=int, default=2, help="noise baseline: reruns of each original")
    ap.add_argument("--max-new-tokens", type=int, default=384)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--4bit", dest="four_bit", action="store_true", help="load models in 4-bit (for 7B on a T4)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="results_part2")
    ap.add_argument("--dry-run", action="store_true", help="no GPU: use the corrupting test double to check the flow")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    tasks = load_cruxeval()
    random.Random(a.seed).shuffle(tasks)
    suite = build_suite(tasks, n_tasks=a.n, ops=a.ops)
    n_var = sum(len(it["variants"]) for it in suite)
    print(f"Suite: {len(suite)} tasks, {n_var} programs ({n_var - len(suite)} mutants)")

    summaries, exs = [], []
    for name in a.models:
        if a.dry_run:
            from mureco.models import CorruptingOracle
            from scripts_selftest_helpers import corrupt
            answers = {v["prompt"]: v["gt_answer"] for it in suite for v in it["variants"]}
            bad = {v["prompt"]: corrupt(v["gt_answer"]) for it in suite for v in it["variants"] if v["variant"] != "original"}
            model = CorruptingOracle(answers, bad, p=0.25)
            model.name = "dry-run test double"
        else:
            from mureco.models import HFModel
            model = HFModel(name, max_new_tokens=a.max_new_tokens, batch_size=a.batch, load_in_4bit=a.four_bit)
        s, rows, recs = run(suite, model, reruns=a.reruns, out_dir=a.out)
        summaries.append(s); exs.append(examples(recs, suite))
        print(tables(s)); print()
        del model
        try:
            import torch, gc; gc.collect(); torch.cuda.empty_cache()
        except Exception:
            pass
    charts(summaries, a.out)
    print("Report:", write_report(summaries, exs, a.out))


if __name__ == "__main__":
    main()
