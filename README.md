# MuReCo: Mutation-based Reasoning Consistency Testing of Code LLMs

| | MuCoCo (Part 1) | MuReCo (Part 2, this prototype) |
|---|---|---|
| Mutations | MuCoCo's 11 operators | MuCoCo's operators, **imported unchanged** (random, sequential, for2while, demorgan, constant_unfold) |
| Combined mutations | Appendix H only | All valid **pairs**, with HInter-style **hidden failure** check |
| Validity | Mutant passes the original test | Same, **plus trace invariance**: the true trace is identical across versions |
| What is checked | Final answer | Final answer **and** a step-by-step trace of key variables |
| Oracle for reasoning | none | **Real execution** (`sys.settrace`), no human or LLM judge |
| Noise control | temperature 0 | Each original **rerun** in a different batch; flip rate reported |

## Files
```
mureco/bridge.py     loads MuCoCo's CodeMutator (stubs its LLM wrappers only)
mureco/tasks.py      CruxEval from MuCoCo's datasets/, parsed as MuCoCo does
mureco/tracer.py     ground-truth value histories via sys.settrace
mureco/suite.py      originals, single mutations, pairs; validity + trace invariance
mureco/prompts.py    MuCoCo's zero-shot prompt (Part 1) and MuReCo's trace prompt
mureco/oracle.py     MuCoCo's answer categories + reasoning and hidden-failure oracles
mureco/pipeline.py   run a model, score, save records and summary
mureco/report.py     tables, chart, examples of "right answer, wrong reasoning"
scripts/selftest.py        validates the pipeline with test doubles (no model)
scripts/parser_test.py     unit tests for the answer parser
scripts/run_mucoco_demo.py Part 1: MuCoCo's experiment on a small model
scripts/run_mureco.py      Part 2: MuReCo on one or more models (--dry-run without GPU)
scripts/walkthrough.py     live demo of one task, for the presentation
notebooks/Task3_MuCoCo_MuReCo.ipynb   everything on a free Colab T4
```

## Quick start (Colab)
1. Open `notebooks/Task3_MuCoCo_MuReCo.ipynb` in Colab, select a T4 GPU.
2. Run the cells; upload `mureco.zip` when asked.

Locally: `git clone https://github.com/mucoco-tester/mucoco-tester.github.io mucoco`,
place this folder next to it (or set `MUCOCO_DIR`), `pip install pandas numpy transformers accelerate`.

## Metrics
* **Answer inconsistency** (MuCoCo): correctness-, incorrectness- or invalidity-based.
* **Reasoning inconsistency** (MuReCo): among pairs whose answers agree, the share
  whose traces disagree (one matches execution and the other does not, or both wrong but different).
* **Right answer, wrong reasoning**: correct output with a trace that contradicts execution.
* **Hidden pair failures**: share of inconsistent pairs a+b where a alone and b alone are consistent.
* **Trace accuracy, step accuracy, first divergence step**, and **noise flip rate**.

## Notes
* Answer correctness here is strict. MuCoCo's `verify_with_canon_ans` sorts lists before
  comparing (so `[3, 1]` passes for `[1, 3]`); Part 1 keeps MuCoCo's behaviour, Part 2 does not.
* `selftest.py`: a perfect test double must give 0% inconsistency; injected trace errors with
  correct answers must all be detected (MuCoCo's answer oracle sees 0% of them).
