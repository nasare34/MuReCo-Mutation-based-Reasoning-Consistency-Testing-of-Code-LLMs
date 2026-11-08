"""Run MuReCo end to end: query a model on every variant, score, summarise."""
import json
import os
import random
import time

from .oracle import score_variant, summarise


def run(suite, model, reruns=2, out_dir="results", log=print, seed=0):
    os.makedirs(out_dir, exist_ok=True)
    prompts = [v["prompt"] for it in suite for v in it["variants"]]
    t0 = time.time()
    log(f"[MuReCo] {model.name}: {len(prompts)} prompts for {len(suite)} tasks")
    responses = dict(zip(prompts, model.generate(prompts)))
    rerun_resp = []
    if reruns:
        rng = random.Random(seed)
        orig_prompts = [it["variants"][0]["prompt"] for it in suite]
        for r in range(reruns):
            order = orig_prompts[:]
            rng.shuffle(order)                 # different batch composition each rerun
            rerun_resp.append(dict(zip(order, model.generate(order))))
    log(f"[MuReCo] generation done in {time.time() - t0:.0f}s")
    task_records = []
    for it in suite:
        recs = {v["variant"]: score_variant(v, responses[v["prompt"]], it) for v in it["variants"]}
        o = it["variants"][0]
        reruns_scored = [score_variant(o, rr[o["prompt"]], it) for rr in rerun_resp]
        task_records.append({"id": it["id"], "orig_id": it["orig_id"], "records": recs, "reruns": reruns_scored})
    summary, rows = summarise(task_records)
    summary["model"] = model.name
    summary["seconds"] = round(time.time() - t0)
    tag = model.name.split("/")[-1]
    with open(os.path.join(out_dir, f"{tag}_records.jsonl"), "w") as f:
        for t, it in zip(task_records, suite):
            f.write(json.dumps({"task": it["id"], "orig_id": it["orig_id"], "tracked": it["tracked"],
                                "gt_trace": it["gt_trace"], "expected": repr(it["expected"]),
                                "variants": {v["variant"]: {"code": v["code"], "prompt": v["prompt"],
                                                            **{k: x for k, x in t["records"][v["variant"]].items()}}
                                             for v in it["variants"]},
                                "compare": t["compare"]}, default=str) + "\n")
    with open(os.path.join(out_dir, f"{tag}_summary.json"), "w") as f:
        json.dump(summary, f, indent=2, default=str)
    return summary, rows, task_records
