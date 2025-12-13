import networkx as nx
from typing import List, Tuple


from expansion import cartesian_product_expansion


def ring(n: int, directed: bool = True) -> nx.DiGraph:
    G = nx.DiGraph()
    nodes = list(range(n))
    nx.add_cycle(G, nodes)
    if not directed:
        edges = list(G.edges())
        reverse_edges = [(v, u) for u, v in edges]
        G.add_edges_from(reverse_edges)
    return G


def circulant_graph(n: int, generators: List[int], directed: bool = False) -> nx.DiGraph:
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


def complete_graph(n: int) -> nx.DiGraph:
    return nx.complete_graph(n, create_using=nx.DiGraph())


def torus(dimensions: List[int]) -> nx.DiGraph:
    assert (len(dimensions) > 0)
    G = ring(dimensions[0], False)
    for d in dimensions[1:]:
        G_prime = ring(d, False)
        G = cartesian_product_expansion(G, G_prime)
    return G


def generalized_kautz_graph(d: int, m: int) -> nx.DiGraph:
    assert (d >= 1 and m >= 1)

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
    G = circulant_graph(32, [2, 5, 7, 3, 11])
    A = BFB(G)
    utils.print_schedule(A, False)
    utils.print_schedule_bound(G)


def _main2():
    G = torus([4, 4])
    # G = create_torus([3, 3, 2])
    A = BFB(G)
    utils.print_schedule(A, True)
    utils.print_schedule_bound(G)
    visualize.visualize_digraph(G)
    # visualize.visualize_schedule(G, A, list(G.nodes)[0])
    visualize.visualize_schedule(G, A, list(G.nodes)[1])


def _main3():
    G = ring(6, False)
    A = BFB(G)
    utils.print_schedule(A, False)
    utils.print_schedule_bound(G)
    visualize.visualize_digraph(G)
    visualize.visualize_schedule(G, A, list(G.nodes)[0])


def _main4():
    G = generalized_kautz_graph(2, 17)
    A = BFB(G, False)
    utils.print_schedule(A, False)
    utils.print_schedule_bound(G)
    visualize.visualize_digraph(G)
    # visualize.visualize_schedule(G, A, list(G.nodes)[0])


def _main5():

    def oo(n: int):
        min_diameter = float('inf')
        best_pairs = (0, 0)

        # print(f'n = {n}')
        for a1 in range(1, n // 2):
            a2 = a1 + 1
            G = circulant_graph(n, [a1, a2], False)
            diameter = nx.diameter(G)

            if diameter < min_diameter:
                min_diameter = diameter
                best_pairs = (a1, a2)

        return best_pairs

    n = 4
    pairs = oo(4)
    for i in range(5, 256):
        new_pairs = oo(i)
        if pairs != new_pairs:
            print(f"{n} ~ {i - 1}, {pairs}")
            pairs = new_pairs
            n = i


def _main6():
    # G = circulant_graph(4, [1, 2], False)
    G = circulant_graph(16, [2, 3], False)
    A = BFB(G, False)
    utils.print_schedule(A, False)
    utils.print_schedule_bound(G)
    # visualize.visualize_digraph(G)
    # visualize.visualize_schedule(G, A, list(G.nodes)[0])


def _main7():
    import expansion
    G = complete_graph(3)
    A = BFB(G, False)
    G, A = expansion.degree_expansion(G, A, 2)
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
    # _main4()    # Generalized Kautz Graph
    # _main5()    # circulant test
    # _main6()    # circulant graph
    _main7()
