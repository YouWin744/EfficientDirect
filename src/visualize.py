import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, Tuple, NewType, TypedDict, Any, NamedTuple

# 假设这些类型定义都来自于 schedule_type 模块
from schedule_type import Node, Schedule, TransferMap, TransferKey


def visualize_digraph(G: nx.DiGraph, title: str):

    # 1. 准备绘图画布
    plt.figure(figsize=(6, 6))

    # 2. 选择布局
    # spring_layout: 默认，像弹簧一样把节点分散开
    # circular_layout: 适用于环形、周期性拓扑
    pos = nx.spring_layout(G, seed=42)

    # 3. 绘制节点
    nx.draw_networkx_nodes(G, pos,
                           node_size=800,
                           node_color="#DADADA",
                           edgecolors='lightgray',
                           linewidths=1.5)

    # 4. 绘制边（关键：设置 arrows=True）
    nx.draw_networkx_edges(G, pos,
                           edgelist=G.edges(),
                           edge_color='gray',
                           arrows=True,
                           arrowsize=20,
                           width=2)

    # 5. 绘制节点标签 (节点ID)
    nx.draw_networkx_labels(G, pos, font_size=12, font_color='black')

    # 6. 设置标题和显示
    plt.title(title, fontsize=15)
    plt.axis('off')
    plt.show()


def visualize_schedule(G: nx.DiGraph, schedule: Schedule, source_node: Node):

    time_steps = sorted(schedule.keys())

    if not time_steps:
        print("Schedule is empty, nothing to visualize.")
        return

    # 1. 准备布局，在所有时间片使用相同的布局，保持一致性
    try:
        pos = nx.spring_layout(G, seed=42)
    except nx.NetworkXException:
        pos = nx.spring_layout(G)

    # 2. 遍历每个时间步并绘图
    for t in time_steps:
        step_schedule = schedule[t]

        # 存储当前时间步所有活跃边的信息
        # 键是 (w, u)，值是包含 total_load 的字典
        active_transfers: Dict[Tuple[Node, Node], Dict[str, Any]] = {}

        # 遍历所有目的节点 u
        for u, entry in step_schedule.items():
            transfers: TransferMap = entry['transfers']

            for transfer_key, fraction in transfers.items():
                v = transfer_key.from_node
                w = transfer_key.via_node

                # --- 核心修改点：只筛选 from_node 是 source_node 的传输 ---
                if v != source_node:
                    continue
                # --------------------------------------------------------

                # 实际发生的传输边是 w -> u
                edge_key = (w, u)

                if edge_key not in active_transfers:
                    active_transfers[edge_key] = {
                        'total_load': 0.0,
                        'labels': []
                    }

                # 累加来自 source_node 的流量
                active_transfers[edge_key]['total_load'] += fraction
                active_transfers[edge_key]['labels'].append(
                    f"{v}: {fraction:.4f}")

        # 3. 准备绘图参数
        plt.figure(figsize=(8, 8))

        all_edges = G.edges()
        active_edges = list(active_transfers.keys())
        # 注意：inactive_edges 应该是不在 active_edges 列表中的所有边，无论它们是否在 schedule 中有其他流量
        inactive_edges = [
            edge for edge in all_edges if edge not in active_edges]

        edge_labels = {}

        for edge in active_edges:
            load_data = active_transfers[edge]
            # 标签只显示总负载，此时 total_load 已经是所有来自 source_node 的流量之和
            label_text = f"{load_data['total_load']:.4f}"
            edge_labels[edge] = label_text

        # 4. 绘制图形

        # 绘制节点，源节点高亮
        node_colors = ["#FFDDDD" if node ==
                       source_node else "#DADADA" for node in G.nodes()]

        nx.draw_networkx_nodes(G, pos,
                               node_size=1000,
                               node_color=node_colors,
                               edgecolors='lightgray',
                               linewidths=1.5)

        # 绘制非活跃边（灰色虚线）
        nx.draw_networkx_edges(G, pos,
                               edgelist=inactive_edges,
                               edge_color='gray',
                               arrows=True,
                               arrowsize=20,
                               width=1.5,
                               style='dashed')

        # 绘制活跃边（红色粗线）
        nx.draw_networkx_edges(G, pos,
                               edgelist=active_edges,
                               edge_color='red',
                               arrows=True,
                               arrowsize=25,
                               width=3.0)

        # 绘制节点标签
        nx.draw_networkx_labels(G, pos, font_size=12, font_color='black')

        # 绘制边的标签
        nx.draw_networkx_edge_labels(G, pos,
                                     edge_labels=edge_labels,
                                     font_color='red',
                                     font_size=10,
                                     bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', boxstyle="round,pad=0.2"))

        # 5. 设置标题和显示/保存
        plt.title(
            f"Schedule Time Step t = {t} (Source: {source_node})", fontsize=15)
        plt.axis('off')

        plt.show()


if __name__ == "__main__":
    # 假设 bfb_schedule.py 已经被修复，可以正常导入 BFB 函数
    from bfb_schedule import BFB, print_schedule

    # 示例 1: 环形图 (原始示例)
    # G_ring = nx.DiGraph()
    # nx.add_cycle(G_ring, [0, 1, 2, 3])

    # visualize_digraph(G_ring, "Directed Ring Topology (R4)")

    # ------------------------------------------------------
    # 示例 2: 使用 visualize_schedule

    G_example = nx.DiGraph()
    nodes_ex = ['s', 'v1', 'v2', 'u1', 'u2']
    G_example.add_nodes_from(nodes_ex)
    G_example.add_edges_from([
        ('s', 'v1'), ('s', 'v2'),
        ('v1', 'u1'), ('v1', 'u2'),
        ('v2', 'u1'), ('v2', 'u2')
    ])

    source_node_example = 's'

    # 假设 BFB 函数可以计算出 schedule
    # 注意：如果 BFB 依赖于 print_schedule, graph, schedule_type，请确保 bfb_schedule.py 顶部导入正确。
    try:
        schedule_example = BFB(G_example)
        print_schedule(schedule_example)
        visualize_schedule(G_example, schedule_example, source_node_example)
    except NameError:
        print("\nNote: BFB or print_schedule function not found. Please ensure bfb_schedule.py is correctly structured and imported.")
