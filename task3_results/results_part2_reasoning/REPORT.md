# MuReCo prototype results

## deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B  (20 CruxEval tasks)

| Measure | Value |
|---|---|
| Parsing: answers with no readable output | 49.2% (61/124) |
| Parsing: answers with all traces readable | 41.9% (52/124) |
| Original: answer accuracy | 20.0% (4/20) |
| Original: trace accuracy | 5.0% (1/20) |
| Original: right answer, wrong reasoning | 25.0% (1/4) |
| Single mutations: answer inconsistency (MuCoCo) | 51.7% (31/60) |
| Single mutations: reasoning inconsistency, answers agree (MuReCo) | 14.3% (1/7) |
| Pairs of mutations: answer inconsistency (MuCoCo) | 45.5% (20/44) |
| Pairs of mutations: reasoning inconsistency, answers agree (MuReCo) | 33.3% (1/3) |
| All mutants: answer inconsistency (MuCoCo) | 49.0% (51/104) |
| All mutants: reasoning inconsistency, answers agree (MuReCo) | 20.0% (2/10) |
| Hidden pair failures (pair fails, both singles pass) | 19.0% (4/21) |
| Noise: rerun flip rate on originals | 30.0% (6/20) |

| Variant | Pairs | Answer inc. | Reasoning inc. (answers agree) | Mutant trace acc. |
|---|---|---|---|---|
| constant_unfold | 7 | 57.1% (4/7) | 100.0% (1/1) | 0.0% (0/7) |
| for2while | 13 | 53.8% (7/13) | 0.0% (0/2) | 15.4% (2/13) |
| random | 20 | 50.0% (10/20) | 0.0% (0/1) | 5.0% (1/20) |
| sequential | 20 | 50.0% (10/20) | 0.0% (0/3) | 0.0% (0/20) |
| for2while+constant_unfold | 4 | 0.0% (0/4) | n/a | 0.0% (0/4) |
| random+constant_unfold | 7 | 57.1% (4/7) | 100.0% (1/1) | 0.0% (0/7) |
| random+for2while | 13 | 46.2% (6/13) | 0.0% (0/2) | 7.7% (1/13) |
| sequential+constant_unfold | 7 | 42.9% (3/7) | n/a | 14.3% (1/7) |
| sequential+for2while | 13 | 53.8% (7/13) | n/a | 0.0% (0/13) |

### Examples: answers agree, reasoning does not

### CruxEval_545 (sample_545), mutation: constant_unfold
Original program:
```python
def f(array):
    result = []
    index = 0
    while index < len(array):
        result.append(array.pop())
        index += 2
    return result
```
Mutated program (constant_unfold):
```python
def f(array):
    result = []
    index = 0
    while index < len(array):
        result.append(array.pop())
        index += 2 * 1
    return result
```
Call input: `[8, 8, -4, -9, 2, 8, -1, 8]`; expected output `[8, -1, 8]`

| | Answer | Trace |
|---|---|---|
| Ground truth | `[8, -1, 8]` | `{'result': ['[]', '[8]', '[8, -1]', '[8, -1, 8]'], 'index': ['0', '2', '4', '6']}` |
| Model on original | `'<return value>'` (incorrect) | `{'result': ['8', '-4', '2', '-1'], 'index': ['0', '2', '4', '6']}` |
| Model on mutant | `'<return value>'` (incorrect) | `{'result': ['8', '-1', '8'], 'index': ['0', '2', '4', '6', '8']}` |


### CruxEval_545 (sample_545), mutation: random+constant_unfold
Original program:
```python
def f(array):
    result = []
    index = 0
    while index < len(array):
        result.append(array.pop())
        index += 2
    return result
```
Mutated program (random+constant_unfold):
```python
def afZLcQ(gXwpbb):
    result = []
    index = 0
    while index < len(gXwpbb):
        result.append(gXwpbb.pop())
        index += 2 * 1
    return result
```
Call input: `[8, 8, -4, -9, 2, 8, -1, 8]`; expected output `[8, -1, 8]`

| | Answer | Trace |
|---|---|---|
| Ground truth | `[8, -1, 8]` | `{'result': ['[]', '[8]', '[8, -1]', '[8, -1, 8]'], 'index': ['0', '2', '4', '6']}` |
| Model on original | `'<return value>'` (incorrect) | `{'result': ['8', '-4', '2', '-1'], 'index': ['0', '2', '4', '6']}` |
| Model on mutant | `'<return value>'` (incorrect) | `{'result': ['8', '-4', '2', '-1'], 'index': ['0', '2', '4', '6', '8']}` |

