import networkx as nx
from schedule_type import *
import warnings


def line_graph_expansion(G: nx.DiGraph, A: None | Schedule) -> tuple[nx.DiGraph, Schedule]:

    G_prime = nx.DiGraph()

    new_nodes = list(G.edges())
    G_prime.add_nodes_from(new_nodes)

    for u, v in G.edges():
        for _, w in G.out_edges(v):
            G_prime.add_edge((u, v), (v, w))

    A_prime = {}
    if A is not None:

        # g_prime_in_sdegree = dict(G_prime.in_degree())

        # insert the first comm step in A_prime
        # ((v′v, S), (v′v, vu), 1) for each edge (v′v, vu) ∈ E_{L(G)} with v′v != vu
        t_prime_1 = TimeStep(1)
        A_prime[t_prime_1] = {}

        for w in G_prime.nodes():
            u_schedule: TransferMap = {}

            for v in G_prime.predecessors(w):
                u_schedule[(v, v)] = Fraction(1)

            A_prime[t_prime_1][w] = {
                'load_U': 1.0,
                'transfers': u_schedule
            }

        # adapt A to form A_prime
        # ((v′v, C), (uw, ww′), t + 1) for each ((v, C), (u, w), t) ∈ A_G and v′v != ww′
        for t, step_schedule in A.items():
            t_prime = TimeStep(t + 1)

            A_prime[t_prime] = {}

            for w in step_schedule.keys():
                transfers = step_schedule[w]['transfers']

                for (v, u), fraction in transfers.items():
                    for _, w_prime in G.out_edges(w):
                        dest = (w, w_prime)

                        if dest not in A_prime[t_prime]:
                            A_prime[t_prime][dest] = {
                                'load_U': 0.0, 'transfers': {}}

                        for v_prime in G.predecessors(v):
                            if ((v_prime, v) != (w, w_prime)):
                                transfer_key = ((v_prime, v), (u, w))
                                A_prime[t_prime][dest]['transfers'][transfer_key] = fraction

        # Recalculate the maximum load U for t > 1
        for t in A_prime.keys():
            if t == 1:
                continue

            for w in A_prime[t].keys():
                transfers = A_prime[t][w]['transfers']

                link_loads = {}
                for (v_L, v), fraction in transfers.items():
                    if v not in link_loads:
                        link_loads[v] = 0.0
                    link_loads[v] += fraction

                max_load_U = max(link_loads.values()) if link_loads else 0.0
                A_prime[t][w]['load_U'] = max_load_U

    return G_prime, A_prime


def degree_expansion(G: nx.DiGraph, A: None | Schedule, n: int) -> tuple[nx.DiGraph, Schedule]:

    assert (n > 1)

    G_prime = nx.DiGraph()
    nodes = list(G.nodes())
    d = G.out_degree(nodes[0]) if nodes else 0
    if nodes and not all(G.out_degree(node) == d for node in nodes):
        warnings.warn(
            "G does not have uniform out-degree. Degree expansion assumes regular graphs.", RuntimeWarning)

    for j in range(n):
        G_prime.add_nodes_from([(node, j) for node in nodes])

    for w, v in G.edges():
        for j in range(n):
            for i in range(n):
                G_prime.add_edge((w, j), (v, i))

    A_prime: Schedule = {}
    if A is not None:
        t_max = 0

        for t, step_schedule in A.items():
            t_max = max(t_max, t)
            A_prime[t] = {}

            # For all i, j including i=j and for each ((v,C), (u,w), t) ∈ A_G, add ((v_j,C), (u_j, w_i), t) to A_{G∗n}.
            for w in step_schedule.keys():
                transfers = step_schedule[w]['transfers']
                load_U = step_schedule[w]['load_U']

                for i in range(n):
                    new_transfers: TransferMap = {}
                    for (v, u), fraction in transfers.items():
                        for j in range(n):
                            new_transfers[((v, j), (u, j))] = fraction

                    A_prime[t][(w, i)] = {
                        'load_U': load_U,
                        'transfers': new_transfers
                    }

        # Divide shard S into equal-sized chunks C1, . . . ,C_{nd}. Given u_i, u_j ∈ V_{G∗n} with i != j , add ((ui,C_α), (v_α, u_j), tmax + 1) to A_{G∗n} for each (v1, u_j), ... , (v_{nd} , u_j) ∈ E_{G∗n}, where tmax is the max comm step in A_G.
        t_final = TimeStep(t_max + 1)
        A_prime[t_final] = {}

        fraction_per_ring_link = Fraction(1.0 / (n * d))

        for u in nodes:
            for j in range(n):
                u_j = (u, j)
                vs = G_prime.predecessors(u_j)

                A_prime[t_final][u_j] = {
                    'load_U': fraction_per_ring_link, 'transfers': {}}

                for i in range(n):
                    if i != j:
                        u_i = (u, i)
                        for v_alpha in vs:
                            A_prime[t_final][u_j]['transfers'][(
                                u_i, v_alpha)] = fraction_per_ring_link

    return G_prime, A_prime


def cartesian_product_expansion(G1: nx.DiGraph, G2: nx.DiGraph) -> nx.DiGraph:

    G_product = nx.DiGraph()

    nodes1 = list(G1.nodes())
    nodes2 = list(G2.nodes())

    new_nodes = [(u, v) for u in nodes1 for v in nodes2]
    G_product.add_nodes_from(new_nodes)

    for u1, u2 in G1.edges():
        for v in nodes2:
            G_product.add_edge((u1, v), (u2, v))

    for v1, v2 in G2.edges():
        for u in nodes1:
            G_product.add_edge((u, v1), (u, v2))

    return G_product


if __name__ == '__main__':
    from visualize_graph import *
    from bfb_schedule import *

    # G = nx.DiGraph()
    # nodes = ['a', 'b', 'c', 'd']
    # nx.add_cycle(G, nodes)
    # # visualize_digraph(G, 'original')
    # A = BFB(G)
    # print_schedule(A)
    # G_prime, A_prime = degree_expansion(G, A, 2)
    # # visualize_digraph(G_prime, 'degree expansion')
    # print_schedule(A_prime)

    G = nx.DiGraph()
    nodes = ['a', 'b', 'c', 'd']
    edges = [('a', 'c'), ('c', 'a'), ('a', 'd'), ('d', 'a'),
             ('b', 'c'), ('c', 'b'), ('b', 'd'), ('d', 'b')]
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)
    # visualize_digraph(G, 'original')
    A = BFB(G)
    print_schedule(A)
    G_prime, A_prime = line_graph_expansion(G, A)
    # visualize_digraph(G_prime, 'line graph expansion')
    print_schedule(A_prime)
