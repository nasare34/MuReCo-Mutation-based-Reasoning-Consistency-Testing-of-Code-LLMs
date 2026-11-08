"""Build the MuReCo test suite: originals, single mutations and pairs of
mutations (MuCoCo operators), each with ground-truth traces."""
import ast
import contextlib
import io
import itertools

from .bridge import mutate, OPERATORS
from .tracer import run_with_trace, map_names, pick_tracked, canon
from .prompts import mureco_prompt, mucoco_prompt


def _params(code):
    for node in ast.parse(code).body:
        if isinstance(node, ast.FunctionDef):
            return [a.arg for a in node.args.args]
    return []


def _quiet(fn, *a, **k):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*a, **k)


def _gt_answer(tracked_variant_names, tracked_orig, hist, output):
    lines = [f"TRACE {vn}: [{', '.join(hist[vo])}]" for vn, vo in zip(tracked_variant_names, tracked_orig)]
    return "\n".join(lines + [f"OUTPUT: {canon(output)}"])


def build_task(task, ops=OPERATORS, pairs=True, max_vars=2):
    code = task["code"]
    if sum(isinstance(n, ast.FunctionDef) for n in ast.parse(code).body) != 1 or "def f(" not in code:
        return None, "not a single function f"
    try:
        out, hist = run_with_trace(code, "f", task["args"])
    except Exception as e:
        return None, f"original failed: {type(e).__name__}"
    if canon(out) != canon(task["output"]):
        return None, "original output mismatch"
    tracked = pick_tracked(hist, _params(code), max_vars=max_vars)
    if not tracked:
        return None, "no traceable variable"
    meta = type(task["input"]).__name__

    def make(name, op_list):
        if op_list:
            mcode, rename, fname = _quiet(mutate, code, task["input"], task["output"], op_list, input_metadata=meta)
        else:
            mcode, rename, fname = code, {}, "f"
        mout, mhist = run_with_trace(mcode, fname, task["args"])
        mapped = map_names(mhist, rename)
        inv = {v: k for k, v in rename.items()}
        names = [inv.get(v, v) for v in tracked]
        return {
            "variant": name, "ops": list(op_list), "code": mcode, "func_name": fname,
            "rename": rename, "tracked_names": names,
            "output_ok": canon(mout) == canon(task["output"]),
            "trace_invariant": all(mapped.get(v) == hist[v] for v in tracked),
            "prompt": mureco_prompt(mcode, fname, task["input_str"], names),
            "mucoco_prompt": mucoco_prompt(mcode, task),
            "gt_answer": _gt_answer(names, tracked, hist, task["output"]),
        }

    variants, skipped = [make("original", [])], {}
    ok_single = []
    for op in ops:
        try:
            variants.append(make(op, [op]))
            ok_single.append(op)
        except Exception as e:
            skipped[op] = type(e).__name__
    if pairs:
        for a, b in itertools.combinations(ok_single, 2):
            try:
                variants.append(make(f"{a}+{b}", [a, b]))
            except Exception as e:
                skipped[f"{a}+{b}"] = type(e).__name__
    variants = [v for v in variants if v["output_ok"]]
    return {"id": task["id"], "orig_id": task["orig_id"], "input_str": task["input_str"],
            "expected": task["output"], "tracked": tracked,
            "gt_trace": {v: hist[v] for v in tracked}, "variants": variants, "skipped": skipped}, None


def build_suite(tasks, n_tasks=50, ops=OPERATORS, pairs=True, min_variants=2, log=print):
    suite, reasons = [], {}
    for task in tasks:
        if len(suite) >= n_tasks:
            break
        item, why = build_task(task, ops=ops, pairs=pairs)
        if item is None or len(item["variants"]) < min_variants:
            why = why or "no valid mutant"
            reasons[why] = reasons.get(why, 0) + 1
            continue
        suite.append(item)
    log(f"Built {len(suite)} tasks; skipped: {reasons}")
    return suite
