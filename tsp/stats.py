from __future__ import annotations
import json
import os
from scipy.stats import mannwhitneyu

HERE = os.path.dirname(os.path.abspath(__file__))


def load(name):
    with open(os.path.join(HERE, name)) as f:
        return json.load(f)


def a12(x, y):
    """Probability that a random run of x gives a shorter tour than a random run of y."""
    wins = 0.0
    for xi in x:
        for yi in y:
            if xi < yi:
                wins += 1.0
            elif xi == yi:
                wins += 0.5
    return wins / (len(x) * len(y))


def holm(pvalues):
    """Holm–Bonferroni adjusted p-values, returned in the original order."""
    m = len(pvalues)
    order = sorted(range(m), key=lambda i: pvalues[i])
    adjusted = [0.0] * m
    running_max = 0.0
    for rank, i in enumerate(order):
        p_adj = min(1.0, (m - rank) * pvalues[i])
        running_max = max(running_max, p_adj)
        adjusted[i] = running_max
    return adjusted


def main():
    scale = load("scale_results.json")
    param = load("param_results.json")

    comparisons = [
        ("SA vs ILS, n=50",          scale["SA"]["50"],     scale["ILS"]["50"]),
        ("SA vs ILS, n=100",         scale["SA"]["100"],    scale["ILS"]["100"]),
        ("SA vs ILS, n=200",         scale["SA"]["200"],    scale["ILS"]["200"]),
        ("SA alpha 0.995 vs 0.99",   param["SA"]["0.995"],  param["SA"]["0.99"]),
        ("ILS iter 200 vs 100",      param["ILS"]["200"],   param["ILS"]["100"]),
        ("ILS iter 400 vs 200",      param["ILS"]["400"],   param["ILS"]["200"]),
        ("GLS alpha 0.5 vs 0.3",     param["GLS"]["0.5"],   param["GLS"]["0.3"]),
        ("GLS alpha 0.5 vs 1.0",     param["GLS"]["0.5"],   param["GLS"]["1.0"]),
        ("GLS alpha 1.0 vs 0.3",     param["GLS"]["1.0"],   param["GLS"]["0.3"]),
    ]

    raw = [mannwhitneyu(x, y, alternative="two-sided").pvalue for _, x, y in comparisons]
    adjusted = holm(raw)

    print("Mann-Whitney U (two-sided), A12 effect size, Holm correction over all rows.")
    print("A12 = P(first gives a shorter tour than second); 0.5 means no difference.\n")
    print(f"{'Comparison':<26}{'p':>10}{'p (Holm)':>11}{'A12':>7}")
    for (label, x, y), p, p_h in zip(comparisons, raw, adjusted):
        print(f"{label:<26}{p:>10.4f}{p_h:>11.4f}{a12(x, y):>7.2f}")


if __name__ == "__main__":
    main()