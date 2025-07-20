# In gauss_tracer.py

def trace_gauss_walk_dual(dual_adj, start_node, initial_target, rule):
    walk = [start_node, initial_target]
    visited = {start_node, initial_target}
    prev = start_node
    current = initial_target
    while True:
        neighbors = dual_adj.get(current, [])
        if len(neighbors) != 4: break
        try:
            i = neighbors.index(prev)
        except ValueError: break
        next_index = rule(i, len(neighbors))
        if next_index >= len(neighbors): break
        next_vertex = neighbors[next_index]
        if next_vertex == start_node:
            walk.append(start_node)
            break
        if next_vertex in visited: break
        walk.append(next_vertex)
        visited.add(next_vertex)
        prev = current
        current = next_vertex
    return walk

def trace_all_gauss_walks(dual_adj, rule):
    cycles = []
    seen_cycles = set()
    for start_node in dual_adj:
        for initial_target in dual_adj.get(start_node, []):
            walk = trace_gauss_walk_dual(dual_adj, start_node, initial_target, rule)
            if len(walk) > 2 and walk[0] == walk[-1]:
                cycle_nodes = frozenset(walk)
                if cycle_nodes not in seen_cycles:
                    seen_cycles.add(cycle_nodes)
                    cycles.append(walk)
    return cycles
