"""Ground-truth execution traces via sys.settrace.

For each variable we record its *value history*: every value it takes, in
order, starting at its first assignment, adding an entry only when the value
changes. Value histories are invariant under MuCoCo's semantic-preserving
mutations (after mapping renamed identifiers back), which is what lets us
compare a model's reasoning across equivalent programs.
"""
import copy
import signal
import sys
from collections import OrderedDict


def canon(v):
    """Canonical, order-insensitive string form of a value (used for
    comparing runtime values with values parsed from model answers)."""
    if isinstance(v, (set, frozenset)):
        try:
            return "{" + ", ".join(sorted(canon(x) for x in v)) + "}"
        except Exception:
            return repr(v)
    if isinstance(v, dict):
        return "{" + ", ".join(f"{canon(k)}: {canon(x)}" for k, x in v.items()) + "}"
    if isinstance(v, list):
        return "[" + ", ".join(canon(x) for x in v) + "]"
    if isinstance(v, tuple):
        inner = ", ".join(canon(x) for x in v)
        return "(" + inner + ("," if len(v) == 1 else "") + ")"
    if isinstance(v, float) and v.is_integer():
        return repr(v)
    return repr(v)


class _Timeout(Exception):
    pass


def _alarm(signum, frame):
    raise _Timeout()


def run_with_trace(code, func_name, args, timeout=5):
    """Execute `func_name(*args)` defined in `code`; return (output, histories)
    where histories maps variable name -> list of canonical values."""
    ns = {}
    exec(code, ns)
    fn = ns[func_name]
    target = fn.__code__
    hist = OrderedDict()

    def snapshot(frame):
        for name, val in frame.f_locals.items():
            try:
                c = canon(copy.deepcopy(val))
            except Exception:
                c = canon(val)
            h = hist.setdefault(name, [])
            if not h or h[-1] != c:
                h.append(c)

    def local(frame, event, arg):
        if event in ("line", "return"):
            snapshot(frame)
        return local

    def glob(frame, event, arg):
        if frame.f_code is target:
            return local
        return None

    old = signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(timeout)
    sys.settrace(glob)
    try:
        out = fn(*copy.deepcopy(args))
    finally:
        sys.settrace(None)
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)
    return out, dict(hist)


def map_names(hist, rename):
    """Rename mutant variables back to original names; unknown names are kept."""
    return {rename.get(k, k): v for k, v in hist.items()}


def _is_literal(text):
    import ast
    try:
        ast.literal_eval(text)
        return True
    except Exception:
        return False


def pick_tracked(hist, params, max_vars=2, min_len=2, max_len=8, max_chars=60):
    """Choose the variables the model must trace: locals (then parameters)
    that change at least once, with short histories and short values.
    Variables holding non-literal objects (iterators, map objects, slices)
    are excluded: they have no value a model could write down."""
    cands = []
    for i, (name, h) in enumerate(hist.items()):
        if not (min_len <= len(h) <= max_len):
            continue
        if any(len(x) > max_chars for x in h):
            continue
        if not all(_is_literal(x) for x in h):
            continue
        is_param = name in params
        cands.append((is_param, -len(h), i, name))
    cands.sort()
    return [c[3] for c in cands[:max_vars]]
