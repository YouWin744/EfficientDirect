from typing import Dict, List, Tuple, Any
import networkx as nx
import cvxpy as cp
import concurrent.futures
import time
from typing import Dict
from tqdm import tqdm

from schedule_type import *


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

    print(f'Diameter: {diameter}')

    class ProblemTask:
        def __init__(self, t: TimeStep, u: Node, problem: cp.Problem, x_vars: Dict[Tuple[Node, Node], cp.Variable], U: cp.Variable):
            self.t = t
            self.u = u
            self.problem = problem
            self.x_vars = x_vars
            self.U = U

    def _bfb_one_timestep_build(t: TimeStep) -> List[ProblemTask]:
        problems_to_solve: List[ProblemTask] = []

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
            has_valid_flow = False
            for v in sources_v:
                relevant_ws = [w for (src, w) in valid_pairs if src == v]

                # Check if there are any valid paths for v to u
                if relevant_ws:
                    constraints.append(
                        cp.sum([x_vars[(v, w)] for w in relevant_ws]) == 1.0)
                    has_valid_flow = True
                # If not, skip this source/dest pair as it's impossible to complete the flow.
                else:
                    continue

            # If no source has a valid path (w) to the destination u, skip this LP
            if not has_valid_flow and sources_v:
                continue

            # 3rd constraints: valid x_vars
            for (v, w), x in x_vars.items():
                constraints.append(x <= 1.0)

            # build LP
            objective = cp.Minimize(U)
            problem = cp.Problem(objective, constraints)

            # Store the task information
            problems_to_solve.append(ProblemTask(t, u, problem, x_vars, U))

        return problems_to_solve

    def _solve_problem_task(task: ProblemTask) -> Tuple[TimeStep, Node, ScheduleEntry | None]:
        # This function solves a single LP problem from the buffer.
        t, u, problem, x_vars, U = task.t, task.u, task.problem, task.x_vars, task.U

        try:
            # Solve the LP problem
            problem.solve(solver=cp.SCIP)
        except cp.SolverError:
            print(f"Solver failed for node {u} at step {t}")
            return (t, u, None)

        # save results
        u_schedule: TransferMap = {}
        if problem.status == 'optimal':
            for (v, w), var in x_vars.items():
                if var.value is not None and var.value > 1e-5:
                    # v is the source, w is the via node (neighbor of u)
                    u_schedule[TransferKey(v, w)] = Fraction(var.value.item())

            if u_schedule and U.value is not None:
                # Use the provided ScheduleEntry type structure
                schedule_entry = ScheduleEntry(
                    load_U=U.value.item() if U.value is not None else float('-inf'),
                    transfers=u_schedule
                )
                return (t, u, schedule_entry)
            else:
                return (t, u, None)
        else:
            # The 'optimal' status check covers 'infeasible', 'unbounded', etc.
            # print(f"No optimal solution for node {u} at step {t}. Status: {problem.status}")
            return (t, u, None)

    full_schedule: Schedule = {}

    for t in range(1, diameter + 1):
        current_t = TimeStep(t)

        problem_buffer: List[ProblemTask] = _bfb_one_timestep_build(current_t)

        if not problem_buffer:
            continue

        print(
            f'Time Step {current_t}: Solving {len(problem_buffer)} LP problems in parallel...')

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            results_iterator = executor.map(
                _solve_problem_task, problem_buffer)

            results = list(tqdm(results_iterator, total=len(
                problem_buffer), desc=f'Solving t={current_t} problems', unit='problem', leave=True))

        full_schedule[current_t] = {}
        for _, u, schedule_entry in results:
            if schedule_entry is not None:
                full_schedule[current_t][u] = schedule_entry

    time_end = time.time()

    print(f'\nBFB search time cost: {(time_end - time_begin):.3f}')

    return full_schedule


def _main1():
    G1 = nx.DiGraph()
    nodes = ['v1', 'v2', 'w1', 'w2', 'w3', 'u1', 'u2']
    edges = [('v1', 'w1'), ('v1', 'w2'), ('v2', 'w2'), ('v2', 'w3'),
             ('w1', 'u1'), ('w1', 'u2'), ('w2', 'u1'), ('w2', 'u2'), ('w3', 'u2')]

    G1.add_nodes_from(nodes)
    G1.add_edges_from(edges)

    schedule = BFB(G1)

    utils.print_schedule(schedule)


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

    utils.print_schedule(A3)
    utils.print_schedule_bound(G3)

    # visualize_digraph(G3, 'example')
    # visualize_schedule(G3, A3, 5)


if __name__ == "__main__":
    from visualize import *
    from graph import *
    import utils
    # _main1()
    _main2()
