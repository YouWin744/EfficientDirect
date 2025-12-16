from typing import NamedTuple
import graph
import math
import networkx as nx
from bfb_schedule import BFB
import utils
import os
from tqdm import tqdm


class TopologyEntry(NamedTuple):
    N: int
    d: int
    topology: str
    TL: int
    TB: float           # estimated bandwidth
    BW_optimal: bool    # if True, has optimal bandwidth; if False, may not have
    nest_level: int

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
    return TopologyEntry(N, d, topology, TL, TB, False, T.nest_level + 1)


def degree_exp(T: TopologyEntry, n: int) -> TopologyEntry:
    N = n * T.N
    d = n * T.d
    topology = f'Deg({n}, {T.topology})'
    TL = T.TL + 1
    TB = T.TB + (n - 1) / (n * T.N)
    return TopologyEntry(N, d, topology, TL, TB, True if T.BW_optimal else False, T.nest_level + 1)


def cartesian_power(T: TopologyEntry, n: int) -> TopologyEntry:
    N = T.N ** n
    d = T.d * n
    topology = f'Car({n}, {T.topology})'
    TL = T.TL * n
    TB = T.TB * T.N / (T.N - 1) * (T.N ** n - 1) / (T.N ** n)
    return TopologyEntry(N, d, topology, TL, TB, True if T.BW_optimal else False, T.nest_level + 1)


def cartessian_prod(T1: TopologyEntry, T2: TopologyEntry) -> TopologyEntry:
    assert T1.BW_optimal and T2.BW_optimal, "Both topologies must be BW optimal"
    N = T1.N * T2.N
    d = T1.d + T2.d
    topology = f'Car({T1.topology}, {T2.topology})'
    TL = T1.TL + T2.TL
    TB = (N - 1) / N
    return TopologyEntry(N, d, topology, TL, TB, True, T1.nest_level + T2.nest_level + 1)


class TopologyFinder:
    def __init__(self, max_N, max_d) -> None:
        self.max_N = max_N
        self.max_d = max_d
        self.topology_table = {n: {d: [] for d in range(
            1, max_d + 1)} for n in range(1, max_N + 1)}

        self.init_topology_table()

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
                node_num, degree, f'DistReg({name})', diameter, 1 - 1 / node_num, True, 0)
            self.try_insert(tp)

    def init_topology_table(self) -> None:
        '''
        init topology table with topologies with perticular structures,
        including: DBJMod, diamond, DistReg
        '''
        # DBJMod
        self.topology_table[8][2].append(TopologyEntry(
            8, 2, "DBJMod(2,3)", 4, 7 / 8, True, 0))
        self.topology_table[16][2].append(TopologyEntry(
            16, 2, "DBJMod(2,4)", 5, 15 / 16, True, 0))
        self.topology_table[9][3].append(TopologyEntry(
            9, 3, "DBJMod(3,2)", 3, 8 / 9, True, 0))
        self.topology_table[16][4].append(TopologyEntry(
            16, 4, "DBJMod(4,2)", 3, 15 / 16, True, 0))
        # diamond
        self.topology_table[8][2].append(TopologyEntry(
            8, 2, "diamond", 3, 7 / 8, True, 0))

        # DistReg
        dist_reg_path = 'DistReg/graph.csv'
        if os.path.exists(dist_reg_path):
            self.load_DistReg_topologies(dist_reg_path)

    def basic_graph_set1(self, n, d) -> list[TopologyEntry]:
        '''
        uniring, biring
        '''
        tps: list[TopologyEntry] = []

        optimal_B = (n - 1) / n

        # uniring
        if d == 1:
            tps.append(TopologyEntry(
                n, d, f"UniRing({n})", n - 1, optimal_B, True, 0))

        # biring
        if d == 2:
            tps.append(TopologyEntry(
                n, d, f"BiRing({n})", n - 1, optimal_B, True, 0))

        return tps

    def basic_graph_set2(self, n, d) -> list[TopologyEntry]:
        '''
        circulant, complete, complete bipartite, DBJ, generalized kautz(with BW optimality guarantee)
        '''
        tps: list[TopologyEntry] = []

        optimal_B = (n - 1) / n

        # circulant(only 2d)
        if d == 4 and n >= 5:
            '''TODO: why?'''
            a = math.floor(math.sqrt((n - 2) / 2))
            G = graph.circulant_graph(n, [a, a + 1])
            tps.append(TopologyEntry(
                n, d, f"C({n}, [{a}, {a + 1}])", nx.diameter(G), optimal_B, True, 0))

        # complete
        if d == n - 1:
            tps.append(TopologyEntry(
                n, d, f"K({n})", 1, optimal_B, True, 0))

        # complete bipartite
        if d == n // 2 and n % 2 == 0:
            tps.append(TopologyEntry(
                n, d, f"K({d}, {d})", 2, optimal_B, True, 0))

        # DBJ
        '''TODO'''

        # generalized kautz with BW optimality guarantee
        if n == d + 1:
            tps.append(TopologyEntry(
                n, d, f"Pi({d},{n})", 1, optimal_B, True, 0))

        return tps

    def basic_graph_set3(self, n, d) -> list[TopologyEntry]:
        '''
        generalized kautz(with no BW optimality guarantee)
        '''
        tps: list[TopologyEntry] = []

        if n > d + 1:
            G = graph.generalized_kautz_graph(d, n)
            if nx.is_strongly_connected(G):
                A = BFB(G, False)
                tl, tb = utils.get_TL_TB(G, A)
                tps.append(TopologyEntry(
                    n, d, f"g_kautz({d},{n})", tl, tb, False, 0))

        return tps

    def try_insert(self, tp: TopologyEntry) -> bool:
        if tp.N <= self.max_N and tp.d <= self.max_d:
            self.topology_table[tp.N][tp.d].append(tp)
            return True
        return False

    def search(self, print_tqdm: bool = False) -> None:
        # add graphs from basic graph set 1
        # try cartesian product expansion and cartesian power expansion
        n_range1 = range(2, self.max_N + 1)
        if print_tqdm:
            n_range1 = tqdm(n_range1, desc="Pass1")
        for n in n_range1:
            for d in range(1, self.max_d + 1):
                tps = self.basic_graph_set1(n, d)
                self.topology_table[n][d].extend(tps)
                self.topology_table[n][d] = utils.pareto_frontier(
                    self.topology_table[n][d], key1=lambda x: x.TL, key2=lambda x: x.TB, eps2=1e-4, key3=lambda x: x.nest_level)

                for n2 in range(2, n + 1):
                    for d2 in range(1, d + 1):
                        if n * n2 <= self.max_N and d + d2 <= self.max_d:
                            for tp1 in self.topology_table[n][d]:
                                for tp2 in self.topology_table[n2][d2]:
                                    self.try_insert(cartessian_prod(tp1, tp2))

        # add graphs from basic graph set 2
        # try line graph, degree, cartesian power expansion
        n_range2 = range(2, self.max_N + 1)
        if print_tqdm:
            n_range2 = tqdm(n_range2, desc="Pass2")
        for n in n_range2:
            for d in range(1, self.max_d + 1):
                tps = self.basic_graph_set2(n, d)
                self.topology_table[n][d].extend(tps)
                self.topology_table[n][d] = utils.pareto_frontier(
                    self.topology_table[n][d], key1=lambda x: x.TL, key2=lambda x: x.TB, eps2=1e-4, key3=lambda x: x.nest_level)

                for tp in self.topology_table[n][d]:
                    # line graph expansion
                    if tp.d > 1:
                        self.try_insert(line_graph_exp(tp))

                    # degree expansion
                    i = 2
                    while self.try_insert(degree_exp(tp, i)):
                        i += 1

                    # cartesian power expansion
                    i = 2
                    while self.try_insert(cartesian_power(tp, i)):
                        i += 1

        # add graphs from basic graph set 3
        # n_range3 = range(2, self.max_N + 1)
        # if print_tqdm:
        #     n_range3 = tqdm(n_range3, desc="Pass3")
        # for n in n_range3:
        #     for d in range(1, self.max_d + 1):
        #         tps = self.basic_graph_set3(n, d)
        #         self.topology_table[n][d].extend(tps)
        #         self.topology_table[n][d] = utils.pareto_frontier(
        #             self.topology_table[n][d], key1=lambda x: x.TL, key2=lambda x: x.TB, eps2=1e-4)

    def print_topologies(self) -> None:
        for n in range(2, self.max_N + 1):
            for d in range(1, self.max_d + 1):
                print(f"\nN={n}, d={d}:\n")
                tps = self.topology_table[n][d]
                for tp in tps:
                    tp.print()


if __name__ == "__main__":
    tf = TopologyFinder(256, 4)
    tf.search(print_tqdm=True)
    tf.print_topologies()
