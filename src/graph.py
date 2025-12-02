import networkx as nx
from typing import List, Tuple


from expansion import cartesian_product_expansion


def create_ring(n: int, directed: bool = True) -> nx.DiGraph:
    G = nx.DiGraph()
    nodes = list(range(n))
    nx.add_cycle(G, nodes)
    if not directed:
        edges = list(G.edges())
        reverse_edges = [(v, u) for u, v in edges]
        G.add_edges_from(reverse_edges)
    return G


def create_circulant_graph(n: int, generators: List[int], directed: bool = False) -> nx.DiGraph:
    G = nx.DiGraph()
    G.add_nodes_from(range(n))

    edges = set()

    for i in range(n):
        for a in generators:
            if a == 0:
                continue

            target_plus = (i + a) % n
            edges.add((i, target_plus))

            is_half = (n % 2 == 0) and (a == n / 2)

            if not directed or (directed and not is_half and a != 0):
                target_minus = (i - a) % n

                if i != target_minus:
                    edges.add((i, target_minus))

    if not directed:
        final_edges = set()
        for u, v in edges:
            final_edges.add((u, v))
            final_edges.add((v, u))
        G.add_edges_from(final_edges)

    else:
        G.add_edges_from(edges)

    return G


def create_complete_graph(n: int) -> nx.DiGraph:
    return nx.complete_graph(n, create_using=nx.DiGraph())


def create_torus(dimensions: List[int]) -> nx.DiGraph:
    assert (len(dimensions) > 0)
    G = create_ring(dimensions[0], False)
    for d in dimensions[1:]:
        G_prime = create_ring(d, False)
        G = cartesian_product_expansion(G, G_prime)
    return G


def create_generalized_kautz_graph(d: int, m: int) -> nx.DiGraph:
    assert(d >= 1 and m >= 1)

    G = nx.DiGraph()
    G.add_nodes_from(range(m))
    edges = []

    for x in range(m):
        for a in range(1, d + 1):
            y = (-d * x - a) % m
            edges.append((x, y))

    G.add_edges_from(edges)
    return G


def _main1():
    G = create_circulant_graph(32, [2, 5, 7, 3, 11])
    A = BFB(G)
    utils.print_schedule(A, False)
    utils.print_schedule_bound(G)


def _main2():
    G = create_torus([4, 4])
    # G = create_torus([3, 3, 2])
    A = BFB(G)
    utils.print_schedule(A, True)
    utils.print_schedule_bound(G)
    visualize.visualize_digraph(G)
    # visualize.visualize_schedule(G, A, list(G.nodes)[0])
    visualize.visualize_schedule(G, A, list(G.nodes)[1])


def _main3():
    G = create_ring(6, False)
    A = BFB(G)
    utils.print_schedule(A, False)
    utils.print_schedule_bound(G)
    visualize.visualize_digraph(G)
    visualize.visualize_schedule(G, A, list(G.nodes)[0])


def _main4():
    G = create_generalized_kautz_graph(3, 16)
    A = BFB(G)
    utils.print_schedule(A, False)
    utils.print_schedule_bound(G)
    visualize.visualize_digraph(G)
    visualize.visualize_schedule(G, A, list(G.nodes)[0])


if __name__ == '__main__':
    from bfb_schedule import BFB
    import utils
    import visualize

    # _main2()    # torus
    # _main3()    # bfb on bidirectional ring
    _main4()    # Generalized Kautz Graph
