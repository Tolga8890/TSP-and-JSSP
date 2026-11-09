from __future__ import annotations
import math
import random

def random_instance(n: int = 50,
                    width: float = 1000.0,
                    height: float = 1000.0,
                    seed: int | None = None) -> list[tuple[float, float]]:
    rng = random.Random(seed)
    return [(rng.uniform(0, width), rng.uniform(0, height)) for _ in range(n)]


def distance_matrix(coords: list[tuple[float, float]]) -> list[list[float]]:
    n = len(coords)
    M = [[0.0] * n for _ in range(n)]
    for i in range(n):
        xi, yi = coords[i]
        for j in range(i + 1, n):
            xj, yj = coords[j]
            d = math.sqrt((xi - xj) ** 2 + (yi - yj) ** 2)
            M[i][j] = d
            M[j][i] = d
    return M


def tour_length(tour: list[int], dist: list[list[float]]) -> float:
    total = 0.0
    n = len(tour)
    for i in range(n):
        total += dist[tour[i]][tour[(i + 1) % n]]
    return total


def random_tour(n: int, rng: random.Random) -> list[int]:
    t = list(range(n))
    rng.shuffle(t)
    return t



def two_opt_first_improvement(tour: list[int], dist: list[list[float]]) -> list[int]:
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


def local_search(dist: list[list[float]], seed: int | None = None) -> tuple[list[int], float]:
    rng = random.Random(seed)
    n = len(dist)
    tour = random_tour(n, rng)
    tour = two_opt_first_improvement(tour, dist)
    return tour, tour_length(tour, dist)



def double_bridge(tour: list[int], rng: random.Random) -> list[int]:
    n = len(tour)
    cuts = sorted(rng.sample(range(1, n), 3))
    p1, p2, p3 = cuts
    return tour[:p1] + tour[p3:] + tour[p2:p3] + tour[p1:p2]


def iterated_local_search(dist: list[list[float]],
                          n_iterations: int = 100,
                          seed: int | None = None) -> tuple[list[int], float]:
    rng = random.Random(seed)
    n = len(dist)
    tour = random_tour(n, rng)
    tour = two_opt_first_improvement(tour, dist)
    best = list(tour)
    best_len = tour_length(best, dist)

    for _ in range(n_iterations):
        perturbed = double_bridge(list(best), rng)
        candidate = two_opt_first_improvement(perturbed, dist)
        cand_len = tour_length(candidate, dist)
        if cand_len < best_len:
            best = candidate
            best_len = cand_len

    return best, best_len



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
                cost_delta = dist[a][c] + dist[b][d] - dist[a][b] - dist[c][d]
                pen_delta = penalty[a][c] + penalty[b][d] - penalty[a][b] - penalty[c][d]
                delta = cost_delta + lam * pen_delta
                if delta < -1e-12:
                    tour[i + 1 : j + 1] = tour[i + 1 : j + 1][::-1]
                    improved = True
                    break
            if improved:
                break
    return tour


def guided_local_search(dist: list[list[float]],
                        n_iterations: int = 100,
                        alpha: float = 0.3,
                        seed: int | None = None) -> tuple[list[int], float]:
    rng = random.Random(seed)
    n = len(dist)
    penalty = [[0] * n for _ in range(n)]

    tour = random_tour(n, rng)
    tour = _gls_two_opt(tour, dist, penalty, lam=0.0)
    best = list(tour)
    best_len = tour_length(best, dist)
    lam = alpha * best_len / n

    for _ in range(n_iterations):
        max_util = -1.0
        max_edges: list[tuple[int, int]] = []
        for i in range(n):
            a = tour[i]
            b = tour[(i + 1) % n]
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

    return best, best_len



def _avg_edge_cost(dist):
    n = len(dist)
    total, count = 0.0, 0
    for i in range(n):
        for j in range(i + 1, n):
            total += dist[i][j]
            count += 1
    return total / count


def simulated_annealing(dist: list[list[float]],
                        T0: float | None = None,
                        alpha: float = 0.995,
                        iter_per_T: int | None = None,
                        T_min: float = 0.01,
                        seed: int | None = None) -> tuple[list[int], float]:
    rng = random.Random(seed)
    n = len(dist)
    if T0 is None:
        T0 = _avg_edge_cost(dist)
    if iter_per_T is None:
        iter_per_T = n * (n - 1) // 2

    tour = random_tour(n, rng)
    current_len = tour_length(tour, dist)
    best = list(tour)
    best_len = current_len

    T = T0
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
                current_len += delta
                if current_len < best_len:
                    best_len = current_len
                    best = list(tour)
        T *= alpha
    return best, best_len




def main(n: int = 50) -> None:
    coords = random_instance(n=n, seed=42)
    dist = distance_matrix(coords)

    print(f"TSP  n = {n}")
    print()

    _, L = local_search(dist)
    print(f"LS   tour length: {L:.1f}")

    _, L = iterated_local_search(dist, n_iterations=100)
    print(f"ILS  tour length: {L:.1f}")

    _, L = guided_local_search(dist, n_iterations=100, alpha=0.3)
    print(f"GLS  tour length: {L:.1f}")

    _, L = simulated_annealing(dist, alpha=0.995)
    print(f"SA   tour length: {L:.1f}")


if __name__ == "__main__":
    main(n=50)
