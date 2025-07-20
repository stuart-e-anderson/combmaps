def build_from_adjacency(self, adj_list):
    # adj_list: {vertex: [neighbor1, neighbor2, ...]}
    edge_map = {}  # To avoid duplicate edges

    for u in adj_list:
        for v in adj_list[u]:
            if (u, v) not in edge_map and (v, u) not in edge_map:
                d1, d2 = self.add_edge(u, v)
                edge_map[(u, v)] = d1
                edge_map[(v, u)] = d2

    # Link darts cyclically around each vertex
    for v, darts in self.vertex_to_darts.items():
        n = len(darts)
        for i in range(n):
            darts[i].next = darts[(i + 1) % n]

