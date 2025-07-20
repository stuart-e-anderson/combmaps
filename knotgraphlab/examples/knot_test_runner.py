# In knot_test_runner.py

import networkx as nx
from combmapcore.parser import plantri_graphs_planarcode_stream, stream_plantri_binary
from combmapcore.combinatorial import CombinatorialMap
from knotgraphlab.gauss_tracer import trace_all_gauss_walks
from knotgraphlab.viewer import visualize_dual_graph_with_cycle

def main():
    gauss_rule = lambda i, n: (i + 2) % n
    stream = stream_plantri_binary(n_vertices=16)
    for i, rotation in enumerate(plantri_graphs_planarcode_stream(stream), 1):
        cmap = CombinatorialMap()
        cmap.build_from_rotation_system(rotation)
        dual_adj = cmap.compute_dual_adjacency()

        if all(len(neighbors) == 4 for neighbors in dual_adj.values()):
            print(f"\n📤 [#{i}] 4-regular dual — Gauss cycle analysis")
            cycles = trace_all_gauss_walks(dual_adj, rule=gauss_rule)
            if not cycles:
                print("   No cycles found.")
                continue
            
            longest_cycle = max(cycles, key=len)
            print(f"🔗 Longest cycle path:  ", " → ".join(str(v) for v in longest_cycle))
            
            visualize_dual_graph_with_cycle(dual_adj, cmap, i, highlighted_cycle=longest_cycle)
        else:
            print(f"\n📤 [#{i}] Skipped — dual not 4-regular")

if __name__ == "__main__":
    main()
