import networkx as nx
import cvxpy as cp
from schedule_type import *
import concurrent.futures
import time
from typing import Dict
from graph import *


def BFB(G: nx.DiGraph) -> Schedule:
    """
    calculate breadth-first-broadcast (BFB) schedule
    return: dict of schedule
    return type: `schedule[time_step][dest_node] = {'load_U': float, 'transfers': dict (src, ngh) -> fraction`}
    """

    time_begin = time.time()

    path_lengths = dict(nx.all_pairs_shortest_path_length(G))
    nodes = list(G.nodes())

    try:
        diameter = max(max(d.values()) for d in path_lengths.values())
    except ValueError:
        diameter = 0

    def _bfb_one_timestep(t) -> tuple[int, Dict[Node, ScheduleEntry]]:
        schedule_t: Dict[Node, ScheduleEntry] = {}

        for u_index, u in enumerate(nodes):
            # print(f"t={t},u={u_index}")
            sources_v = [v for v in nodes if path_lengths[v].get(u) == t]
            if not sources_v:
                continue

            neighbors_w = list(G.predecessors(u))

            # LP vars
            U = cp.Variable(nonneg=True, name=f"U_{u}_{t}")
            x_vars = {}
            valid_pairs = []

            for v in sources_v:
                for w in neighbors_w:
                    if path_lengths[v].get(w) == t - 1:
                        valid_pairs.append((v, w))
                        var = cp.Variable(
                            nonneg=True, name=f"x_{v}_{w}_{u}_{t}")
                        x_vars[(v, w)] = var

            # LP constraints
            constraints = []

            # 1st constraints: correct max workload
            for w in neighbors_w:
                relevant_vs = [v for (v, ngh) in valid_pairs if ngh == w]
                if relevant_vs:
                    constraints.append(
                        cp.sum([x_vars[(v, w)] for v in relevant_vs]) <= U)

            # 2nd constraints: u receiving all data shards
            for v in sources_v:
                relevant_ws = [w for (src, w) in valid_pairs if src == v]

                # Check if there are any valid paths for v to u
                if relevant_ws:
                    constraints.append(
                        cp.sum([x_vars[(v, w)] for w in relevant_ws]) == 1.0)
                # If not, skip this source/dest pair as it's impossible to complete the flow.
                else:
                    continue

            # 3rd constraints: valid x_vars
            for (v, w), x in x_vars.items():
                constraints.append(x <= 1.0)

            # solve LP
            objective = cp.Minimize(U)
            problem = cp.Problem(objective, constraints)

            try:
                problem.solve(solver=cp.SCIP)
            except cp.SolverError:
                print(f"Solver failed for node {u} at step {t}")
                return (0, {})

            # save results
            u_schedule: TransferMap = {}
            if problem.status == 'optimal':
                for (v, w), var in x_vars.items():
                    if var.value is not None and var.value > 1e-5:
                        u_schedule[TransferKey(v, w)] = var.value

                if u_schedule:
                    schedule_t[u] = ScheduleEntry(
                        load_U=U.value.item() if U.value is not None else float('-inf'),
                        transfers=u_schedule
                    )
            else:
                print(f"No optimal solution for node {u} at step {t}")

        print(t)
        return t, schedule_t

    full_schedule = {}

    print('calculating...')
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        results = executor.map(_bfb_one_timestep, range(1, diameter + 1))
        for t, schedule_t in results:
            full_schedule[t] = schedule_t

    time_end = time.time()

    print(f'BFB search time cost: {(time_end - time_begin):.3f}')

    return full_schedule


def _main1():
    G1 = nx.DiGraph()
    nodes = ['v1', 'v2', 'w1', 'w2', 'w3', 'u1', 'u2']
    edges = [('v1', 'w1'), ('v1', 'w2'), ('v2', 'w2'), ('v2', 'w3'),
             ('w1', 'u1'), ('w1', 'u2'), ('w2', 'u1'), ('w2', 'u2'), ('w3', 'u2')]

    G1.add_nodes_from(nodes)
    G1.add_edges_from(edges)

    schedule = BFB(G1)

    print_schedule(schedule)


def _main2():
    G3 = nx.DiGraph()
    nodes = [0, 1, 2, 3, 4, 5, 6, 7]
    edges = [(0, 1), (0, 2), (0, 3), (0, 4), (1, 5), (1, 6), (1, 7), (2, 5),
             (2, 6), (2, 7), (3, 5), (3, 6), (3, 7), (4, 5), (4, 6), (4, 7)]
    r_edges = [(y, x) for (x, y) in edges]
    G3.add_nodes_from(nodes)
    G3.add_edges_from(edges)
    G3.add_edges_from(r_edges)

    A3 = BFB(G3)

    print_schedule(A3)
    print_schedule_bound(G3)

    visualize_digraph(G3, 'example')


if __name__ == "__main__":
    from visualize_graph import *
    from graph import *
    _main1()
    # _main2()
