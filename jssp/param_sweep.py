from __future__ import annotations
import json
import os
import random as _r
import statistics
import matplotlib.pyplot as plt
from jssp import (
    random_instance, lower_bound, gap_percent,
    simulated_annealing, tabu_search,
)

CACHE = "param_results.json"
TENURES = [3, 5, 8, 12, 20, 40]
SA_ALPHAS = [0.90, 0.95, 0.99]


def load():
    if os.path.exists(CACHE):
        return json.load(open(CACHE))
    return {"tenure": {}, "sa_alpha": {}}


def save(c):
    json.dump(c, open(CACHE, "w"))


def plot(param_values, data_by_value, xlabel, title, filename, color, ref):
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    x = list(range(len(param_values)))
    means = [statistics.mean(data_by_value[str(v)]) for v in param_values]
    stds = [statistics.stdev(data_by_value[str(v)]) for v in param_values]
    gmeans = [gap_percent(m, ref) for m in means]
    ax.errorbar(x, gmeans, yerr=[s / ref * 100 for s in stds], marker="o",
                markersize=7, linewidth=1.8, capsize=4, color=color, zorder=4,
                label="mean ± std")
    rng = _r.Random(0)
    for i, v in enumerate(param_values):
        pts = [gap_percent(z, ref) for z in data_by_value[str(v)]]
        xs = [i + (rng.random() - 0.5) * 0.18 for _ in pts]
        ax.scatter(xs, pts, s=13, color="#2C2A26", alpha=0.28, zorder=2)
    ax.set_xticks(x)
    ax.set_xticklabels([str(v) for v in param_values])
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Gap to best-found (%)")
    ax.set_title(title)
    ax.grid(True, axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(filename, dpi=160, bbox_inches="tight")
    plt.close(fig)


def main(n_jobs=10, n_machines=10, n_runs=30, instance_seed=42):
    inst = random_instance(n_jobs, n_machines, seed=instance_seed)
    lb = lower_bound(inst)
    c = load()

    print("Tabu tenure sweep:")
    for t in TENURES:
        if str(t) in c["tenure"] and len(c["tenure"][str(t)]) >= n_runs:
            print(f"  tenure={t} (cached)"); continue
        print(f"  tenure={t} ...", flush=True)
        c["tenure"][str(t)] = [tabu_search(inst, max_iter=5000, tenure=t, seed=s)[1]
                               for s in range(n_runs)]
        save(c)

    print("SA alpha sweep:")
    for a in SA_ALPHAS:
        if str(a) in c["sa_alpha"] and len(c["sa_alpha"][str(a)]) >= n_runs:
            print(f"  alpha={a} (cached)"); continue
        print(f"  alpha={a} ...", flush=True)
        c["sa_alpha"][str(a)] = [simulated_annealing(inst, alpha=a, seed=s)[1]
                                 for s in range(n_runs)]
        save(c)

    allvals = [x for d in c["tenure"].values() for x in d] + \
              [x for d in c["sa_alpha"].values() for x in d]
    best_found = min(allvals)

    plot(TENURES, c["tenure"], "tenure (tabu list length)",
         f"Tabu — effect of tenure ({n_jobs}x{n_machines}, 30 runs)",
         "param_tenure.png", "#117A65", best_found)
    plot(SA_ALPHAS, c["sa_alpha"], "alpha (cooling ratio)",
         f"SA — effect of cooling rate ({n_jobs}x{n_machines}, 30 runs)",
         "param_sa.png", "#7D3C98", best_found)
    print(f"\nbest-found={best_found}")
    print("saved: param_tenure.png, param_sa.png")


if __name__ == "__main__":
    main()
