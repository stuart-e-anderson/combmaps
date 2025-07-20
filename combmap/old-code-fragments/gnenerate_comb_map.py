for adj in plantri_graphs(7):  # Example with 7 vertices
    cmap = CombinatorialMap()
    cmap.build_from_adjacency(adj)
    cmap.compute_faces()
    dual = cmap.compute_dual_adjacency()
    # You now have the primal and dual; use filters, export, or tests here

