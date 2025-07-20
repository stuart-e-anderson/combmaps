class Dart:
    def __init__(self, origin, target):
        self.origin = origin
        self.target = target
        self.reversal = None
        self.cyclic_next = None
        self.face = None

class CombinatorialMap:
    def __init__(self):
        self.darts = []
        self.vertices = set()
        self.faces = []

    def add_edge(self, u, v):
        d1 = Dart(u, v)
        d2 = Dart(v, u)
        d1.reversal = d2
        d2.reversal = d1
        self.darts.extend([d1, d2])
        self.vertices.update([u, v])

