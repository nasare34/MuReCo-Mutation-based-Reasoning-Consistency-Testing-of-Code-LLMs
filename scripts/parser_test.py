"""Unit tests for the answer parser on formats small models really produce."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from mureco.prompts import parse_mureco

V = ["output", "n"]
cases = {
    "plain": ("TRACE output: [[], [(4, 1)]]\nTRACE n: [1, 3]\nOUTPUT: [(4, 1)]", [[], [(4, 1)]], [1, 3], [(4, 1)]),
    "markdown": ("**TRACE output:** `[[], [(4, 1)]]`\n**TRACE n:** `[1, 3]`\n**OUTPUT:** `[(4, 1)]`", [[], [(4, 1)]], [1, 3], [(4, 1)]),
    "code fence": ("```\nTRACE output: [[], [(4, 1)]]\nTRACE n: [1, 3]\nOUTPUT: [(4, 1)]\n```", [[], [(4, 1)]], [1, 3], [(4, 1)]),
    "multiline list": ("TRACE output: [\n  [],\n  [(4, 1)]\n]\nTRACE n: [1, 3]\nOUTPUT: [(4, 1)]", [[], [(4, 1)]], [1, 3], [(4, 1)]),
    "arrows": ("TRACE output: [] -> [(4, 1)]\nTRACE n: 1 → 3\nOUTPUT: [(4, 1)]", [[], [(4, 1)]], [1, 3], [(4, 1)]),
    "explanation after": ("Let me think.\nTRACE output: [[], [(4, 1)]]\nTRACE n: [1, 3]\nOUTPUT: [(4, 1)] (sorted in reverse)", [[], [(4, 1)]], [1, 3], [(4, 1)]),
    "lowercase labels": ("trace output: [[], [(4, 1)]]\ntrace n: [1, 3]\noutput: [(4, 1)]", [[], [(4, 1)]], [1, 3], [(4, 1)]),
    "think block": ("<think>TRACE output: [9]</think>\nTRACE output: [[], [(4, 1)]]\nTRACE n: [1, 3]\nOUTPUT: [(4, 1)]", [[], [(4, 1)]], [1, 3], [(4, 1)]),
    "return value label": ("TRACE output: [[], [(4, 1)]]\nTRACE n: [1, 3]\nReturn value: [(4, 1)]", [[], [(4, 1)]], [1, 3], [(4, 1)]),
}
fails = 0
for name, (text, o, n, out) in cases.items():
    p = parse_mureco(text, V)
    ok = p["trace"]["output"] == o and p["trace"]["n"] == n and p["output"] == out
    fails += not ok
    print(f"{'ok  ' if ok else 'FAIL'} {name}: {p if not ok else ''}")
p = parse_mureco("I could not solve this.", V)
assert p["output_ok"] is False and p["trace"]["n"] is None
print("PARSER TESTS PASSED" if not fails else f"{fails} PARSER TESTS FAILED")
