from typing import NamedTuple
import graph
import math
import networkx as nx
from bfb_schedule import BFB
import utils
import os


class TopologyEntry(NamedTuple):
    N: int
    d: int
    topology: str
    TL: int
    TB: float           # estimated bandwidth
    BW_optimal: bool    # if True, has optimal bandwidth; if False, may not have

    def print(self):
        bw_opt = "Yes" if self.BW_optimal else "No"
        print(
            f"Topology: {self.topology}, N: {self.N}, d: {self.d}, TL: {self.TL}, TB: {self.TB:.4f}, BW optimal: {bw_opt}")


def line_graph_exp(T: TopologyEntry) -> TopologyEntry:
    N = T.d * T.N
    d = T.d
    topology = f'Line({T.topology})'
    TL = T.TL + 1
    TB = T.TB + 1 / T.N
    return TopologyEntry(N, d, topology, TL, TB, False)


def degree_exp(T: TopologyEntry, n: int) -> TopologyEntry:
    N = n * T.N
    d = n * T.d
    topology = f'Deg({n}, {T.topology})'
    TL = T.TL + 1
    TB = T.TB + (n - 1) / (n * T.N)
    return TopologyEntry(N, d, topology, TL, TB, True if T.BW_optimal else False)


def cartesian_power(T: TopologyEntry, n: int) -> TopologyEntry:
    N = T.N ** n
    d = T.d * n
    topology = f'Car({n}, {T.topology})'
    TL = T.TL * n
    TB = T.TB * T.N / (T.N - 1) * (T.N ** n - 1) / (T.N ** n)
    return TopologyEntry(N, d, topology, TL, TB, True if T.BW_optimal else False)


def cartessian_prod(T1: TopologyEntry, T2: TopologyEntry) -> TopologyEntry:
    assert T1.BW_optimal and T2.BW_optimal, "Both topologies must be BW optimal"
    N = T1.N * T2.N
    d = T1.d + T2.d
    topology = f'Car({T1.topology}, {T2.topology})'
    TL = T1.TL + T2.TL
    TB = (N - 1) / N
    return TopologyEntry(N, d, topology, TL, TB, True)


class TopologyFinder:
    def __init__(self, max_N, max_d) -> None:
        self.max_N = max_N
        self.max_d = max_d
        self.topology_table = {n: {d: [] for d in range(
            1, max_d + 1)} for n in range(1, max_N + 1)}

    def load_DistReg_topologies(self, filepath: str) -> None:
        with open(filepath, 'r') as f:
            lines = f.readlines()

        for line in lines[1:]:  # Skip header
            parts = line.strip().split(',')
            if len(parts) < 6:
                continue

            name = int(parts[0])
            node_num = int(parts[1])
            degree = int(parts[2])
            diameter = int(parts[3])

            tp = TopologyEntry(
                node_num, degree, f'DistReg({name})', diameter, 1 - 1 / node_num, True)
            self.try_insert(tp)

    def basic_graph(self, n, d) -> list[TopologyEntry]:
        tps: list[TopologyEntry] = []

        optimal_B = (n - 1) / n

        # uniring
        if d == 1:
            tps.append(TopologyEntry(
                n, d, f"UniRing({n})", n - 1, optimal_B, True))

        # biring
        if d == 2:
            tps.append(TopologyEntry(
                n, d, f"BiRing({n})", n - 1, optimal_B, True))

        # circulant(only 2d)
        if d == 4 and n >= 5:
            a = math.floor(math.sqrt((n - 2) / 2))
            G = graph.circulant_graph(n, [a, a + 1])
            tps.append(TopologyEntry(
                n, d, f"C({n}, [{a}, {a + 1}])", nx.diameter(G), optimal_B, True))

        # complete
        if d == n - 1:
            tps.append(TopologyEntry(
                n, d, f"K({n})", 1, optimal_B, True))

        # complete bipartite
        if d == n // 2 and n % 2 == 0:
            tps.append(TopologyEntry(
                n, d, f"K({d}, {d})", 2, optimal_B, True))

        # diamond
        if d == 2 and n == 8:
            tps.append(TopologyEntry(
                n, d, f"diamond", 3, optimal_B, True))

        # DBJ
        '''TODO'''

        # DBJMod
        if d == 2 and n == 8:
            tps.append(TopologyEntry(
                n, d, f"DBJ(2,3)", 4, optimal_B, True))
        if d == 2 and n == 16:
            tps.append(TopologyEntry(
                n, d, f"DBJ(2,4)", 5, optimal_B, True))
        if d == 3 and n == 9:
            tps.append(TopologyEntry(
                n, d, f"DBJ(3,2)", 3, optimal_B, True))
        if d == 4 and n == 16:
            tps.append(TopologyEntry(
                n, d, f"DBJ(4,2)", 3, optimal_B, True))

        # DistReg
        # handled in load_DistReg_topologies()

        # generalized kautz
        if n == d + 1:
            tps.append(TopologyEntry(
                n, d, f"Pi({d},{n})", 1, optimal_B, True))

        # '''TODO'''
        # generalized kautz graph 有自环，变换后不一定是正则图
        # elif n > d + 1:
        #     G = graph.generalized_kautz_graph(d, n)
        #     A = BFB(G, False)
        #     tl, tb = utils.get_TL_TB(G, A)

        #     tps.append(TopologyEntry(n, d, f"g_kautz({d},{n})", tl, tb, False))

        return tps

    def try_insert(self, tp: TopologyEntry) -> None:
        if tp.N <= self.max_N and tp.d <= self.max_d:
            self.topology_table[tp.N][tp.d].append(tp)

    def search(self, print_details=False) -> None:
        dist_reg_path = 'DistReg/graph.csv'
        if os.path.exists(dist_reg_path):
            self.load_DistReg_topologies(dist_reg_path)

        for n in range(2, self.max_N + 1):
            for d in range(1, self.max_d + 1):
                tps = self.basic_graph(n, d)
                self.topology_table[n][d].extend(tps)
                self.topology_table[n][d] = utils.pareto_frontier(
                    self.topology_table[n][d], key1=lambda x: x.TL, key2=lambda x: x.TB, eps=1e-4)

                for tp in self.topology_table[n][d]:
                    if tp.d > 1:
                        self.try_insert(line_graph_exp(tp))
                    self.try_insert(degree_exp(tp, 2))
                    self.try_insert(cartesian_power(tp, 2))
                    self.try_insert(cartesian_power(tp, 3))
                    '''TODO'''
                    # more expansion strategies

                if print_details:
                    print(f"\nN={n}, d={d}:\n")
                    for tp in self.topology_table[n][d]:
                        tp.print()

    def print_topologies(self) -> None:
        for n in range(2, self.max_N + 1):
            for d in range(1, self.max_d + 1):
                print(f"\nN={n}, d={d}:\n")
                tps = self.topology_table[n][d]
                for tp in tps:
                    tp.print()


if __name__ == "__main__":
    tf = TopologyFinder(256, 4)
    tf.search(print_details=True)
    # tf.print_topologies()
