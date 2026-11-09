from __future__ import annotations
import math
import random
from dataclasses import dataclass



@dataclass(frozen=True)
class JSSPInstance:
    machines: tuple[tuple[int, ...], ...]
    durations: tuple[tuple[int, ...], ...]
    name: str

    @property
    def n_jobs(self) -> int:
        return len(self.machines)

    @property
    def n_machines(self) -> int:
        return len(self.machines[0])


def random_instance(n_jobs: int, n_machines: int, seed: int | None = None,
                    name: str | None = None) -> JSSPInstance:
    rng = random.Random(seed)
    machines, durations = [], []
    for _ in range(n_jobs):
        perm = list(range(n_machines))
        rng.shuffle(perm)
        machines.append(tuple(perm))
        durations.append(tuple(rng.randint(1, 99) for _ in range(n_machines)))
    if name is None:
        name = f"rand_{n_jobs}x{n_machines}" + (f"_s{seed}" if seed is not None else "")
    return JSSPInstance(machines=tuple(machines), durations=tuple(durations), name=name)


def random_permutation(inst: JSSPInstance, rng: random.Random) -> list[int]:
    perm = []
    for j in range(inst.n_jobs):
        perm.extend([j] * inst.n_machines)
    rng.shuffle(perm)
    return perm


def decode(perm: list[int], inst: JSSPInstance):
    n_jobs = inst.n_jobs
    n_machines = inst.n_machines
    job_op = [0] * n_jobs
    job_ready = [0] * n_jobs
    machine_ready = [0] * n_machines
    schedule = []
    for j in perm:
        o = job_op[j]
        m = inst.machines[j][o]
        d = inst.durations[j][o]
        start = job_ready[j] if job_ready[j] > machine_ready[m] else machine_ready[m]
        finish = start + d
        schedule.append((j, o, m, start, finish))
        job_ready[j] = finish
        machine_ready[m] = finish
        job_op[j] += 1
    makespan = max(machine_ready)
    return makespan, schedule


def makespan(perm: list[int], inst: JSSPInstance) -> int:
    n_jobs = inst.n_jobs
    job_op = [0] * n_jobs
    job_ready = [0] * n_jobs
    machine_ready = [0] * inst.n_machines
    for j in perm:
        o = job_op[j]
        m = inst.machines[j][o]
        d = inst.durations[j][o]
        s = job_ready[j] if job_ready[j] > machine_ready[m] else machine_ready[m]
        f = s + d
        job_ready[j] = f
        machine_ready[m] = f
        job_op[j] += 1
    return max(machine_ready)


def lower_bound(inst: JSSPInstance) -> int:
    n_machines = inst.n_machines
    lb_job = max(sum(inst.durations[j]) for j in range(inst.n_jobs))

    load = [0] * n_machines
    min_head = [float("inf")] * n_machines
    min_tail = [float("inf")] * n_machines
    for j in range(inst.n_jobs):
        durs = inst.durations[j]
        total = sum(durs)
        prefix = 0
        for o in range(n_machines):
            m = inst.machines[j][o]
            d = durs[o]
            head = prefix
            tail = total - prefix - d
            load[m] += d
            if head < min_head[m]:
                min_head[m] = head
            if tail < min_tail[m]:
                min_tail[m] = tail
            prefix += d
    lb_machine = max(min_head[m] + load[m] + min_tail[m] for m in range(n_machines))
    return int(max(lb_job, lb_machine))


def gap_percent(ms: int, lb: int) -> float:
    return (ms - lb) / lb * 100.0


def validate_schedule(perm: list[int], inst: JSSPInstance) -> bool:
    ms, sched = decode(perm, inst)
    by_job = {}
    for (j, o, m, s, f) in sched:
        by_job.setdefault(j, {})[o] = (s, f)
    for j, ops in by_job.items():
        for o in range(1, inst.n_machines):
            if ops[o][0] < ops[o - 1][1] - 1e-9:
                return False
    by_machine = {}
    for (j, o, m, s, f) in sched:
        by_machine.setdefault(m, []).append((s, f))
    for m, intervals in by_machine.items():
        intervals.sort()
        for i in range(1, len(intervals)):
            if intervals[i][0] < intervals[i - 1][1] - 1e-9:
                return False
    if ms < lower_bound(inst):
        return False
    return True



def _two_swap_first_improvement(perm, inst):
    L = len(perm)
    cur = makespan(perm, inst)
    improved = True
    while improved:
        improved = False
        for i in range(L - 1):
            for k in range(i + 1, L):
                if perm[i] == perm[k]:
                    continue
                perm[i], perm[k] = perm[k], perm[i]
                new = makespan(perm, inst)
                if new < cur:
                    cur = new
                    improved = True
                    break
                perm[i], perm[k] = perm[k], perm[i]
            if improved:
                break
    return perm, cur


def local_search(inst, seed=None):
    rng = random.Random(seed)
    perm = random_permutation(inst, rng)
    perm, ms = _two_swap_first_improvement(perm, inst)
    return perm, ms



def _double_bridge(perm, rng):
    L = len(perm)
    if L < 8:
        p = list(perm); rng.shuffle(p); return p
    cuts = sorted(rng.sample(range(1, L), 3))
    p1, p2, p3 = cuts
    return perm[:p1] + perm[p3:] + perm[p2:p3] + perm[p1:p2]


def iterated_local_search(inst, n_iterations=50, seed=None):
    rng = random.Random(seed)
    perm = random_permutation(inst, rng)
    perm, ms = _two_swap_first_improvement(perm, inst)
    best, best_ms = list(perm), ms
    for _ in range(n_iterations):
        cand = _double_bridge(best, rng)
        cand, cand_ms = _two_swap_first_improvement(cand, inst)
        if cand_ms < best_ms:
            best, best_ms = cand, cand_ms
    return best, best_ms



def _avg_duration(inst):
    tot = sum(sum(inst.durations[j]) for j in range(inst.n_jobs))
    return tot / (inst.n_jobs * inst.n_machines)


def simulated_annealing(inst, T0=None, alpha=0.95, iter_per_T=None,
                        T_min=0.1, seed=None):
    rng = random.Random(seed)
    L = inst.n_jobs * inst.n_machines
    if T0 is None:
        T0 = _avg_duration(inst) * 2.0
    if iter_per_T is None:
        iter_per_T = L

    perm = random_permutation(inst, rng)
    cur = makespan(perm, inst)
    best, best_ms = list(perm), cur

    T = T0
    while T > T_min:
        for _ in range(iter_per_T):
            i = rng.randint(0, L - 1)
            k = rng.randint(0, L - 1)
            if perm[i] == perm[k]:
                continue
            perm[i], perm[k] = perm[k], perm[i]
            new = makespan(perm, inst)
            delta = new - cur
            if delta < 0 or rng.random() < math.exp(-delta / T):
                cur = new
                if cur < best_ms:
                    best, best_ms = list(perm), cur
            else:
                perm[i], perm[k] = perm[k], perm[i]
        T *= alpha
    return best, best_ms



def _op_on_machine(inst):
    oom = [dict() for _ in range(inst.n_jobs)]
    for j in range(inst.n_jobs):
        for o in range(inst.n_machines):
            oom[j][inst.machines[j][o]] = o
    return oom


def perm_to_mseq(perm, inst):
    _, sched = decode(perm, inst)
    by_machine = [[] for _ in range(inst.n_machines)]
    for (j, o, m, s, f) in sched:
        by_machine[m].append((s, j))
    return [ [j for _, j in sorted(lst)] for lst in by_machine ]


def graph_makespan(mseq, inst, oom=None):
    from collections import deque
    n, m = inst.n_jobs, inst.n_machines
    p, mach = inst.durations, inst.machines
    if oom is None:
        oom = _op_on_machine(inst)

    pos = [dict() for _ in range(m)]
    for mm in range(m):
        for idx, jb in enumerate(mseq[mm]):
            pos[mm][jb] = idx

    r = [[0] * m for _ in range(n)]
    crit_pred = [[None] * m for _ in range(n)]
    indeg = [[0] * m for _ in range(n)]
    for j in range(n):
        for o in range(m):
            deg = 1 if o > 0 else 0
            mm = mach[j][o]
            if pos[mm][j] > 0:
                deg += 1
            indeg[j][o] = deg

    q = deque((j, o) for j in range(n) for o in range(m) if indeg[j][o] == 0)
    processed = 0
    ms = 0
    while q:
        j, o = q.popleft()
        processed += 1
        finish = r[j][o] + p[j][o]
        if finish > ms:
            ms = finish
        if o + 1 < m:
            if finish > r[j][o + 1]:
                r[j][o + 1] = finish
                crit_pred[j][o + 1] = (j, o)
            indeg[j][o + 1] -= 1
            if indeg[j][o + 1] == 0:
                q.append((j, o + 1))
        mm = mach[j][o]
        pj = pos[mm][j]
        if pj + 1 < n:
            sj = mseq[mm][pj + 1]
            so = oom[sj][mm]
            if finish > r[sj][so]:
                r[sj][so] = finish
                crit_pred[sj][so] = (j, o)
            indeg[sj][so] -= 1
            if indeg[sj][so] == 0:
                q.append((sj, so))

    if processed < n * m:
        return None, None, None
    return ms, r, crit_pred


def critical_blocks(mseq, inst, r, crit_pred, ms, oom):
    n, m = inst.n_jobs, inst.n_machines
    p, mach = inst.durations, inst.machines
    last = None
    for j in range(n):
        for o in range(m):
            if r[j][o] + p[j][o] == ms:
                last = (j, o)
                break
        if last:
            break
    path = []
    node = last
    while node is not None:
        path.append(node)
        node = crit_pred[node[0]][node[1]]
    path.reverse()
    blocks = []
    cur_m = None
    cur = []
    for (j, o) in path:
        mm = mach[j][o]
        if mm == cur_m:
            cur.append(j)
        else:
            if cur:
                blocks.append((cur_m, cur))
            cur_m = mm
            cur = [j]
    if cur:
        blocks.append((cur_m, cur))
    return blocks


def n5_moves(mseq, inst, oom):
    ms, r, crit_pred = graph_makespan(mseq, inst, oom)
    if ms is None:
        return [], None
    blocks = critical_blocks(mseq, inst, r, crit_pred, ms, oom)
    moves = set()
    B = len(blocks)
    for bi, (mm, jobs) in enumerate(blocks):
        k = len(jobs)
        if k < 2:
            continue
        if bi != 0:
            moves.add((mm, jobs[0], jobs[1]))
        if bi != B - 1:
            moves.add((mm, jobs[-2], jobs[-1]))
    return list(moves), ms


def _apply_move(mseq, mm, a, b):
    seq = list(mseq[mm])
    ia, ib = seq.index(a), seq.index(b)
    seq[ia], seq[ib] = seq[ib], seq[ia]
    new = list(mseq)
    new[mm] = seq
    return new



def local_search_n5(inst, seed=None):
    rng = random.Random(seed)
    oom = _op_on_machine(inst)
    perm = random_permutation(inst, rng)
    mseq = perm_to_mseq(perm, inst)
    cur, _, _ = graph_makespan(mseq, inst, oom)
    improved = True
    while improved:
        improved = False
        moves, cur = n5_moves(mseq, inst, oom)
        best_move, best_ms = None, cur
        for (mm, a, b) in moves:
            cand = _apply_move(mseq, mm, a, b)
            cms, _, _ = graph_makespan(cand, inst, oom)
            if cms is not None and cms < best_ms:
                best_ms, best_move = cms, (mm, a, b)
        if best_move is not None:
            mseq = _apply_move(mseq, *best_move)
            cur = best_ms
            improved = True
    return mseq, cur



def tabu_search(inst, max_iter=1000, tenure=10, seed=None):
    rng = random.Random(seed)
    oom = _op_on_machine(inst)
    perm = random_permutation(inst, rng)
    mseq = perm_to_mseq(perm, inst)
    cur, _, _ = graph_makespan(mseq, inst, oom)
    best_mseq, best_ms = [list(s) for s in mseq], cur

    tabu = {}
    for it in range(max_iter):
        moves, cur = n5_moves(mseq, inst, oom)
        if not moves:
            break
        best_move, best_move_ms = None, float("inf")
        fallback_move, fallback_ms = None, float("inf")
        for (mm, a, b) in moves:
            cand = _apply_move(mseq, mm, a, b)
            cms, _, _ = graph_makespan(cand, inst, oom)
            if cms is None:
                continue
            if cms < fallback_ms:
                fallback_ms, fallback_move = cms, (mm, a, b)
            key = (mm, frozenset((a, b)))
            is_tabu = tabu.get(key, 0) > it
            if is_tabu and cms >= best_ms:
                continue
            if cms < best_move_ms:
                best_move_ms, best_move = cms, (mm, a, b)
        if best_move is None:
            best_move, best_move_ms = fallback_move, fallback_ms
        if best_move is None:
            break
        mm, a, b = best_move
        mseq = _apply_move(mseq, mm, a, b)
        tabu[(mm, frozenset((a, b)))] = it + tenure
        if best_move_ms < best_ms:
            best_ms = best_move_ms
            best_mseq = [list(s) for s in mseq]
    return best_mseq, best_ms



def draw_gantt_mseq(inst, mseq, filename, title=None, ax=None):
    import matplotlib.pyplot as plt
    oom = _op_on_machine(inst)
    ms, r, _ = graph_makespan(mseq, inst, oom)
    n_jobs, n_machines = inst.n_jobs, inst.n_machines
    cmap = plt.get_cmap("tab20" if n_jobs > 10 else "tab10")
    ncol = 20 if n_jobs > 10 else 10

    own_fig = ax is None
    if own_fig:
        fig, ax = plt.subplots(figsize=(11, 0.45 * n_machines + 1.5))
    for j in range(n_jobs):
        for o in range(n_machines):
            m = inst.machines[j][o]
            s = r[j][o]
            d = inst.durations[j][o]
            ax.barh(m, d, left=s, height=0.7, color=cmap(j % ncol),
                    edgecolor="white", linewidth=0.6)
            if d >= ms * 0.03:
                ax.text(s + d / 2, m, str(j), va="center", ha="center",
                        fontsize=7, color="white")
    ax.set_yticks(range(n_machines))
    ax.set_yticklabels([f"M{m}" for m in range(n_machines)])
    ax.set_xlabel("Time")
    ax.invert_yaxis()
    ax.set_title(title or f"{inst.name} — makespan {ms}")
    ax.grid(True, axis="x", alpha=0.25, linewidth=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    if own_fig:
        fig.tight_layout()
        fig.savefig(filename, dpi=160, bbox_inches="tight")
        plt.close(fig)
    return ms


def draw_gantt(inst, perm, filename, title=None):
    import matplotlib.pyplot as plt
    ms, sched = decode(perm, inst)
    n_jobs = inst.n_jobs
    n_machines = inst.n_machines

    cmap = plt.get_cmap("tab20" if n_jobs > 10 else "tab10")
    fig, ax = plt.subplots(figsize=(11, 0.45 * n_machines + 1.5))
    for (j, o, m, s, f) in sched:
        ax.barh(m, f - s, left=s, height=0.7,
                color=cmap(j % (20 if n_jobs > 10 else 10)),
                edgecolor="white", linewidth=0.6)
        if f - s >= ms * 0.03:
            ax.text((s + f) / 2, m, str(j), va="center", ha="center",
                    fontsize=7, color="white")
    ax.set_yticks(range(n_machines))
    ax.set_yticklabels([f"M{m}" for m in range(n_machines)])
    ax.set_xlabel("Time")
    ax.invert_yaxis()
    ax.set_title(title or f"{inst.name} — makespan {ms}")
    ax.grid(True, axis="x", alpha=0.25, linewidth=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.tight_layout()
    fig.savefig(filename, dpi=160, bbox_inches="tight")
    plt.close(fig)



def main(n_jobs=10, n_machines=10, seed=42):
    inst = random_instance(n_jobs, n_machines, seed=seed)
    lb = lower_bound(inst)
    print(f"{inst.name}   ({n_jobs} jobs x {n_machines} machines)")
    print(f"lower bound: {lb}\n")

    for name, fn, kw in [
        ("LS",  local_search,          {}),
        ("ILS", iterated_local_search, {"n_iterations": 50}),
        ("SA",  simulated_annealing,   {"alpha": 0.95}),
    ]:
        perm, ms = fn(inst, **kw)
        print(f"{name:5} makespan {ms:6d}   gap to LB {gap_percent(ms, lb):5.1f}%")


if __name__ == "__main__":
    main()
