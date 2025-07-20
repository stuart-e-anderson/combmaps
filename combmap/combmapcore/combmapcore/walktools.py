"""
    Extract closed dart walks (Jordan curves) from the combinatorial map.
    Each walk is a sequence of darts forming a loop via reversal.next traversal.
"""
def extract_walks(cmap):
    walks = []
    visited = set()
    print("Dart count:", len(cmap.darts))
    
    for dart in cmap.darts:
        if dart.reversal is None or dart.next is None:
            print(f"❌ Dart linkage broken: {dart}")
            continue

        if dart in visited:
            continue

        walk = []
        current = dart
        while current not in visited:
            visited.add(current)
            walk.append(current)
            current = current.reversal.next
        walks.append(walk)

    return walks

    walks = []
    visited = set()

    for dart in cmap.darts:
        if dart in visited:
            continue

        walk = []
        current = dart
        while current and current not in visited:
            visited.add(current)
            walk.append(current)
            if current.reversal is None or current.reversal.next is None:
                break  # 🛑 Bail out if linkage is broken
            current = current.reversal.next

        if walk:
            walks.append(walk)

    return walks

