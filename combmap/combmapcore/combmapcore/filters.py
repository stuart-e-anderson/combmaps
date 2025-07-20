def is_4_regular(adj_list):
    """Check if every vertex has degree 4."""
    return all(len(neighbors) == 4 for neighbors in adj_list.values())

def has_valence_distribution(adj_list, target_counts):
    """
    Check valence distribution against a target.
    Example: {3: 10, 4: 5} means 10 vertices of valence 3, 5 of valence 4.
    """
    from collections import Counter
    valences = [len(neighbors) for neighbors in adj_list.values()]
    count = Counter(valences)
    for k, v in target_counts.items():
        if count.get(k, 0) != v:
            return False
    return True

