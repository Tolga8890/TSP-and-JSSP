from __future__ import annotations
import json
import os
import statistics
from scipy.stats import mannwhitneyu

HERE = os.path.dirname(os.path.abspath(__file__))


def load(name):
    with open(os.path.join(HERE, name)) as f:
        return json.load(f)


def a12(x, y):
    """Probability that a random run of x gives a shorter makespan than a random run of y."""
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


def significance_table(analysis, neigh, param):
    comparisons = [
        ("Tabu vs ILS",              analysis["Tabu"],          analysis["ILS"]),
        ("ILS vs SA (alpha 0.95)",   analysis["ILS"],           analysis["SA"]),
        ("SA (alpha 0.99) vs ILS",   param["sa_alpha"]["0.99"], analysis["ILS"]),
        ("LS(swap) vs LS(N5)",       neigh["LS(swap)"],         neigh["LS(N5)"]),
        ("Tabu(N5) vs LS(N5)",       neigh["Tabu(N5)"],         neigh["LS(N5)"]),
        ("tenure 5 vs 3",            param["tenure"]["5"],      param["tenure"]["3"]),
        ("tenure 8 vs 5",            param["tenure"]["8"],      param["tenure"]["5"]),
        ("tenure 12 vs 8",           param["tenure"]["12"],     param["tenure"]["8"]),
        ("tenure 12 vs 20",          param["tenure"]["12"],     param["tenure"]["20"]),
        ("tenure 20 vs 40",          param["tenure"]["20"],     param["tenure"]["40"]),
        ("SA alpha 0.95 vs 0.90",    param["sa_alpha"]["0.95"], param["sa_alpha"]["0.9"]),
        ("SA alpha 0.99 vs 0.95",    param["sa_alpha"]["0.99"], param["sa_alpha"]["0.95"]),
    ]
    raw = [mannwhitneyu(x, y, alternative="two-sided").pvalue for _, x, y in comparisons]
    adjusted = holm(raw)

    print("Mann-Whitney U (two-sided), A12 effect size, Holm correction over all rows.")
    print("A12 = P(first gives a shorter makespan than second); 0.5 means no difference.\n")
    print(f"{'Comparison':<26}{'p':>10}{'p (Holm)':>11}{'A12':>7}")
    for (label, x, y), p, p_h in zip(comparisons, raw, adjusted):
        print(f"{label:<26}{p:>10.4f}{p_h:>11.4f}{a12(x, y):>7.2f}")


def shape_table(shape):
    print("\nShape study: best value found, how often it was reached, and spread.\n")
    print(f"{'shape':<7}{'n/m':>5}{'LB':>6}{'best':>6}{'hits':>7}"
          f"{'gap LB (best) %':>17}{'mean gap best %':>17}{'std':>7}")
    for key, d in shape.items():
        vals, lb = d["vals"], d["lb"]
        best = min(vals)
        hits = f"{vals.count(best)}/{len(vals)}"
        gap_lb = (best - lb) / lb * 100
        gap_best = statistics.mean((v - best) / best * 100 for v in vals)
        print(f"{key:<7}{d['ratio']:>5.1f}{lb:>6}{best:>6}{hits:>7}"
              f"{gap_lb:>17.1f}{gap_best:>17.2f}{statistics.stdev(vals):>7.1f}")


def main():
    analysis = load("analysis_results.json")
    neigh = load("neighborhood_results.json")
    param = load("param_results.json")
    shape = load("shape_results.json")
    significance_table(analysis, neigh, param)
    shape_table(shape)


if __name__ == "__main__":
    main()