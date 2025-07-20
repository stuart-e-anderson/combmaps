import networkx as nx
import matplotlib.pyplot as plt
import numpy as np


def build_dual_nx_graph(dual_adj):
    G = nx.Graph()
    for node, neighbors in dual_adj.items():
        for nbr in neighbors:
            G.add_edge(node, nbr)
    return G


def circular_layout(G):
    nodes = list(G.nodes())
    n = len(nodes)
    pos = {}
    for i, node in enumerate(nodes):
        angle = 2 * np.pi * i / n
        pos[node] = np.array([np.cos(angle), np.sin(angle)])
    return pos


# In viewer.py

def visualize_dual_graph_with_cycle(dual_adj, highlighted_cycle=None):
    G = build_dual_nx_graph(dual_adj)
    pos = circular_layout(G)

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Use a different color for nodes in the highlighted cycle
    node_colors = ['#22c55e' if node in highlighted_cycle else '#a78bfa' for node in G.nodes()]
    
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=400, ax=ax)
    nx.draw_networkx_edges(G, pos, edge_color='gray', width=1.2, ax=ax)

    if highlighted_cycle:
        # Highlight the edges of the cycle
        cycle_edges = [(highlighted_cycle[i], highlighted_cycle[i + 1]) for i in range(len(highlighted_cycle) - 1)]
        nx.draw_networkx_edges(G, pos, edgelist=cycle_edges, edge_color='#22c55e', width=3, ax=ax)

    labels = {node: str(node) for node in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels, font_size=9, font_color='white', ax=ax)
    
    # Update the title of the plot
    ax.set_title("Dual Graph with Highlighted Gauss Cycle", fontsize=14, color='white')
    
    plt.tight_layout()
    plt.show()
