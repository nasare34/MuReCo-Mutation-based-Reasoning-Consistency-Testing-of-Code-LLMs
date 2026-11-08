"""Load CruxEval tasks from MuCoCo's bundled dataset, exactly as MuCoCo's
CruxEval database builder parses them (eval of input and output)."""
import inspect
import os
import pandas as pd
from .bridge import MUCOCO_DIR


def load_cruxeval(path=None):
    path = path or os.path.join(MUCOCO_DIR, "datasets", "open_ended_format", "cruxeval_test.csv")
    df = pd.read_csv(path, encoding="utf-8", header=0, quoting=1)
    tasks = []
    for i, row in df.iterrows():
        ns = {}
        try:
            exec(row["code"], ns)
            fn = ns["f"]
            inp = eval(row["input"], ns)
            out = {"FALSE": False, "TRUE": True}.get(row["output"])
            out = eval(row["output"]) if out is None else out
        except Exception:
            continue
        nparams = len(inspect.signature(fn).parameters)
        args = tuple(inp) if nparams > 1 else (inp,)
        tasks.append({"id": f"CruxEval_{i}", "orig_id": row["id"], "code": row["code"],
                      "input_str": row["input"], "input": inp, "args": args,
                      "output": out, "nparams": nparams})
    return tasks
