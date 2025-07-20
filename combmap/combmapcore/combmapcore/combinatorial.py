# In combmapcore/combinatorial.py

class Dart:
    def __init__(self, origin, target):
        self.origin = origin
        self.target = target
        self.reversal = None
        self.next = None
        self.face = None

    def __repr__(self):
        return f"Dart({self.origin} -> {self.target})"

class CombinatorialMap:
    def __init__(self):
        self.darts = []
        self.vertex_to_darts = {}
        self.faces = []

    def build_from_rotation_system(self, rotation_dict):
        dart_lookup = {}
        for u, neighbors in rotation_dict.items():
            for v in neighbors:
                d = Dart(u, v)
                dart_lookup[(u, v)] = d
                self.darts.append(d)
                self.vertex_to_darts.setdefault(u, []).append(d)
        for (u, v), dart in dart_lookup.items():
            rev = dart_lookup.get((v, u))
            if rev:
                dart.reversal = rev
                rev.reversal = dart
        for u, neighbors in rotation_dict.items():
            ordered_darts = [dart_lookup[(u, v)] for v in neighbors]
            for i, d in enumerate(ordered_darts):
                d.next = ordered_darts[(i + 1) % len(ordered_darts)]

    def compute_faces(self):
        visited = set()
        self.faces = []
        for dart in self.darts:
            if dart not in visited and dart.reversal:
                face = []
                current = dart
                while current not in visited:
                    visited.add(current)
                    face.append(current)
                    current.face = face
                    current = current.reversal.next
                self.faces.append(face)

    def compute_dual_adjacency(self):
        if not self.faces: self.compute_faces()
        face_to_idx = {id(face): i for i, face in enumerate(self.faces)}
        dual_adj = {i: [] for i in range(len(self.faces))}
        for i, face in enumerate(self.faces):
            for dart in face:
                if dart.reversal and dart.reversal.face:
                    neighbor_idx = face_to_idx.get(id(dart.reversal.face))
                    if neighbor_idx is not None and neighbor_idx != i:
                        dual_adj[i].append(neighbor_idx)
        for i in dual_adj:
            dual_adj[i] = list(dict.fromkeys(dual_adj[i]))
        return dual_adj
