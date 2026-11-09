from __future__ import annotations
import json
import os
import random as _r
import statistics
import matplotlib.pyplot as plt
from tsp import (
    random_instance, distance_matrix,
    iterated_local_search, guided_local_search, simulated_annealing,
)

CACHE_FILE = "param_results.json"

SA_ALPHAS  = [0.90, 0.95, 0.99, 0.995]
ILS_ITERS  = [25, 50, 100, 200, 400]
GLS_ALPHAS = [0.05, 0.1, 0.3, 0.5, 1.0]


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {"SA": {}, "ILS": {}, "GLS": {}}


def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)


def sweep(algo, dist, param_name, param_values, n_runs, cache_bucket, extra_kwargs=None):
    extra_kwargs = extra_kwargs or {}
    for v in param_values:
        key = str(v)
        if key in cache_bucket and len(cache_bucket[key]) >= n_runs:
            print(f"    {param_name}={v} (cached)")
            continue
        print(f"    {param_name}={v} ...", flush=True)
        kwargs = {param_name: v, **extra_kwargs}
        cache_bucket[key] = [algo(dist, **kwargs)[1] for _ in range(n_runs)]
        save_cache_global(cache_bucket)


_full_cache = None
def save_cache_global(_):
    if _full_cache is not None:
        save_cache(_full_cache)


def plot_sweep(param_values, lengths_per_value, param_label, title, filename, color):
    fig, ax = plt.subplots(figsize=(7.0, 4.6))

    means = [statistics.mean(lengths_per_value[str(v)]) for v in param_values]
    stds = [statistics.stdev(lengths_per_value[str(v)]) for v in param_values]

    x = list(range(len(param_values)))
    ax.errorbar(x, means, yerr=stds, marker="o", markersize=7,
                linewidth=1.8, capsize=4, color=color, label="mean ± std", zorder=4)

    _rng = _r.Random(0)
    for i, v in enumerate(param_values):
        xs_pts = [i + (_rng.random() - 0.5) * 0.18 for _ in lengths_per_value[str(v)]]
        ax.scatter(xs_pts, lengths_per_value[str(v)], s=14,
                   color="#2C2A26", alpha=0.30, edgecolors="none", zorder=2)

    ax.set_xticks(x)
    ax.set_xticklabels([str(v) for v in param_values])
    ax.set_xlabel(param_label)
    ax.set_ylabel("Tour length  (30 runs)")
    ax.set_title(title)
    ax.grid(True, axis="y", alpha=0.25, linewidth=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color("#666")
    ax.spines["bottom"].set_color("#666")
    ax.tick_params(colors="#333")
    ax.legend(frameon=False, loc="best")

    fig.tight_layout()
    fig.savefig(filename, dpi=160, bbox_inches="tight")
    plt.close(fig)


def main(n=100, n_runs=30, instance_seed=42):
    global _full_cache
    _full_cache = load_cache()

    coords = random_instance(n=n, seed=instance_seed)
    dist = distance_matrix(coords)

    print(f"Parameter sweep at n = {n}, runs per setting = {n_runs}\n")

    print("  SA (alpha cooling):")
    sweep(simulated_annealing, dist, "alpha", SA_ALPHAS, n_runs,
          _full_cache["SA"])

    print("\n  ILS (n_iterations):")
    sweep(iterated_local_search, dist, "n_iterations", ILS_ITERS, n_runs,
          _full_cache["ILS"])

    print("\n  GLS (alpha penalty):")
    sweep(guided_local_search, dist, "alpha", GLS_ALPHAS, n_runs,
          _full_cache["GLS"], extra_kwargs={"n_iterations": 100})

    plot_sweep(SA_ALPHAS, _full_cache["SA"],
               "alpha (cooling ratio)",
               "SA — effect of cooling rate on tour length (n=100)",
               "param_sa.png", "#7D3C98")
    plot_sweep(ILS_ITERS, _full_cache["ILS"],
               "n_iterations",
               "ILS — effect of iteration budget on tour length (n=100)",
               "param_ils.png", "#1B4F72")
    plot_sweep(GLS_ALPHAS, _full_cache["GLS"],
               "alpha (penalty scale)",
               "GLS — effect of penalty scale on tour length (n=100)",
               "param_gls.png", "#117A65")

    print("\nsaved: param_sa.png, param_ils.png, param_gls.png")


if __name__ == "__main__":
    main()
