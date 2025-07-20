def link_reversals(self):
    edge_map = {}
    for dart in self.darts:
        key = (dart.origin, dart.target)
        edge_map[key] = dart
    for dart in self.darts:
        rev_key = (dart.target, dart.origin)
        dart.reversal = edge_map.get(rev_key)

