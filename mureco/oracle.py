"""MuReCo oracles and metrics.

Answer level (MuCoCo, Table 2): an (original, mutant) pair is inconsistent if
one output is correct and the other is not (correctness-based), both are wrong
with different answers (incorrectness-based), or exactly one is invalid
(invalidity-based). Correctness is strict canonical equality. (MuCoCo's
`verify_with_canon_ans` sorts lists before comparing, so it accepts outputs in
the wrong order; `answer_correct(..., mucoco_compat=True)` reproduces that.)

Reasoning level (new): a pair is reasoning-inconsistent if the traces are
comparable (mutant is trace-invariant, both traces parsed) and either exactly
one trace matches real execution, or both are wrong but differ.

Hidden failures (HInter's idea, applied to code): a pair-of-mutations variant
a+b is a hidden failure if it is inconsistent while both single mutations a
and b are consistent.
"""
from statistics import mean

from .bridge import CodeMutator
from .prompts import parse_mureco
from .tracer import canon


def _norm(x, gt_set):
    """Canonical form of a predicted value; a quoted value such as '[1, 2]'
    is read as the literal it spells when that matches a true value."""
    c = canon(x)
    if c not in gt_set and isinstance(x, str):
        try:
            import ast
            alt = canon(ast.literal_eval(x))
            if alt in gt_set:
                return alt
        except Exception:
            pass
    return c


def _dedupe(seq, gt_set=frozenset()):
    out = []
    for x in seq:
        c = _norm(x, gt_set)
        if not out or out[-1] != c:
            out.append(c)
    return out


def answer_correct(pred, expected, mucoco_compat=False):
    if not mucoco_compat:
        return canon(pred) == canon(expected)
    try:
        CodeMutator.verify_with_canon_ans(func_output=pred, canon_ans=expected)
        return True
    except Exception:
        return False


def score_variant(variant, response, item):
    p = parse_mureco(response, variant["tracked_names"])
    rec = {"variant": variant["variant"], "ops": variant["ops"], "order": len(variant["ops"]),
           "trace_invariant": variant["trace_invariant"], "raw": response}
    if not p["output_ok"]:
        rec.update(outcome="invalid", output=None)
    else:
        rec.update(outcome="correct" if answer_correct(p["output"], item["expected"]) else "incorrect",
                   output=canon(p["output"]))
    traces, exact, steps, first_div = {}, [], [], []
    for vn, vo in zip(variant["tracked_names"], item["tracked"]):
        gt = item["gt_trace"][vo]
        pred = p["trace"].get(vn)
        if pred is None:
            traces[vo] = None
            continue
        pred = _dedupe(pred, frozenset(gt))
        traces[vo] = pred
        n = max(len(pred), len(gt))
        match = [i < len(pred) and i < len(gt) and pred[i] == gt[i] for i in range(n)]
        exact.append(pred == gt)
        steps.append(sum(match) / n if n else 1.0)
        first_div.append(next((i for i, m in enumerate(match) if not m), None))
    rec["traces"] = traces
    rec["trace_valid"] = all(t is not None for t in traces.values())
    rec["trace_correct"] = rec["trace_valid"] and all(exact)
    rec["step_acc"] = mean(steps) if steps else None
    rec["first_div"] = min([d for d in first_div if d is not None], default=None)
    rec["right_answer_wrong_reasoning"] = rec["outcome"] == "correct" and rec["trace_valid"] and not rec["trace_correct"]
    return rec


def compare(orig, mut):
    """Compare a mutant record against the original record of the same task."""
    if orig["outcome"] != mut["outcome"]:
        kind = "invalidity" if "invalid" in (orig["outcome"], mut["outcome"]) else "correctness"
        ans_inc = True
    elif orig["outcome"] == "incorrect" and orig["output"] != mut["output"]:
        kind, ans_inc = "incorrectness", True
    else:
        kind, ans_inc = None, False
    comparable = mut["trace_invariant"] and orig["trace_valid"] and mut["trace_valid"]
    if comparable:
        reas_inc = (orig["trace_correct"] != mut["trace_correct"]) or (
            not orig["trace_correct"] and orig["traces"] != mut["traces"])
    else:
        reas_inc = None
    return {"answer_inconsistent": ans_inc, "answer_kind": kind, "comparable": comparable,
            "reasoning_inconsistent": reas_inc,
            "hidden_reasoning": comparable and not ans_inc and reas_inc,
            "any_inconsistent": ans_inc or bool(reas_inc)}


def _rate(xs):
    xs = [x for x in xs if x is not None]
    return (100.0 * sum(xs) / len(xs), sum(xs), len(xs)) if xs else (None, 0, 0)


def summarise(task_records):
    """task_records: list of {'id', 'records': {variant: rec}, 'reruns': [rec,...]}"""
    rows = []
    for t in task_records:
        recs = t["records"]
        orig = recs["original"]
        cmp = {v: compare(orig, r) for v, r in recs.items() if v != "original"}
        for v, c in cmp.items():
            r = recs[v]
            hidden_pair = None
            if r["order"] == 2:
                a, b = r["ops"]
                ca, cb = cmp.get(a), cmp.get(b)
                if ca is not None and cb is not None:
                    hidden_pair = c["any_inconsistent"] and not ca["any_inconsistent"] and not cb["any_inconsistent"]
            rows.append({"task": t["id"], "variant": v, "order": r["order"], **c,
                         "hidden_pair": hidden_pair, "outcome": r["outcome"],
                         "trace_correct": r["trace_correct"], "step_acc": r["step_acc"],
                         "first_div": r["first_div"],
                         "rawr": r["right_answer_wrong_reasoning"]})
        t["compare"] = cmp

    def block(sel):
        return {
            "n_pairs": len(sel),
            "answer_inconsistency": _rate([r["answer_inconsistent"] for r in sel]),
            "reasoning_inconsistency": _rate([r["reasoning_inconsistent"] for r in sel
                                              if not r["answer_inconsistent"]]),
            "any_inconsistency": _rate([r["any_inconsistent"] for r in sel]),
            "mutant_trace_accuracy": _rate([r["trace_correct"] for r in sel]),
            "mutant_right_answer_wrong_reasoning": _rate([r["rawr"] for r in sel if r["outcome"] == "correct"]),
        }

    origs = [t["records"]["original"] for t in task_records]
    summary = {
        "n_tasks": len(task_records),
        "original": {
            "answer_accuracy": _rate([o["outcome"] == "correct" for o in origs]),
            "trace_accuracy": _rate([o["trace_correct"] for o in origs]),
            "right_answer_wrong_reasoning": _rate([o["right_answer_wrong_reasoning"] for o in origs if o["outcome"] == "correct"]),
        },
        "parsing": {
            "invalid_output_rate": _rate([r["outcome"] == "invalid" for t in task_records for r in t["records"].values()]),
            "trace_parsed_rate": _rate([r["trace_valid"] for t in task_records for r in t["records"].values()]),
        },
        "all_mutants": block(rows),
        "single_mutations": block([r for r in rows if r["order"] == 1]),
        "pairs_of_mutations": block([r for r in rows if r["order"] == 2]),
        "hidden_pair_failures": _rate([r["hidden_pair"] for r in rows if r["order"] == 2 and r["any_inconsistent"]]),
        "per_operator": {},
        "noise": None,
    }
    for v in sorted({r["variant"] for r in rows}, key=lambda x: (x.count("+"), x)):
        summary["per_operator"][v] = block([r for r in rows if r["variant"] == v])
    flips = []
    for t in task_records:
        o = t["records"]["original"]
        for rr in t.get("reruns", []):
            flips.append(rr["output"] != o["output"] or rr["traces"] != o["traces"])
    if flips:
        summary["noise"] = {"rerun_flip_rate": _rate(flips)}
    return summary, rows
