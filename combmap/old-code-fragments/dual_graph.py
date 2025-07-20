def compute_dual_adjacency(self):
    dual_adj = {i: set() for i in range(len(self.faces))}
    for dart in self.darts:
        f1 = dart.face
        f2 = dart.reversal.face
        if f1 != f2:
            dual_adj[f1].add(f2)
    # Convert sets to sorted lists
    return {f: sorted(list(neighbors)) for f, neighbors in dual_adj.items()}

