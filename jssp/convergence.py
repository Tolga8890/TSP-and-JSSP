from __future__ import annotations
import math
import random
import matplotlib.pyplot as plt
from jssp import (
    random_instance, lower_bound,
    _op_on_machine, random_permutation, perm_to_mseq,
    graph_makespan, n5_moves, _apply_move, makespan,
)


def traced_tabu(inst, max_iter=5000, tenure=12, seed=None):
    rng = random.Random(seed)
    oom = _op_on_machine(inst)
    mseq = perm_to_mseq(random_permutation(inst, rng), inst)
    cur, _, _ = graph_makespan(mseq, inst, oom)
    best = cur
    tabu = {}
    trace_cur, trace_best = [cur], [best]
    for it in range(max_iter):
        moves, cur = n5_moves(mseq, inst, oom)
        if not moves:
            break
        bm, bms = None, float("inf")
        fb, fbms = None, float("inf")
        for (mm, a, b) in moves:
            cand = _apply_move(mseq, mm, a, b)
            cms, _, _ = graph_makespan(cand, inst, oom)
            if cms is None:
                continue
            if cms < fbms:
                fbms, fb = cms, (mm, a, b)
            key = (mm, frozenset((a, b)))
            if tabu.get(key, 0) > it and cms >= best:
                continue
            if cms < bms:
                bms, bm = cms, (mm, a, b)
        if bm is None:
            bm, bms = fb, fbms
        if bm is None:
            break
        mm, a, b = bm
        mseq = _apply_move(mseq, mm, a, b)
        tabu[(mm, frozenset((a, b)))] = it + tenure
        cur = bms
        if bms < best:
            best = bms
        trace_cur.append(cur)
        trace_best.append(best)
    return trace_cur, trace_best


def traced_sa_best(inst, alpha=0.95, seed=None):
    rng = random.Random(seed)
    L = inst.n_jobs * inst.n_machines
    T0 = sum(sum(inst.durations[j]) for j in range(inst.n_jobs)) / L * 2.0
    iter_per_T = L
    perm = random_permutation(inst, rng)
    cur = makespan(perm, inst)
    best = cur
    trace = [best]
    T = T0
    while T > 0.1:
        for _ in range(iter_per_T):
            i = rng.randint(0, L - 1)
            k = rng.randint(0, L - 1)
            if perm[i] == perm[k]:
                continue
            perm[i], perm[k] = perm[k], perm[i]
            new = makespan(perm, inst)
            d = new - cur
            if d < 0 or rng.random() < math.exp(-d / T):
                cur = new
                if cur < best:
                    best = cur
            else:
                perm[i], perm[k] = perm[k], perm[i]
        trace.append(best)
        T *= alpha
    return trace


def main(n_jobs=10, n_machines=10, instance_seed=42):
    inst = random_instance(n_jobs, n_machines, seed=instance_seed)
    lb = lower_bound(inst)
    print("tracing Tabu ...")
    tcur, tbest = traced_tabu(inst, max_iter=5000, tenure=12, seed=1)
    print("tracing SA ...")
    sabest = traced_sa_best(inst, alpha=0.95, seed=1)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
    ax = axes[0]
    ax.plot(range(len(tcur)), tcur, color="#9BB8AC", linewidth=0.7, label="current")
    ax.plot(range(len(tbest)), tbest, color="#117A65", linewidth=1.6, label="best so far")
    ax.axhline(lb, color="#B24A2A", linewidth=1.0, linestyle="--", label=f"lower bound {lb}")
    ax.set_title("Tabu (N5) — iteration")
    ax.set_xlabel("iteration")
    ax.set_ylabel("makespan")
    ax.legend(frameon=False, fontsize=8)

    ax = axes[1]
    ax.plot(range(len(sabest)), sabest, color="#7D3C98", linewidth=1.6, label="best so far")
    ax.axhline(lb, color="#B24A2A", linewidth=1.0, linestyle="--", label=f"lower bound {lb}")
    ax.set_title("SA (swap) — temperature level")
    ax.set_xlabel("temperature level")
    ax.set_ylabel("makespan")
    ax.legend(frameon=False, fontsize=8)

    for ax in axes:
        ax.grid(True, alpha=0.25)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    fig.suptitle(f"Convergence — JSSP {n_jobs}x{n_machines}", fontsize=11)
    fig.tight_layout()
    fig.savefig("convergence.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    print("saved: convergence.png")


if __name__ == "__main__":
    main()
