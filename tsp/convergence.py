from __future__ import annotations
import math
import random
import matplotlib.pyplot as plt
from tsp import random_instance, distance_matrix, tour_length, random_tour

def traced_ls(dist, seed=None):
    rng = random.Random(seed)
    n = len(dist)
    tour = random_tour(n, rng)
    best_len = tour_length(tour, dist)
    trace = [(0, best_len)]

    step = 0
    improved = True
    while improved:
        improved = False
        for i in range(n - 1):
            for j in range(i + 2, n):
                if i == 0 and j == n - 1:
                    continue
                a, b = tour[i], tour[i + 1]
                c, d = tour[j], tour[(j + 1) % n]
                delta = dist[a][c] + dist[b][d] - dist[a][b] - dist[c][d]
                if delta < -1e-12:
                    tour[i + 1 : j + 1] = tour[i + 1 : j + 1][::-1]
                    best_len += delta
                    step += 1
                    trace.append((step, best_len))
                    improved = True
                    break
            if improved:
                break
    return trace


def _two_opt_first(tour, dist):
    n = len(tour)
    improved = True
    while improved:
        improved = False
        for i in range(n - 1):
            for j in range(i + 2, n):
                if i == 0 and j == n - 1:
                    continue
                a, b = tour[i], tour[i + 1]
                c, d = tour[j], tour[(j + 1) % n]
                delta = dist[a][c] + dist[b][d] - dist[a][b] - dist[c][d]
                if delta < -1e-12:
                    tour[i + 1 : j + 1] = tour[i + 1 : j + 1][::-1]
                    improved = True
                    break
            if improved:
                break
    return tour


def _double_bridge(tour, rng):
    n = len(tour)
    cuts = sorted(rng.sample(range(1, n), 3))
    p1, p2, p3 = cuts
    return tour[:p1] + tour[p3:] + tour[p2:p3] + tour[p1:p2]


def traced_ils(dist, n_iterations=100, seed=None):
    rng = random.Random(seed)
    n = len(dist)
    tour = _two_opt_first(random_tour(n, rng), dist)
    best = list(tour)
    best_len = tour_length(best, dist)
    trace = [(0, best_len)]

    for k in range(1, n_iterations + 1):
        perturbed = _double_bridge(list(best), rng)
        candidate = _two_opt_first(perturbed, dist)
        cand_len = tour_length(candidate, dist)
        if cand_len < best_len:
            best = candidate
            best_len = cand_len
        trace.append((k, best_len))
    return trace


def _gls_two_opt(tour, dist, penalty, lam):
    n = len(tour)
    improved = True
    while improved:
        improved = False
        for i in range(n - 1):
            for j in range(i + 2, n):
                if i == 0 and j == n - 1:
                    continue
                a, b = tour[i], tour[i + 1]
                c, d = tour[j], tour[(j + 1) % n]
                cd = dist[a][c] + dist[b][d] - dist[a][b] - dist[c][d]
                pd = penalty[a][c] + penalty[b][d] - penalty[a][b] - penalty[c][d]
                if cd + lam * pd < -1e-12:
                    tour[i + 1 : j + 1] = tour[i + 1 : j + 1][::-1]
                    improved = True
                    break
            if improved:
                break
    return tour


def traced_gls(dist, n_iterations=100, alpha=0.3, seed=None):
    rng = random.Random(seed)
    n = len(dist)
    penalty = [[0] * n for _ in range(n)]

    tour = _gls_two_opt(random_tour(n, rng), dist, penalty, lam=0.0)
    best = list(tour)
    best_len = tour_length(best, dist)
    lam = alpha * best_len / n
    trace = [(0, best_len)]

    for k in range(1, n_iterations + 1):
        max_util = -1.0
        max_edges = []
        for i in range(n):
            a, b = tour[i], tour[(i + 1) % n]
            util = dist[a][b] / (1 + penalty[a][b])
            if util > max_util + 1e-12:
                max_util = util
                max_edges = [(a, b)]
            elif abs(util - max_util) <= 1e-12:
                max_edges.append((a, b))
        for (a, b) in max_edges:
            penalty[a][b] += 1
            penalty[b][a] += 1

        tour = _gls_two_opt(tour, dist, penalty, lam)
        L = tour_length(tour, dist)
        if L < best_len:
            best_len = L
            best = list(tour)
        trace.append((k, best_len))
    return trace


def traced_sa(dist, T0=None, alpha=0.995, iter_per_T=None, T_min=0.01, seed=None):
    rng = random.Random(seed)
    n = len(dist)
    if T0 is None:
        total, cnt = 0.0, 0
        for i in range(n):
            for j in range(i + 1, n):
                total += dist[i][j]; cnt += 1
        T0 = total / cnt
    if iter_per_T is None:
        iter_per_T = n * (n - 1) // 2

    tour = random_tour(n, rng)
    cur_len = tour_length(tour, dist)
    best_len = cur_len
    trace = [(0, best_len)]

    T = T0
    step = 0
    while T > T_min:
        for _ in range(iter_per_T):
            i = rng.randint(0, n - 2)
            j = rng.randint(i + 1, n - 1)
            if i == 0 and j == n - 1:
                continue
            a, b = tour[i], tour[i + 1]
            c, d = tour[j], tour[(j + 1) % n]
            delta = dist[a][c] + dist[b][d] - dist[a][b] - dist[c][d]
            if delta < 0 or rng.random() < math.exp(-delta / T):
                tour[i + 1 : j + 1] = tour[i + 1 : j + 1][::-1]
                cur_len += delta
                if cur_len < best_len:
                    best_len = cur_len
        T *= alpha
        step += 1
        trace.append((step, best_len))
    return trace


def main(n=100, instance_seed=42):
    coords = random_instance(n=n, seed=instance_seed)
    dist = distance_matrix(coords)

    print("Tracing LS ...")
    tr_ls = traced_ls(dist)
    print("Tracing ILS ...")
    tr_ils = traced_ils(dist, n_iterations=100)
    print("Tracing GLS ...")
    tr_gls = traced_gls(dist, n_iterations=100, alpha=0.3)
    print("Tracing SA ...")
    tr_sa = traced_sa(dist, alpha=0.995)

    fig, axes = plt.subplots(2, 2, figsize=(10, 6.5), sharey=False)
    specs = [
        (tr_ls,  "LS  (2-opt swap steps)",             "swap count",      "#D95F02", axes[0, 0]),
        (tr_ils, "ILS (perturb+LS outer iterations)",   "outer iteration", "#1B4F72", axes[0, 1]),
        (tr_gls, "GLS (penalty+LS outer iterations)",   "outer iteration", "#117A65", axes[1, 0]),
        (tr_sa,  "SA  (temperature levels)",             "temp level",      "#7D3C98", axes[1, 1]),
    ]
    for trace, title, xlab, color, ax in specs:
        xs = [t[0] for t in trace]
        ys = [t[1] for t in trace]
        ax.plot(xs, ys, color=color, linewidth=1.3)
        ax.set_title(title, fontsize=10)
        ax.set_xlabel(xlab, fontsize=9)
        ax.grid(True, alpha=0.25, linewidth=0.5)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.tick_params(labelsize=8)

    for ax in axes.flat:
        ax.set_ylabel("Best tour length so far", fontsize=9)
    fig.suptitle(f"Convergence dynamics — n={n}, one run per algorithm", fontsize=11)
    fig.tight_layout()
    fig.savefig("convergence.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    print("saved: convergence.png")


if __name__ == "__main__":
    main()
