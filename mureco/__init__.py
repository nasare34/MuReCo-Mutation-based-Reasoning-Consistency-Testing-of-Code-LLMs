"""MuReCo: Mutation-based Reasoning Consistency testing of Code LLMs.

A prototype that extends MuCoCo (Chua, Lwin & Soremekun, EMNLP 2026):
it reuses MuCoCo's semantic-preserving mutation engine, then checks a
model's step-by-step reasoning trace (not only its final answer) against
real program execution, across equivalent versions of the same program.
"""
__version__ = "0.1.0"
