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

