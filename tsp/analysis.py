from __future__ import annotations
import statistics
from tsp import (
    random_instance, distance_matrix,
    local_search, iterated_local_search,
    guided_local_search, simulated_annealing,
)


def run_many(algo, dist, n_runs=30, **kwargs):
    lengths = []
    for _ in range(n_runs):
        _, L = algo(dist, **kwargs)
        lengths.append(L)
    return lengths


def summarize(name, xs):
    return {
        "name": name,
        "mean": statistics.mean(xs),
        "median": statistics.median(xs),
        "std": statistics.stdev(xs) if len(xs) > 1 else 0.0,
        "min": min(xs),
        "max": max(xs),
    }


def print_table(rows):
    header = f"{'Algorithm':<10}{'Mean':>10}{'Median':>10}{'Std':>10}{'Min':>10}{'Max':>10}"
    print(header)
    for r in rows:
        print(f"{r['name']:<10}{r['mean']:>10.1f}{r['median']:>10.1f}"
              f"{r['std']:>10.1f}{r['min']:>10.1f}{r['max']:>10.1f}")


def save_boxplot(results, filename, n, n_runs):
    import matplotlib.pyplot as plt
    import random as _r

    labels = ["LS", "ILS", "GLS", "SA"]
    data = [results[k] for k in labels]

    fig, ax = plt.subplots(figsize=(7.5, 4.8))

    bp = ax.boxplot(
        data, tick_labels=labels, showmeans=True, meanline=True,
        widths=0.55, patch_artist=True,
        boxprops=dict(facecolor="#EDE7DA", edgecolor="#2C2A26", linewidth=1.2),
        whiskerprops=dict(color="#2C2A26", linewidth=1.0),
        capprops=dict(color="#2C2A26", linewidth=1.0),
        medianprops=dict(color="#2C2A26", linewidth=1.8),
        meanprops=dict(color="#B24A2A", linewidth=1.2, linestyle=":"),
        flierprops=dict(marker="o", markersize=3, markerfacecolor="#2C2A26",
                        markeredgecolor="none", alpha=0.4),
    )

    _rng = _r.Random(0)
    for i, xs in enumerate(data, start=1):
        jx = [i + (_rng.random() - 0.5) * 0.18 for _ in xs]
        ax.scatter(jx, xs, s=14, color="#2C2A26", alpha=0.35,
                   edgecolors="none", zorder=3)

    ax.set_ylabel("Tour length")
    ax.set_title(f"Tour length distribution over {n_runs} runs  (n = {n})")
    ax.grid(True, axis="y", alpha=0.25, linewidth=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color("#666")
    ax.spines["bottom"].set_color("#666")
    ax.tick_params(colors="#333")

    fig.tight_layout()
    fig.savefig(filename, dpi=160, bbox_inches="tight")
    plt.close(fig)


def main(n: int = 50, n_runs: int = 30, instance_seed: int | None = 42) -> None:
    coords = random_instance(n=n, seed=instance_seed)
    dist = distance_matrix(coords)

    print(f"TSP  n = {n}  runs per algorithm = {n_runs}")
    print()

    results = {}
    for name, algo, kwargs in [
        ("LS",  local_search,             {}),
        ("ILS", iterated_local_search,    {"n_iterations": 100}),
        ("GLS", guided_local_search,      {"n_iterations": 100, "alpha": 0.3}),
        ("SA",  simulated_annealing,      {"alpha": 0.995}),
    ]:
        print(f"  running {name} ...")
        results[name] = run_many(algo, dist, n_runs=n_runs, **kwargs)

    print()
    rows = [summarize(name, results[name]) for name in ("LS", "ILS", "GLS", "SA")]
    print_table(rows)

    save_boxplot(results, "analysis.png", n=n, n_runs=n_runs)
    print("\nsaved: analysis.png")


if __name__ == "__main__":
    main(n=50, n_runs=30)
