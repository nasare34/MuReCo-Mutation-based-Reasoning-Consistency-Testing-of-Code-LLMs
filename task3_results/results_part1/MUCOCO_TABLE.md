## MuCoCo reproduction: Qwen/Qwen2.5-Coder-14B-Instruct, CruxEval output prediction, 50 tasks

| Mutation type | Inconsistency % | Mutant accuracy % |
|---|---|---|
| Lexical | 13.01 (16/123) | 56.10 (69/123) |
| Syntactic | 10.53 (4/38) | 47.37 (18/38) |
| Logical | 24.07 (13/54) | 40.74 (22/54) |
| All | 15.35 (33/215) | 50.70 (109/215) |

Original-program accuracy: 56.00% (28/50); invalid answers: originals 4/50, mutants 21/215

| Operator | Inconsistency % | Mutant accuracy % |
|---|---|---|
| random | 18.00 (9/50) | 60.00 (30/50) |
| sequential | 14.00 (7/50) | 60.00 (30/50) |
| literal_format | 0.00 (0/23) | 39.13 (9/23) |
| for2while | 10.53 (2/19) | 42.11 (8/19) |
| for2enumerate | 10.53 (2/19) | 52.63 (10/19) |
| demorgan | 0.00 (0/4) | 75.00 (3/4) |
| boolean_literal | 0.00 (0/4) | 75.00 (3/4) |
| commutative_reorder | 14.29 (1/7) | 57.14 (4/7) |
| constant_unfold | 23.08 (3/13) | 30.77 (4/13) |
| constant_unfold_add | 38.46 (5/13) | 23.08 (3/13) |
| constant_unfold_mult | 30.77 (4/13) | 38.46 (5/13) |