# MuReCo prototype results

## Qwen/Qwen2.5-Coder-1.5B-Instruct  (60 CruxEval tasks)

| Measure | Value |
|---|---|
| Parsing: answers with no readable output | 62.7% (222/354) |
| Parsing: answers with all traces readable | 40.4% (143/354) |
| Original: answer accuracy | 18.3% (11/60) |
| Original: trace accuracy | 3.3% (2/60) |
| Original: right answer, wrong reasoning | 81.8% (9/11) |
| Single mutations: answer inconsistency (MuCoCo) | 50.3% (88/175) |
| Single mutations: reasoning inconsistency, answers agree (MuReCo) | 34.8% (8/23) |
| Pairs of mutations: answer inconsistency (MuCoCo) | 53.8% (64/119) |
| Pairs of mutations: reasoning inconsistency, answers agree (MuReCo) | 11.1% (1/9) |
| All mutants: answer inconsistency (MuCoCo) | 51.7% (152/294) |
| All mutants: reasoning inconsistency, answers agree (MuReCo) | 28.1% (9/32) |
| Hidden pair failures (pair fails, both singles pass) | 7.7% (5/65) |
| Noise: rerun flip rate on originals | 7.5% (9/120) |

| Variant | Pairs | Answer inc. | Reasoning inc. (answers agree) | Mutant trace acc. |
|---|---|---|---|---|
| constant_unfold | 14 | 50.0% (7/14) | 0.0% (0/1) | 0.0% (0/14) |
| demorgan | 2 | 100.0% (2/2) | n/a | 0.0% (0/2) |
| for2while | 39 | 46.2% (18/39) | 66.7% (2/3) | 2.6% (1/39) |
| random | 60 | 48.3% (29/60) | 40.0% (4/10) | 8.3% (5/60) |
| sequential | 60 | 53.3% (32/60) | 22.2% (2/9) | 5.0% (3/60) |
| for2while+constant_unfold | 7 | 28.6% (2/7) | n/a | 0.0% (0/7) |
| for2while+demorgan | 2 | 100.0% (2/2) | n/a | 0.0% (0/2) |
| random+constant_unfold | 14 | 78.6% (11/14) | n/a | 0.0% (0/14) |
| random+demorgan | 2 | 100.0% (2/2) | n/a | 0.0% (0/2) |
| random+for2while | 39 | 46.2% (18/39) | 0.0% (0/3) | 7.7% (3/39) |
| sequential+constant_unfold | 14 | 78.6% (11/14) | n/a | 7.1% (1/14) |
| sequential+demorgan | 2 | 0.0% (0/2) | 50.0% (1/2) | 0.0% (0/2) |
| sequential+for2while | 39 | 46.2% (18/39) | 0.0% (0/4) | 10.3% (4/39) |

### Examples: answers agree, reasoning does not

### CruxEval_702 (sample_702), mutation: random
Original program:
```python
def f(nums):
    count = len(nums)
    for i in range(len(nums) - 1, -1, -1):
        nums.insert(i, nums.pop(0))
    return nums
```
Mutated program (random):
```python
def afZLcQ(gXwpbb):
    count = len(gXwpbb)
    for i in range(len(gXwpbb) - 1, -1, -1):
        gXwpbb.insert(i, gXwpbb.pop(0))
    return gXwpbb
```
Call input: `[0, -5, -4]`; expected output `[-4, -5, 0]`

| | Answer | Trace |
|---|---|---|
| Ground truth | `[-4, -5, 0]` | `{'i': ['2', '1', '0'], 'nums': ['[0, -5, -4]', '[-5, -4, 0]', '[-4, -5, 0]']}` |
| Model on original | `None` (invalid) | `{'i': ['2', '1', '0'], 'nums': ['0', '-5', '-4', '-5', '-4']}` |
| Model on mutant | `None` (invalid) | `{'i': ['2', '1', '0'], 'nums': ['0', '-5', '0']}` |


### CruxEval_702 (sample_702), mutation: for2while
Original program:
```python
def f(nums):
    count = len(nums)
    for i in range(len(nums) - 1, -1, -1):
        nums.insert(i, nums.pop(0))
    return nums
```
Mutated program (for2while):
```python
def f(nums):
    count = len(nums)
    loop_var0 = len(nums) - 1
    while loop_var0 > -1:
        i = loop_var0
        nums.insert(i, nums.pop(0))
        loop_var0 += -1
    return nums
```
Call input: `[0, -5, -4]`; expected output `[-4, -5, 0]`

| | Answer | Trace |
|---|---|---|
| Ground truth | `[-4, -5, 0]` | `{'i': ['2', '1', '0'], 'nums': ['[0, -5, -4]', '[-5, -4, 0]', '[-4, -5, 0]']}` |
| Model on original | `None` (invalid) | `{'i': ['2', '1', '0'], 'nums': ['0', '-5', '-4', '-5', '-4']}` |
| Model on mutant | `None` (invalid) | `{'i': ['2', '1', '0'], 'nums': ['0', '-5', '-4', '0']}` |


### CruxEval_614 (sample_614), mutation: random
Original program:
```python
def f(text, substr, occ):
    n = 0
    while True:
        i = text.rfind(substr)
        if i == -1:
            break
        elif n == occ:
            return i
        else:
            n += 1
            text = text[:i]
    return -1
```
Mutated program (random):
```python
def eMRfGLcrJePt(wrpPmDHQbGea, jTEQykdeLF, eJnjbwX):
    n = 0
    while True:
        i = wrpPmDHQbGea.rfind(jTEQykdeLF)
        if i == -1:
            break
        elif n == eJnjbwX:
            return i
        else:
            n += 1
            wrpPmDHQbGea = wrpPmDHQbGea[:i]
    return -1
```
Call input: `'zjegiymjc', 'j', 2`; expected output `-1`

| | Answer | Trace |
|---|---|---|
| Ground truth | `-1` | `{'n': ['0', '1', '2'], 'i': ['7', '1', '-1']}` |
| Model on original | `-1` (correct) | `{'n': ['0', '1', '2'], 'i': ['7', '4', '-1']}` |
| Model on mutant | `-1` (correct) | `{'n': ['0'], 'i': ['-1']}` |


## Qwen/Qwen2.5-Coder-7B-Instruct  (60 CruxEval tasks)

| Measure | Value |
|---|---|
| Parsing: answers with no readable output | 0.8% (3/354) |
| Parsing: answers with all traces readable | 98.9% (350/354) |
| Original: answer accuracy | 38.3% (23/60) |
| Original: trace accuracy | 16.7% (10/60) |
| Original: right answer, wrong reasoning | 60.9% (14/23) |
| Single mutations: answer inconsistency (MuCoCo) | 33.1% (58/175) |
| Single mutations: reasoning inconsistency, answers agree (MuReCo) | 20.9% (24/115) |
| Pairs of mutations: answer inconsistency (MuCoCo) | 34.5% (41/119) |
| Pairs of mutations: reasoning inconsistency, answers agree (MuReCo) | 28.9% (22/76) |
| All mutants: answer inconsistency (MuCoCo) | 33.7% (99/294) |
| All mutants: reasoning inconsistency, answers agree (MuReCo) | 24.1% (46/191) |
| Hidden pair failures (pair fails, both singles pass) | 9.5% (6/63) |
| Noise: rerun flip rate on originals | 1.7% (2/120) |

| Variant | Pairs | Answer inc. | Reasoning inc. (answers agree) | Mutant trace acc. |
|---|---|---|---|---|
| constant_unfold | 14 | 42.9% (6/14) | 25.0% (2/8) | 7.1% (1/14) |
| demorgan | 2 | 0.0% (0/2) | 100.0% (2/2) | 0.0% (0/2) |
| for2while | 39 | 25.6% (10/39) | 25.0% (7/28) | 17.9% (7/39) |
| random | 60 | 40.0% (24/60) | 13.9% (5/36) | 20.0% (12/60) |
| sequential | 60 | 30.0% (18/60) | 19.5% (8/41) | 18.3% (11/60) |
| for2while+constant_unfold | 7 | 28.6% (2/7) | 60.0% (3/5) | 0.0% (0/7) |
| for2while+demorgan | 2 | 0.0% (0/2) | 100.0% (2/2) | 0.0% (0/2) |
| random+constant_unfold | 14 | 35.7% (5/14) | 22.2% (2/9) | 7.1% (1/14) |
| random+demorgan | 2 | 0.0% (0/2) | 100.0% (2/2) | 0.0% (0/2) |
| random+for2while | 39 | 33.3% (13/39) | 24.0% (6/25) | 17.9% (7/39) |
| sequential+constant_unfold | 14 | 42.9% (6/14) | 25.0% (2/8) | 7.1% (1/14) |
| sequential+demorgan | 2 | 0.0% (0/2) | 50.0% (1/2) | 0.0% (0/2) |
| sequential+for2while | 39 | 38.5% (15/39) | 17.4% (4/23) | 17.9% (7/39) |

### Examples: answers agree, reasoning does not

### CruxEval_244 (sample_244), mutation: for2while
Original program:
```python
def f(text, symbols):
    count = 0
    if symbols:
        for i in symbols:
            count += 1
        text = text * count
    return text.rjust(len(text) + count*2)[:-2]
```
Mutated program (for2while):
```python
def f(text, symbols):
    count = 0
    if symbols:
        loop_var0 = 0
        while loop_var0 < len(symbols):
            i = symbols[loop_var0]
            count += 1
            loop_var0 += 1
        text = text * count
    return text.rjust(len(text) + count * 2)[:-2]
```
Call input: `'', 'BC1ty'`; expected output `'        '`

| | Answer | Trace |
|---|---|---|
| Ground truth | `'        '` | `{'count': ['0', '1', '2', '3', '4', '5'], 'i': ["'B'", "'C'", "'1'", "'t'", "'y'"]}` |
| Model on original | `''` (incorrect) | `{'count': ['0', '3'], 'i': ["'B'", "'C'", "'1'"]}` |
| Model on mutant | `''` (incorrect) | `{'count': ['0', '1', '2', '3'], 'i': ["'B'", "'C'", "'1'", "'t'"]}` |


### CruxEval_244 (sample_244), mutation: sequential+constant_unfold
Original program:
```python
def f(text, symbols):
    count = 0
    if symbols:
        for i in symbols:
            count += 1
        text = text * count
    return text.rjust(len(text) + count*2)[:-2]
```
Mutated program (sequential+constant_unfold):
```python
def generic_function1(var1, var2):
    count = 0
    if var2:
        for i in var2:
            count += 1
        var1 = var1 * count
    return var1.rjust(len(var1) + count * (2 * 1))[:-(2 * 1)]
```
Call input: `'', 'BC1ty'`; expected output `'        '`

| | Answer | Trace |
|---|---|---|
| Ground truth | `'        '` | `{'count': ['0', '1', '2', '3', '4', '5'], 'i': ["'B'", "'C'", "'1'", "'t'", "'y'"]}` |
| Model on original | `''` (incorrect) | `{'count': ['0', '3'], 'i': ["'B'", "'C'", "'1'"]}` |
| Model on mutant | `''` (incorrect) | `{'count': ['0', '1', '2'], 'i': ["'B'", "'C'", "'1'"]}` |


### CruxEval_244 (sample_244), mutation: for2while+constant_unfold
Original program:
```python
def f(text, symbols):
    count = 0
    if symbols:
        for i in symbols:
            count += 1
        text = text * count
    return text.rjust(len(text) + count*2)[:-2]
```
Mutated program (for2while+constant_unfold):
```python
def f(text, symbols):
    count = 0
    if symbols:
        loop_var0 = 0
        while loop_var0 < len(symbols):
            i = symbols[loop_var0]
            count += 1
            loop_var0 += 1
        text = text * count
    return text.rjust(len(text) + count * (2 * 1))[:-(2 * 1)]
```
Call input: `'', 'BC1ty'`; expected output `'        '`

| | Answer | Trace |
|---|---|---|
| Ground truth | `'        '` | `{'count': ['0', '1', '2', '3', '4', '5'], 'i': ["'B'", "'C'", "'1'", "'t'", "'y'"]}` |
| Model on original | `''` (incorrect) | `{'count': ['0', '3'], 'i': ["'B'", "'C'", "'1'"]}` |
| Model on mutant | `''` (incorrect) | `{'count': ['0', '1', '2', '3'], 'i': ["'B'", "'C'", "'1'", "'t'"]}` |

