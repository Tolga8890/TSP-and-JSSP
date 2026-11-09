from __future__ import annotations
import json
import os
import statistics
import matplotlib.pyplot as plt
import random as _r
from jssp import (
    random_instance, lower_bound, gap_percent,
    local_search, iterated_local_search, simulated_annealing, tabu_search,
)

CACHE_FILE = "analysis_results.json"

ALGOS = [
    ("LS",   local_search,          {}),
    ("ILS",  iterated_local_search, {"n_iterations": 50}),
    ("SA",   simulated_annealing,   {"alpha": 0.95}),
    ("Tabu", tabu_search,           {"max_iter": 5000, "tenure": 12}),
]
COLORS = {"LS": "#D95F02", "ILS": "#1B4F72", "SA": "#7D3C98", "Tabu": "#117A65"}


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}


def save_cache(c):
    with open(CACHE_FILE, "w") as f:
        json.dump(c, f)


def main(n_jobs=10, n_machines=10, n_runs=30, instance_seed=42):
    inst = random_instance(n_jobs, n_machines, seed=instance_seed)
    lb = lower_bound(inst)
    cache = load_cache()

    for name, fn, kw in ALGOS:
        if name in cache and len(cache[name]) >= n_runs:
            print(f"{name} (cached)")
            continue
        print(f"running {name} ...", flush=True)
        cache[name] = [fn(inst, seed=s, **kw)[1] for s in range(n_runs)]
        save_cache(cache)

    results = {name: cache[name] for name, _, _ in ALGOS}
    best_found = min(min(v) for v in results.values())

    print(f"\n{inst.name}   LB={lb}   best-found={best_found}\n")
    print(f"{'Algo':<6}{'Mean':>9}{'Median':>9}{'Std':>8}{'Min':>7}"
          f"{'gapLB%':>9}{'gapBest%':>10}")
    for name, _, _ in ALGOS:
        v = results[name]
        m = statistics.mean(v)
        print(f"{name:<6}{m:>9.1f}{statistics.median(v):>9.1f}"
              f"{statistics.stdev(v):>8.1f}{min(v):>7d}"
              f"{gap_percent(m, lb):>9.1f}{gap_percent(m, best_found):>10.1f}")

    labels = [name for name, _, _ in ALGOS]
    data = [[gap_percent(x, best_found) for x in results[name]] for name in labels]
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    bp = ax.boxplot(data, tick_labels=labels, showmeans=True, meanline=True,
                    widths=0.55, patch_artist=True,
                    boxprops=dict(facecolor="#EDE7DA", edgecolor="#2C2A26", linewidth=1.2),
                    whiskerprops=dict(color="#2C2A26"),
                    capprops=dict(color="#2C2A26"),
                    medianprops=dict(color="#2C2A26", linewidth=1.8),
                    meanprops=dict(color="#B24A2A", linewidth=1.2, linestyle=":"),
                    flierprops=dict(marker="o", markersize=3, alpha=0.4))
    rng = _r.Random(0)
    for i, name in enumerate(labels, start=1):
        xs = [i + (rng.random() - 0.5) * 0.18 for _ in data[i - 1]]
        ax.scatter(xs, data[i - 1], s=14, color="#2C2A26", alpha=0.30, zorder=3)
    ax.set_ylabel("Gap to best-found (%)")
    ax.set_title(f"JSSP {n_jobs}x{n_machines} — solution quality over {n_runs} runs")
    ax.grid(True, axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig("analysis.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    print("\nsaved: analysis.png")


if __name__ == "__main__":
    main()
