class Dart:
    def __init__(self, origin, target):
        self.origin = origin
        self.target = target
        self.reversal = None
        self.next = None
        self.face = None
        self.index = None  # Optional unique ID

    def __repr__(self):
        return f"Dart({self.origin} → {self.target})"


class CombinatorialMap:
    def __init__(self):
        self.darts = []
        self.vertex_to_darts = {}
        self.faces = []

    def add_edge(self, u, v):
        d1 = Dart(u, v)
        d2 = Dart(v, u)
        d1.reversal = d2
        d2.reversal = d1
        self.darts.extend([d1, d2])

        for dart in [d1, d2]:
            self.vertex_to_darts.setdefault(dart.origin, []).append(dart)

        return d1, d2

    def build_from_adjacency(self, adj_list):
        seen = set()
        for u in adj_list:
            for v in adj_list[u]:
                if (u, v) not in seen and (v, u) not in seen:
                    self.add_edge(u, v)
                    seen.add((u, v))
        # Set up cyclic linking
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

