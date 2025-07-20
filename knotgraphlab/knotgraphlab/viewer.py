# In viewer.py

import networkx as nx
import matplotlib.pyplot as plt

def visualize_dual_graph_with_cycle(dual_adj, cmap, graph_index, highlighted_cycle=None):
    # Create a simple undirected graph from the adjacency data.
    G = nx.Graph(dual_adj)
    pos = None

    try:
        # Let networkx check for planarity and create its own valid embedding object.
        # This is the most robust way to avoid validation errors.
        is_planar, embedding = nx.check_planarity(G, counterexample=False)

        if not is_planar:
            raise ValueError("Graph is not planar according to networkx.")

        # Pass the networkx-generated embedding to the layout function.
        pos = nx.combinatorial_embedding_to_pos(embedding)

    except Exception as e:
        print(f"⚠️ Could not generate planar layout for graph #{graph_index} ({e}). Falling back.")
        pos = nx.spring_layout(G)

    # --- Drawing Logic ---
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 10))
    
    node_colors = ['#22c55e' if node in highlighted_cycle else '#a78bfa' for node in G.nodes()]
    
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=400, ax=ax)
    nx.draw_networkx_edges(G, pos, edge_color='gray', width=1.2, ax=ax)

    if highlighted_cycle:
        cycle_edges = [(highlighted_cycle[i], highlighted_cycle[i + 1]) for i in range(len(highlighted_cycle) - 1)]
        nx.draw_networkx_edges(G, pos, edgelist=cycle_edges, edge_color='#22c55e', width=3, ax=ax)

    labels = {node: str(node) for node in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels, font_size=9, font_color='white', ax=ax)
    ax.set_title(f"Dual Graph #{graph_index} with Highlighted Gauss Cycle", fontsize=14, color='white')
    
    ax.set_aspect('equal')
    plt.tight_layout()
    plt.show()
