import networkx as nx
import matplotlib.pyplot as plt


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
                           arrows=True,          # 明确显示箭头
                           arrowsize=20,         # 调整箭头大小
                           width=2)

    # 5. 绘制节点标签 (节点ID)
    nx.draw_networkx_labels(G, pos, font_size=12, font_color='black')

    # 6. 设置标题和显示
    plt.title(title, fontsize=15)
    plt.axis('off')  # 隐藏坐标轴
    plt.show()


if __name__ == "__main__":
    G_ring = nx.DiGraph()
    nx.add_cycle(G_ring, [0, 1, 2, 3])

    visualize_digraph(G_ring, "Directed Ring Topology (R4)")
