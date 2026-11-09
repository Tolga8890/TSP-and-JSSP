from __future__ import annotations
import json
import os
import statistics
import matplotlib.pyplot as plt
import random as _r
from jssp import (
    random_instance, lower_bound, gap_percent,
    local_search, local_search_n5, tabu_search,
)

CACHE = "neighborhood_results.json"
METHODS = [
    ("LS(swap)", local_search,    {}),
    ("LS(N5)",   local_search_n5, {}),
    ("Tabu(N5)", tabu_search,     {"max_iter": 5000, "tenure": 12}),
]
COLORS = {"LS(swap)": "#D95F02", "LS(N5)": "#9BB8AC", "Tabu(N5)": "#117A65"}


def load():
    return json.load(open(CACHE)) if os.path.exists(CACHE) else {}


def save(c):
    json.dump(c, open(CACHE, "w"))


def main(n_jobs=10, n_machines=10, n_runs=20, instance_seed=42):
    inst = random_instance(n_jobs, n_machines, seed=instance_seed)
    lb = lower_bound(inst)
    c = load()
    for name, fn, kw in METHODS:
        if name in c and len(c[name]) >= n_runs:
            print(f"{name} (cached)"); continue
        print(f"{name} ...", flush=True)
        c[name] = [fn(inst, seed=s, **kw)[1] for s in range(n_runs)]
        save(c)

    best = min(min(v) for v in c.values())
    print(f"\n{inst.name}  LB={lb}  best-found={best}\n")
    print(f"{'method':<10}{'mean':>9}{'gapLB%':>9}{'gapBest%':>10}")
    for name, _, _ in METHODS:
        m = statistics.mean(c[name])
        print(f"{name:<10}{m:>9.1f}{gap_percent(m, lb):>9.1f}{gap_percent(m, best):>10.1f}")

    labels = [n for n, _, _ in METHODS]
    data = [[gap_percent(x, best) for x in c[name]] for name in labels]
    fig, ax = plt.subplots(figsize=(7.0, 4.6))
    bp = ax.boxplot(data, tick_labels=labels, widths=0.55, patch_artist=True,
                    medianprops=dict(color="#2C2A26", linewidth=1.6),
                    flierprops=dict(marker="o", markersize=3, alpha=0.4))
    for patch, name in zip(bp["boxes"], labels):
        patch.set(facecolor=COLORS[name], alpha=0.55, edgecolor="#2C2A26")
    rng = _r.Random(0)
    for i, name in enumerate(labels, start=1):
        xs = [i + (rng.random() - 0.5) * 0.16 for _ in data[i - 1]]
        ax.scatter(xs, data[i - 1], s=13, color="#2C2A26", alpha=0.3, zorder=3)
    ax.set_ylabel("Gap to best-found (%)")
    ax.set_title(f"Neighborhood × search — JSSP {n_jobs}x{n_machines}, {n_runs} runs")
    ax.grid(True, axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig("neighborhood.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    print("saved: neighborhood.png")


if __name__ == "__main__":
    main()
