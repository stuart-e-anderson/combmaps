from vennmaplib import plantri_graphs, CombinatorialMap

def test_one_graph(n=7):
    print(f"Streaming Plantri graphs with {n} vertices...")
    for adj in plantri_graphs(n):
        cmap = CombinatorialMap()
        cmap.build_from_adjacency(adj)
        cmap.compute_faces()
        dual = cmap.compute_dual_adjacency()

        print("\n🔗 Primal adjacency:")
        for v in sorted(cmap.vertex_to_darts):
            targets = [d.target for d in cmap.vertex_to_darts[v]]
            print(f"  Vertex {v}: {targets}")

        print("\n🌀 Dual adjacency (faces):")
        for f, neighbors in dual.items():
            print(f"  Face {f}: {neighbors}")

        print(f"\n✅ Total darts: {len(cmap.darts)}")
        print(f"✅ Total faces: {len(cmap.faces)}")
        break  # Remove break to test all graphs

if __name__ == "__main__":
    test_one_graph()

