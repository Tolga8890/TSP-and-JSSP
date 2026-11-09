
from __future__ import annotations
import matplotlib.pyplot as plt
from tsp import (
    random_instance, distance_matrix,
    local_search, iterated_local_search,
)


def draw_tour(ax, coords, tour, title, color):
    xs = [coords[i][0] for i in tour] + [coords[tour[0]][0]]
    ys = [coords[i][1] for i in tour] + [coords[tour[0]][1]]
    ax.plot(xs, ys, color=color, linewidth=1.1, alpha=0.85)
    ax.scatter([c[0] for c in coords], [c[1] for c in coords],
               s=14, color="#2C2A26", zorder=3)
    ax.set_title(title, fontsize=10)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for side in ("top", "right", "bottom", "left"):
        ax.spines[side].set_color("#999")


def main(n=100, instance_seed=42, n_ls_trials=30):
    coords = random_instance(n=n, seed=instance_seed)
    dist = distance_matrix(coords)

    ls_runs = [local_search(dist) for _ in range(n_ls_trials)]
    ls_runs.sort(key=lambda x: x[1])
    ls_best_tour, ls_best_len = ls_runs[0]
    ls_worst_tour, ls_worst_len = ls_runs[-1]

    ils_tour, ils_len = iterated_local_search(dist, n_iterations=100)

    fig, axes = plt.subplots(1, 3, figsize=(11, 4))
    draw_tour(axes[0], coords, ls_worst_tour,
              f"LS — worst of {n_ls_trials} runs   L = {ls_worst_len:.0f}",
              "#D95F02")
    draw_tour(axes[1], coords, ls_best_tour,
              f"LS — best of {n_ls_trials} runs   L = {ls_best_len:.0f}",
              "#D95F02")
    draw_tour(axes[2], coords, ils_tour,
              f"ILS (100 iter)   L = {ils_len:.0f}",
              "#1B4F72")

    fig.suptitle(f"Tour geometry — n={n}, same instance", fontsize=11)
    fig.tight_layout()
    fig.savefig("tours.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"saved: tours.png  (LS worst {ls_worst_len:.0f}, best {ls_best_len:.0f}, ILS {ils_len:.0f})")


if __name__ == "__main__":
    main()
