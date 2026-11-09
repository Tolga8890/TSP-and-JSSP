from __future__ import annotations
import statistics
import time
import jssp

# Every schedule an algorithm looks at goes through one of these two functions,
# so counting their calls measures how much search each algorithm performs.
_counter = {"evals": 0}
_makespan = jssp.makespan
_graph_makespan = jssp.graph_makespan


def _counted_makespan(*args, **kwargs):
    _counter["evals"] += 1
    return _makespan(*args, **kwargs)


def _counted_graph_makespan(*args, **kwargs):
    _counter["evals"] += 1
    return _graph_makespan(*args, **kwargs)


jssp.makespan = _counted_makespan
jssp.graph_makespan = _counted_graph_makespan

ALGOS = [
    ("LS",             jssp.local_search,          {}),
    ("ILS",            jssp.iterated_local_search, {"n_iterations": 50}),
    ("SA (alpha 0.95)", jssp.simulated_annealing,  {"alpha": 0.95}),
    ("SA (alpha 0.99)", jssp.simulated_annealing,  {"alpha": 0.99}),
    ("Tabu",           jssp.tabu_search,           {"max_iter": 5000, "tenure": 12}),
]


def main(n_jobs=10, n_machines=10, instance_seed=42, n_runs=5):
    inst = jssp.random_instance(n_jobs, n_machines, seed=instance_seed)
    print(f"Budget per run on {inst.name}, mean over seeds 0..{n_runs - 1}\n")
    print(f"{'Algo':<17}{'schedules evaluated':>21}{'time (s)':>10}")
    for name, fn, kw in ALGOS:
        evals, secs = [], []
        for s in range(n_runs):
            _counter["evals"] = 0
            t0 = time.perf_counter()
            fn(inst, seed=s, **kw)
            secs.append(time.perf_counter() - t0)
            evals.append(_counter["evals"])
        print(f"{name:<17}{statistics.mean(evals):>21,.0f}{statistics.mean(secs):>10.1f}")


if __name__ == "__main__":
    main()