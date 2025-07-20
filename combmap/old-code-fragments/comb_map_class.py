class CombinatorialMap:
    def __init__(self):
        self.darts = []
        self.vertex_to_darts = {}  # Maps each vertex to its outgoing darts
        self.faces = []            # List of faces (each as list of darts)

    def add_edge(self, u, v):
        d1 = Dart(u, v)
        d2 = Dart(v, u)
        d1.reversal = d2
        d2.reversal = d1
        self.darts.extend([d1, d2])

        for dart in [d1, d2]:
            if dart.origin not in self.vertex_to_darts:
                self.vertex_to_darts[dart.origin] = []
            self.vertex_to_darts[dart.origin].append(dart)

        return d1, d2

