from __future__ import annotations
import json
import os
import matplotlib.pyplot as plt
from jssp import (
    random_instance, lower_bound, gap_percent,
    local_search, perm_to_mseq, tabu_search, draw_gantt_mseq,
)


def main(n_jobs=10, n_machines=10, instance_seed=42):
    inst = random_instance(n_jobs, n_machines, seed=instance_seed)
    lb = lower_bound(inst)

    perm, ls_ms = local_search(inst, seed=3)
    ls_mseq = perm_to_mseq(perm, inst)

    if os.path.exists("best_solution.json"):
        d = json.load(open("best_solution.json"))
        best_mseq, best_ms = d["mseq"], d["ms"]
    else:
        best_mseq, best_ms = tabu_search(inst, max_iter=5000, tenure=12, seed=3)
        with open("best_solution.json", "w") as f:
            json.dump({"mseq": best_mseq, "ms": best_ms}, f)

    fig, axes = plt.subplots(1, 2, figsize=(15, 0.45 * n_machines + 1.6))
    draw_gantt_mseq(inst, ls_mseq, None,
                    title=f"LS (swap) — makespan {ls_ms}  (gap LB {gap_percent(ls_ms, lb):.0f}%)",
                    ax=axes[0])
    draw_gantt_mseq(inst, best_mseq, None,
                    title=f"Tabu (N5) best — makespan {best_ms}  (gap LB {gap_percent(best_ms, lb):.0f}%)",
                    ax=axes[1])
    xmax = max(ls_ms, best_ms) * 1.02
    for a in axes:
        a.set_xlim(0, xmax)
    fig.suptitle(f"Schedule geometry — JSSP {n_jobs}x{n_machines}, LB={lb}", fontsize=12)
    fig.tight_layout()
    fig.savefig("gantt.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"saved: gantt.png  (LS {ls_ms}, Tabu {best_ms})")


if __name__ == "__main__":
    main()
