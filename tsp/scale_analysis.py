from __future__ import annotations
import json
import os
import statistics
import matplotlib.pyplot as plt
from tsp import (
    random_instance, distance_matrix,
    local_search, iterated_local_search,
    guided_local_search, simulated_annealing,
)

CACHE_FILE = "scale_results.json"


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)


ALGOS = [
    ("LS",  local_search,          {}),
    ("ILS", iterated_local_search, {"n_iterations": 100}),
    ("GLS", guided_local_search,   {"n_iterations": 100, "alpha": 0.3}),
    ("SA",  simulated_annealing,   {"alpha": 0.995}),
]

COLORS = {"LS": "#D95F02", "ILS": "#1B4F72", "GLS": "#117A65", "SA": "#7D3C98"}


def run_many(algo, dist, n_runs=30, **kwargs):
    return [algo(dist, **kwargs)[1] for _ in range(n_runs)]


def main(sizes=(50, 100, 200), n_runs=30, instance_seed=42):
    cache = load_cache()

    for n in sizes:
        coords = random_instance(n=n, seed=instance_seed)
        dist = distance_matrix(coords)
        print(f"\nn = {n}")
        for name, algo, kwargs in ALGOS:
            key_algo = cache.setdefault(name, {})
            if str(n) in key_algo and len(key_algo[str(n)]) >= n_runs:
                print(f"  {name} ... (cached)")
                continue
            print(f"  {name} ...", flush=True)
            key_algo[str(n)] = run_many(algo, dist, n_runs=n_runs, **kwargs)
            save_cache(cache)

    results = {name: {int(n_): xs for n_, xs in cache[name].items()} for name, _, _ in ALGOS}

    print(f"\n{'n':<6}", end="")
    for name, _, _ in ALGOS:
        print(f"{name+' mean':>14}{name+' std':>12}", end="")
    print()
    for n in sizes:
        print(f"{n:<6}", end="")
        for name, _, _ in ALGOS:
            xs = results[name][n]
            print(f"{statistics.mean(xs):>14.1f}{statistics.stdev(xs):>12.1f}", end="")
        print()

    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    for name, _, _ in ALGOS:
        means = [statistics.mean(results[name][n]) for n in sizes]
        stds = [statistics.stdev(results[name][n]) for n in sizes]
        ax.errorbar(sizes, means, yerr=stds,
                    marker="o", markersize=6, linewidth=1.6,
                    capsize=4, color=COLORS[name], label=name)

    ax.set_xlabel("Instance size (n)")
    ax.set_ylabel("Mean tour length  (± std over 30 runs)")
    ax.set_title("Scaling behavior across instance sizes")
    ax.set_xticks(list(sizes))
    ax.grid(True, alpha=0.25, linewidth=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color("#666")
    ax.spines["bottom"].set_color("#666")
    ax.tick_params(colors="#333")
    ax.legend(frameon=False, loc="upper left")

    fig.tight_layout()
    fig.savefig("scale.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    print("\nsaved: scale.png")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        sizes = tuple(int(x) for x in sys.argv[1:])
        main(sizes=sizes)
    else:
        main()
