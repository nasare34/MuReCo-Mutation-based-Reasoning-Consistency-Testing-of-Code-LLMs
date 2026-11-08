"""Task 3, part 1: run MuCoCo's own experiment on a small open model.

Uses, unchanged from the MuCoCo repository: the CruxEval dataset it ships,
its 11 mutation operators and validity check (CodeMutator), its zero-shot
output-prediction prompt, its answer processing and its correctness check
(verify_with_canon_ans). Prints a table in the layout of the paper's Table 6.

Example (Colab GPU):
  python scripts/run_mucoco_demo.py --model Qwen/Qwen2.5-Coder-1.5B-Instruct --n 50
"""
import argparse, contextlib, io, json, os, random, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from mureco.tasks import load_cruxeval
from mureco.bridge import mutate
from mureco.prompts import mucoco_prompt, mucoco_process_answer
from mureco.oracle import answer_correct

OPS = {"Lexical": ["random", "sequential", "literal_format"],
       "Syntactic": ["for2while", "for2enumerate"],
       "Logical": ["demorgan", "boolean_literal", "commutative_reorder", "constant_unfold",
                   "constant_unfold_add", "constant_unfold_mult"]}


def outcome(text, expected):
    ans = mucoco_process_answer(text)
    if ans in ("", None):
        return "invalid", ans
    return ("correct" if answer_correct(ans, expected, mucoco_compat=True) else "incorrect"), ans


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-Coder-1.5B-Instruct")
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="results_part1")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    tasks = load_cruxeval()
    random.Random(a.seed).shuffle(tasks)
    tasks = tasks[:a.n]

    items = []
    for t in tasks:
        vs = [("original", None, t["code"])]
        for cat, ops in OPS.items():
            for op in ops:
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        code, _, _ = mutate(t["code"], t["input"], t["output"], [op],
                                            input_metadata=type(t["input"]).__name__)
                    vs.append((op, cat, code))
                except Exception:
                    pass
        items.append((t, vs))
    prompts = [mucoco_prompt(code, t) for t, vs in items for _, _, code in vs]
    print(f"{len(tasks)} tasks, {len(prompts) - len(tasks)} MuCoCo test cases (mutants)")

    from mureco.models import HFModel
    model = HFModel(a.model, max_new_tokens=128, batch_size=a.batch)
    resp = model.generate(prompts)

    k, rows, origs = 0, [], []
    for t, vs in items:
        outs = []
        for op, cat, code in vs:
            outs.append((op, cat) + outcome(resp[k], t["output"]) + (resp[k],)); k += 1
        o = outs[0]
        origs.append(o)
        for op, cat, oc, ans, raw in outs[1:]:
            inc = oc != o[2] or (oc == "incorrect" and repr(ans) != repr(o[3]))
            rows.append({"task": t["id"], "op": op, "category": cat, "orig_outcome": o[2], "mut_raw": raw, "orig_raw": o[4],
                         "mut_outcome": oc, "inconsistent": inc, "orig_answer": repr(o[3]), "mut_answer": repr(ans)})
    with open(os.path.join(a.out, "mucoco_rows.jsonl"), "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    def line(name, sel):
        inc = sum(r["inconsistent"] for r in sel); acc = sum(r["mut_outcome"] == "correct" for r in sel)
        n = len(sel)
        return f"| {name} | {100*inc/n:.2f} ({inc}/{n}) | {100*acc/n:.2f} ({acc}/{n}) |" if n else f"| {name} | n/a | n/a |"
    out = [f"## MuCoCo reproduction: {a.model}, CruxEval output prediction, {len(tasks)} tasks", "",
           "| Mutation type | Inconsistency % | Mutant accuracy % |", "|---|---|---|"]
    for cat in OPS:
        out.append(line(cat, [r for r in rows if r["category"] == cat]))
    out.append(line("All", rows))
    no = len(origs)
    oacc = sum(o[2] == "correct" for o in origs); oinv = sum(o[2] == "invalid" for o in origs)
    minv = sum(r["mut_outcome"] == "invalid" for r in rows)
    out += ["", f"Original-program accuracy: {100*oacc/no:.2f}% ({oacc}/{no}); "
            f"invalid answers: originals {oinv}/{no}, mutants {minv}/{len(rows)}"]

    out += ["", "| Operator | Inconsistency % | Mutant accuracy % |", "|---|---|---|"]
    for cat, ops in OPS.items():
        for op in ops:
            out.append(line(op, [r for r in rows if r["op"] == op]))
    text = "\n".join(out)
    open(os.path.join(a.out, "MUCOCO_TABLE.md"), "w").write(text)
    print(text)


if __name__ == "__main__":
    main()
