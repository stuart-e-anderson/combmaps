class Dart:
    def __init__(self, origin, target):
        self.origin = origin          # Source vertex
        self.target = target          # Target vertex
        self.reversal = None          # Opposite dart
        self.next = None              # Next dart around origin vertex
        self.face = None              # Face index this dart belongs to
        self.index = None             # Optional dart ID

    def __repr__(self):
        return f"Dart({self.origin} → {self.target})"


class CombinatorialMap:
    def __init__(self):
        self.darts = []
        self.vertex_to_darts = {}
        self.faces = []

    def add_edge(self, u, v):
        # Create both darts
        d1 = Dart(u, v)
        d2 = Dart(v, u)
        self.darts.extend([d1, d2])
        for dart in [d1, d2]:
            self.vertex_to_darts.setdefault(dart.origin, []).append(dart)

    def build_from_adjacency(self, adj_list):
        seen = set()
        for u in adj_list:
            for v in adj_list[u]:
                if (u, v) not in seen and (v, u) not in seen:
                    self.add_edge(u, v)
                    seen.add((u, v))
        self.link_reversals()
        self.link_next_darts()

    def link_reversals(self):
        # Efficient reversal linking using dictionary
        edge_map = {}
        for dart in self.darts:
            key = (dart.origin, dart.target)
            edge_map[key] = dart
        for dart in self.darts:
            rev_key = (dart.target, dart.origin)
            dart.reversal = edge_map.get(rev_key)
            if dart.reversal is None:
                raise ValueError(f"Missing reversal for dart {dart}")

    def link_next_darts(self):
        for v, darts in self.vertex_to_darts.items():
            for i in range(len(darts)):
                darts[i].next = darts[(i + 1) % len(darts)]

    def compute_faces(self):
        visited = set()
        for dart in self.darts:
            if dart not in visited:
                face = []
                current = dart
                while current not in visited:
                    visited.add(current)
                    current.face = len(self.faces)
                    face.append(current)
                    current = current.reversal.next
                self.faces.append(face)

    def compute_dual_adjacency(self):
        dual_adj = {i: set() for i in range(len(self.faces))}
        for dart in self.darts:
            f1 = dart.face
            f2 = dart.reversal.face
            if f1 != f2:
                dual_adj[f1].add(f2)
        return {f: sorted(neighbors) for f, neighbors in dual_adj.items()}

