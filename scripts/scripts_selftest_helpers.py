"""Shared helper: corrupt one trace step while keeping the output correct."""
import re


def corrupt(ans):
    lines = ans.split("\n")
    m = re.match(r"(TRACE \S+: )\[(.*)\]$", lines[0])
    parts = [p.strip() for p in re.split(r",\s(?![^\[\(\{]*[\]\)\}])", m.group(2))]
    if len(parts) >= 3:
        del parts[len(parts) // 2]
    else:
        parts = parts[1:]
    lines[0] = m.group(1) + "[" + ", ".join(parts) + "]"
    return "\n".join(lines)
