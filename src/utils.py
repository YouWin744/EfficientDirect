from typing import TypeVar, Callable, List, Tuple
import networkx as nx
from schedule_type import *


_T = TypeVar('_T')


def pareto_frontier(candidates: List[_T],
                    key1: Callable[[_T], Any],
                    key2: Callable[[_T], Any]
                    ) -> List[_T]:

    L = len(candidates)
    if L == 0:
        return []

    pareto_frontier = []

    sorted_index = sorted(list(range(L)), key=lambda index: (
        key1(candidates[index]), key2(candidates[index])))

    # 1st element
    c = candidates[sorted_index[0]]
    pareto_frontier.append(c)
    min_key2 = key2(c)

    # rest elements
    for i in range(1, L):
        current_candidate = candidates[sorted_index[i]]
        current_key2 = key2(current_candidate)

        if current_key2 < min_key2:
            min_key2 = current_key2
            pareto_frontier.append(current_candidate)

    return pareto_frontier


def print_schedule_bound(G: nx.DiGraph):
    in_degrees = [d for n, d in G.in_degree()]
    is_in_regular = all(d == in_degrees[0] for d in in_degrees)

    assert is_in_regular, "not regular graph"
    assert nx.is_strongly_connected(G), "not connected graph"

    num_nodes = G.number_of_nodes()
    d = in_degrees[0]

    diameter = nx.diameter(G)

    print(f"ideal T: {diameter}, U: {(num_nodes - 1) / d}")

    return num_nodes, diameter, (num_nodes - 1) / d


def print_schedule(schedule: 'Schedule', full_details: bool = True) -> Tuple[int, float]:
    """
    Returns: Tuple[int, float]: TL, TB
    """

    time_steps = sorted(schedule.keys())

    if not time_steps:
        if full_details:
            print("empty schedule")
        return -1, -1

    if full_details:
        print("=" * 60)
        print('print schedule begin')
        print("=" * 45)

    T_B = 0.

    for t in time_steps:
        step_schedule = schedule[t]

        if full_details:
            if t > 1:
                print("")
            print(f"t = {t}")

        u_t = 0

        dest_nodes = sorted(step_schedule.keys())

        for u in dest_nodes:
            entry = step_schedule[u]
            load_U = entry['load_U']
            transfers = entry['transfers']
            u_t = max(u_t, load_U)

            if full_details:
                # if t > 1 and u == dest_nodes[0]:
                #     print("")

                # print(f"t = {t}")
                print(f"    to {u}: (U = {load_U:.4f})")

                sorted_transfers = sorted(
                    transfers.items(), key=lambda item: (item[0][0], item[0][1]))

                for transfer_key, fraction in sorted_transfers:
                    print(
                        f"        from {transfer_key.from_node}, via {transfer_key.via_node}, load={fraction:.4f}")

        T_B += u_t

    if full_details:
        print("=" * 45)

    print(f"total T: {len(time_steps)}, U: {T_B:.4f}")

    if full_details:
        print('print schedule end')
        print("=" * 60)

    return len(time_steps), T_B
