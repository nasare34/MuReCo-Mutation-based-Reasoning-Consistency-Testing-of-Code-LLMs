"""Readable report: summary table, per-operator table, charts, and examples
of hidden reasoning inconsistencies (right answer, wrong reasoning)."""
import os


def fmt(r):
    v, k, n = r
    return "n/a" if v is None else f"{v:.1f}% ({k}/{n})"


def tables(summary):
    s = summary
    lines = [f"## {s['model']}  ({s['n_tasks']} CruxEval tasks)", "",
             "| Measure | Value |", "|---|---|",
             f"| Parsing: answers with no readable output | {fmt(s['parsing']['invalid_output_rate'])} |",
             f"| Parsing: answers with all traces readable | {fmt(s['parsing']['trace_parsed_rate'])} |",
             f"| Original: answer accuracy | {fmt(s['original']['answer_accuracy'])} |",
             f"| Original: trace accuracy | {fmt(s['original']['trace_accuracy'])} |",
             f"| Original: right answer, wrong reasoning | {fmt(s['original']['right_answer_wrong_reasoning'])} |"]
    for key, label in [("single_mutations", "Single mutations"), ("pairs_of_mutations", "Pairs of mutations"), ("all_mutants", "All mutants")]:
        b = s[key]
        lines += [f"| {label}: answer inconsistency (MuCoCo) | {fmt(b['answer_inconsistency'])} |",
                  f"| {label}: reasoning inconsistency, answers agree (MuReCo) | {fmt(b['reasoning_inconsistency'])} |"]
    lines.append(f"| Hidden pair failures (pair fails, both singles pass) | {fmt(s['hidden_pair_failures'])} |")
    if s.get("noise"):
        lines.append(f"| Noise: rerun flip rate on originals | {fmt(s['noise']['rerun_flip_rate'])} |")
    lines += ["", "| Variant | Pairs | Answer inc. | Reasoning inc. (answers agree) | Mutant trace acc. |", "|---|---|---|---|---|"]
    for v, b in s["per_operator"].items():
        lines.append(f"| {v} | {b['n_pairs']} | {fmt(b['answer_inconsistency'])} | {fmt(b['reasoning_inconsistency'])} | {fmt(b['mutant_trace_accuracy'])} |")
    return "\n".join(lines)


def examples(task_records, suite, k=3):
    by_id = {it["id"]: it for it in suite}
    out = []
    for t in task_records:
        for v, c in t["compare"].items():
            if c["hidden_reasoning"] and len(out) < k:
                it = by_id[t["id"]]
                o, m = t["records"]["original"], t["records"][v]
                var = next(vv for vv in it["variants"] if vv["variant"] == v)
                out.append("\n".join([
                    f"### {t['id']} ({t['orig_id']}), mutation: {v}",
                    "Original program:", "```python", it["variants"][0]["code"], "```",
                    f"Mutated program ({v}):", "```python", var["code"], "```",
                    f"Call input: `{it['input_str']}`; expected output `{it['expected']!r}`", "",
                    "| | Answer | Trace |", "|---|---|---|",
                    f"| Ground truth | `{it['expected']!r}` | `{it['gt_trace']}` |",
                    f"| Model on original | `{o['output']}` ({o['outcome']}) | `{o['traces']}` |",
                    f"| Model on mutant | `{m['output']}` ({m['outcome']}) | `{m['traces']}` |", ""]))
    return "\n\n".join(out) if out else "_No hidden reasoning inconsistencies found in this run._"


def charts(summaries, out_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    paths = []
    names = [s["model"].split("/")[-1] for s in summaries]
    groups = [("single_mutations", "Single"), ("pairs_of_mutations", "Pairs")]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    width = 0.2
    xs = range(len(summaries))
    bars = [(g, "answer_inconsistency", f"{lbl}: answer (MuCoCo)") for g, lbl in groups] + \
           [(g, "reasoning_inconsistency", f"{lbl}: reasoning (MuReCo)") for g, lbl in groups]
    for j, (g, m, lbl) in enumerate(bars):
        vals = [(s[g][m][0] or 0) for s in summaries]
        ax.bar([x + (j - 1.5) * width for x in xs], vals, width, label=lbl)
    ax.set_xticks(list(xs)); ax.set_xticklabels(names)
    ax.set_ylabel("Inconsistency rate (%)"); ax.set_title("Answer-level vs reasoning-level inconsistency")
    ax.legend(fontsize=8); fig.tight_layout()
    p = os.path.join(out_dir, "inconsistency_rates.png"); fig.savefig(p, dpi=160); plt.close(fig); paths.append(p)
    return paths


def write_report(summaries, per_model_examples, out_dir, title="MuReCo prototype results"):
    parts = [f"# {title}", ""]
    for s, ex in zip(summaries, per_model_examples):
        parts += [tables(s), "", "### Examples: answers agree, reasoning does not", "", ex, ""]
    p = os.path.join(out_dir, "REPORT.md")
    open(p, "w").write("\n".join(parts))
    return p
