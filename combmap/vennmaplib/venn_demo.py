from vennmaplib import plantri_graphs, CombinatorialMap

for adj in plantri_graphs(7):  # stream graphs with 7 vertices
    cmap = CombinatorialMap()
    cmap.build_from_adjacency(adj)
    cmap.compute_faces()
    dual = cmap.compute_dual_adjacency()

    print("Primal vertices:")
    for v in sorted(cmap.vertex_to_darts):
        print(f"  Vertex {v}: {[d.target for d in cmap.vertex_to_darts[v]]}")

    print("Dual graph adjacency:")
    for f, neighbors in dual.items():
        print(f"  Face {f}: {neighbors}")
    break  # Remove to process all graphs

