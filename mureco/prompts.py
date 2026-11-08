"""Prompts and answer parsing.

* `mucoco_prompt`: MuCoCo's zero-shot output-prediction prompt, copied from
  prediction_inconsistency/prompt_templates/prompt_template.py (answer only).
* `mureco_prompt`: MuReCo's trace prompt, asking for the value history of the
  tracked variables plus the final output.
"""
import ast
import re
import textwrap

MUCOCO_ZERO_SHOT = textwrap.dedent("""
    # You are given a code snippet, a description of the code and the input. Return the expected output in your answer. Your answer should only contain the expected output with no additional information. 
                         
    # The output should be in the expected format. For example, given max([10,1]), your answer should be 10 and not "10".
    # Do not return any reasoning in your final answer.
                         
    {qn_desc}
                
    # Code Snippet
    {full_sol}
    
    # Input
    {test_input}
                        
    # Your answer
""")


def mucoco_prompt(code, task):
    inp = task["input"]
    test_input = f'"{inp}"' if isinstance(inp, str) else inp
    return MUCOCO_ZERO_SHOT.format(qn_desc="", full_sol=code, test_input=test_input)


def mucoco_process_answer(text):
    """MuCoCo's LLMConsistencyTester.process_llm_ans, reproduced."""
    text = strip_think(text).strip()
    text = re.sub(r"^```(?:python)?\s*|\s*```$", "", text).strip()
    try:
        result = ast.literal_eval(text)
        if isinstance(result, tuple) and len(result) >= 1:
            return result[0]
        return result
    except Exception:
        return text.strip('"').strip("'")


MURECO_TEMPLATE = """You are given a Python function and an input. Execute the function mentally, step by step.

```python
{code}
```

Call: {call}

Track these variables: {vars}.
For each variable, list every value it takes, in order: start with its first value inside the function, and add a new entry each time its value changes. Then give the function's return value.

Answer in exactly this format, using Python literals, with no other text:
{format_lines}
OUTPUT: <return value>"""


def mureco_prompt(code, func_name, input_str, tracked_names):
    fmt = "\n".join(f"TRACE {v}: [value1, value2, ...]" for v in tracked_names)
    return MURECO_TEMPLATE.format(code=code.strip(), call=f"{func_name}({input_str})",
                                  vars=", ".join(tracked_names), format_lines=fmt)


def strip_think(text):
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    if "</think>" in text:                     # unterminated opening tag
        text = text.split("</think>")[-1]
    return text


_OPEN = {"[": "]", "(": ")", "{": "}"}


def _strip_md(s):
    """Remove markdown bold (**) and backticks, but never inside quoted
    strings, where they may be real program values (e.g. '6 ** 2')."""
    out, quote, esc, i = [], None, False, 0
    while i < len(s):
        ch = s[i]
        if quote:
            out.append(ch)
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == quote or ch == "\n":
                quote = None
            i += 1
            continue
        if ch in "'\"" and (i == 0 or not s[i - 1].isalnum()):
            quote = ch
            out.append(ch)
        elif s.startswith("**", i):
            i += 2
            continue
        elif ch == "`":
            pass
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def _clean(s):
    s = _strip_md(s)
    s = re.sub(r"^\s*(?:python|text)\s*$", "", s, flags=re.M)
    return s.strip()


def _balanced(s):
    """Return the bracket-balanced literal at the start of s (may span lines)."""
    s = s.lstrip()
    if not s or s[0] not in _OPEN:
        return None
    stack, quote, esc = [], None, False
    for i, ch in enumerate(s):
        if quote:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == quote:
                quote = None
            continue
        if ch in "'\"":
            quote = ch
        elif ch in _OPEN:
            stack.append(_OPEN[ch])
        elif stack and ch == stack[-1]:
            stack.pop()
            if not stack:
                return s[:i + 1]
    return None


def _literal(s):
    """Parse a Python literal from the start of s, tolerating markdown,
    trailing explanations and multi-line lists."""
    s = _clean(s)
    b = _balanced(s)
    for cand in ([b] if b else []) + [s.split("\n")[0].strip().rstrip(".").strip()]:
        try:
            return True, ast.literal_eval(cand)
        except Exception:
            pass
    line = s.split("\n")[0].strip()
    toks = line.split()                      # longest literal prefix, e.g. "6 (because ...)"
    for k in range(len(toks), 0, -1):
        try:
            return True, ast.literal_eval(" ".join(toks[:k]).rstrip(".,;"))
        except Exception:
            pass
    return False, line.strip("'\"")


def _sequence(s):
    """Parse a trace: a list literal, or values separated by arrows."""
    s = _clean(s)
    line = s.split("\n")[0]
    if "->" in line or "→" in line:
        parts = re.split(r"\s*(?:->|→)\s*", line.strip())
        if len(parts) > 1:
            out = []
            for part in parts:
                ok, v = _literal(part)
                out.append(v if ok else part.strip())
            return out
    ok, lit = _literal(s)
    if ok and isinstance(lit, (list, tuple)):
        return list(lit)
    return None


def _after(label, body):
    """Text after the last 'LABEL:' (case-insensitive, markdown tolerant)."""
    pat = re.compile(rf"(?im)^[ \t>*#-]*{label}\s*[:=]\s*")
    ms = list(pat.finditer(body))
    return body[ms[-1].end():] if ms else None


def parse_mureco(text, tracked_names):
    """Return {'trace': {var: list|None}, 'output': value, 'output_ok': bool}."""
    body = _strip_md(strip_think(text))
    trace = {}
    for v in tracked_names:
        rest = _after(rf"TRACE\s+{re.escape(v)}", body)
        if rest is None:
            rest = _after(re.escape(v), body)      # e.g. "output: [...]"
        trace[v] = _sequence(rest) if rest is not None else None
    rest = _after(r"(?:OUTPUT|RETURN(?:\s+VALUE)?|FINAL\s+OUTPUT)", body)
    if rest is None or not rest.strip():
        return {"trace": trace, "output": None, "output_ok": False}
    ok, out = _literal(rest)
    return {"trace": trace, "output": out, "output_ok": ok or bool(str(out).strip())}
