def is_valid_knot_graph(adj_list):
    """
    Apply domain-specific tests to decide whether this graph can represent a knot.
    For now: check for 4-regularity.
    """
    return all(len(neighbors) == 4 for neighbors in adj_list.values())

