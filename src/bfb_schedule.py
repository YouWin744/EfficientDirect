import networkx as nx
import cvxpy as cp
from schedule_type import *


def BFB(G: nx.DiGraph) -> Schedule:
    """
    calculate breadth-first-broadcast (BFB) schedule  
    return: dict of schedule 
    return type: `schedule[time_step][dest_node] = {'load_U': float, 'transfers': dict (src, ngh) -> fraction`}
    """

    path_lengths = dict(nx.all_pairs_shortest_path_length(G))
    nodes = list(G.nodes())

    try:
        diameter = max(max(d.values()) for d in path_lengths.values())
    except ValueError:
        diameter = 0

    full_schedule = {}

    for t in range(1, diameter + 1):
        full_schedule[t] = {}
        print(f"calculating step {t}...")

        for u in nodes:
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
                problem.solve()
            except cp.SolverError:
                print(f"Solver failed for node {u} at step {t}")
                continue

            # save results
            u_schedule = {}
            if problem.status == 'optimal':
                for (v, w), var in x_vars.items():
                    if var.value is not None and var.value > 1e-5:
                        u_schedule[(v, w)] = var.value

                if u_schedule:
                    full_schedule[t][u] = {
                        'load_U': U.value,
                        'transfers': u_schedule
                    }
            else:
                print(f"No optimal solution for node {u} at step {t}")

    return full_schedule


if __name__ == "__main__":
    G = nx.DiGraph()
    nodes = ['v1', 'v2', 'w1', 'w2', 'w3', 'u1', 'u2']
    edges = [('v1', 'w1'), ('v1', 'w2'), ('v2', 'w2'), ('v2', 'w3'),
             ('w1', 'u1'), ('w1', 'u2'), ('w2', 'u1'), ('w2', 'u2'), ('w3', 'u2')]

    G.add_nodes_from(nodes)
    G.add_edges_from(edges)

    schedule = BFB(G)

    print_schedule(schedule)
