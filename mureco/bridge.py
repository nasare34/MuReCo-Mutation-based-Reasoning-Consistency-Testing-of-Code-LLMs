"""Bridge to MuCoCo's released mutation engine.

MuCoCo's `utility/constants.py` imports its LLM wrappers (OpenAI, Mistral,
HuggingFace, LangChain). We only need the AST mutation code, so we register
light stub modules for those wrappers before importing. Nothing in MuCoCo's
mutation logic is changed.
"""
import ast
import copy
import os
import sys
import types

MUCOCO_DIR = os.environ.get("MUCOCO_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "mucoco"))
MUCOCO_DIR = os.path.abspath(MUCOCO_DIR)


def _install_stubs():
    class _Stub:
        def __init__(self, *a, **k):
            pass

    for mod, names in {
        "llm_models.code_llms": ["OpenAILLM", "Codestral", "DeepSeekLLM"],
        "llm_models.code_reasoning_llms": ["OpenAIReasoningLLM"],
        "llm_models.gpu_code_llms": ["TransformersCodeLLM"],
    }.items():
        if mod in sys.modules:
            continue
        m = types.ModuleType(mod)
        for n in names:
            setattr(m, n, type(n, (_Stub,), {}))
        sys.modules[mod] = m
    if "llm_models" not in sys.modules:
        pkg = types.ModuleType("llm_models")
        pkg.__path__ = []
        sys.modules["llm_models"] = pkg


def load_mucoco():
    if not os.path.isdir(os.path.join(MUCOCO_DIR, "code_mutation")):
        raise FileNotFoundError(
            f"MuCoCo repository not found at {MUCOCO_DIR}. Clone "
            "https://github.com/mucoco-tester/mucoco-tester.github.io and set MUCOCO_DIR.")
    if MUCOCO_DIR not in sys.path:
        sys.path.insert(0, MUCOCO_DIR)
    _install_stubs()
    from code_mutation.mutation_functions import CodeMutator  # noqa: E402
    from code_mutation.mutation_relations import check_for_mutation_conflicts  # noqa: E402
    return CodeMutator, check_for_mutation_conflicts


CodeMutator, check_for_mutation_conflicts = load_mucoco()

# The five operators used in the proposal (all are MuCoCo operators).
OPERATORS = ["random", "sequential", "for2while", "demorgan", "constant_unfold"]


def _signature(code, func_name):
    tree = ast.parse(code)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            return node.name, [a.arg for a in node.args.args]
    return func_name, []


def mutate(code, input_args, output_args, mutations, func_name="f", input_metadata="list"):
    """Apply one or more MuCoCo mutations in sequence (MuCoCo's own
    second-order procedure). Returns (mutated_code, rename_map) where
    rename_map maps mutant identifiers back to original identifiers.
    Raises if MuCoCo rejects the mutation (not applicable, identical, or
    fails the validity check against the expected output)."""
    if len(mutations) > 1 and not check_for_mutation_conflicts(mutations=list(mutations)):
        raise ValueError(f"conflicting mutations {mutations}")
    cm = CodeMutator(func_name=func_name,
                     mutated_dict={"question": code, "full_sol": code, "qn_desc": "", "examples": {}},
                     benchmark_set="CruxEval")
    current_name = func_name
    for m in mutations:
        cm.func_name = current_name
        cm.mutate_for_prediction_inconsistency_test(
            mutation_type=m, input_args=copy.deepcopy(input_args), output_args=output_args,
            input_metadata=input_metadata, task_set="CruxEval")
        current_name, _ = _signature(cm.mutated_dict["full_sol"], current_name)
    mutated = cm.mutated_dict["full_sol"]
    o_name, o_args = _signature(code, func_name)
    m_name, m_args = _signature(mutated, func_name)
    rename = {m_name: o_name}
    rename.update({ma: oa for ma, oa in zip(m_args, o_args)})
    return mutated, rename, m_name
