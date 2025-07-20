class Dart:
    def __init__(self, origin, target):
        self.origin = origin          # Source vertex
        self.target = target          # Target vertex
        self.reversal = None          # Opposite dart (edge in reverse direction)
        self.next = None              # Next dart around origin vertex
        self.face = None              # Face ID this dart borders
        self.index = None             # Optional unique dart ID

    def __repr__(self):
        return f"Dart({self.origin} → {self.target})"

