from __future__ import annotations
import json
import os
import statistics
import matplotlib.pyplot as plt
from jssp import random_instance, lower_bound, gap_percent, tabu_search

CACHE = "shape_results.json"
SHAPES = [(6, 6), (10, 10), (15, 15), (15, 10), (20, 5)]

def load():
    return json.load(open(CACHE)) if os.path.exists(CACHE) else {}


def save(c):
    json.dump(c, open(CACHE, "w"))


def main(n_runs=20, instance_seed=42):
    c = load()
    rows = []
    for (nj, nm) in SHAPES:
        key = f"{nj}x{nm}"
        inst = random_instance(nj, nm, seed=instance_seed)
        lb = lower_bound(inst)
        if key in c and len(c[key]["vals"]) >= n_runs:
            print(f"{key} (cached)")
        else:
            print(f"{key} ...", flush=True)
            vals = [tabu_search(inst, max_iter=5000, tenure=12, seed=s)[1]
                    for s in range(n_runs)]
            c[key] = {"lb": lb, "vals": vals, "ratio": nj / nm}
            save(c)
        d = c[key]
        gaps = [gap_percent(v, d["lb"]) for v in d["vals"]]
        rows.append((key, d["ratio"], statistics.mean(gaps), statistics.stdev(gaps)))

    print(f"\n{'shape':>8}{'n/m':>6}{'gapLB mean%':>13}{'std':>8}")
    for key, ratio, gm, gs in rows:
        print(f"{key:>8}{ratio:>6.1f}{gm:>13.1f}{gs:>8.1f}")

    rows_sorted = sorted(rows, key=lambda r: r[1])
    labels = [r[0] for r in rows_sorted]
    gmeans = [r[2] for r in rows_sorted]
    gstds = [r[3] for r in rows_sorted]

    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    x = list(range(len(labels)))
    ax.bar(x, gmeans, yerr=gstds, color="#117A65", alpha=0.85,
           edgecolor="#0C5A4B", capsize=4, width=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{labels[i]}\n(n/m={rows_sorted[i][1]:.1f})" for i in range(len(labels))])
    ax.set_ylabel("Tabu gap to LB (%)  — 20 runs")
    ax.set_title("Tabu gap to lower bound by instance shape")
    ax.grid(True, axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig("shape.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    print("saved: shape.png")


if __name__ == "__main__":
    main()
