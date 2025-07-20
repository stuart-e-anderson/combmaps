def compute_jordan_curves(cmap):
    """
    Decompose a 4-regular planar graph into Jordan curves (cycles).
    Returns a list of lists of darts, one per curve.
    """
    curves = []
    visited = set()
    for dart in cmap.darts:
        if dart not in visited:
            curve = []
            current = dart
            while current not in visited:
                visited.add(current)
                curve.append(current)
                current = current.reversal.next.next
            curves.append(curve)
    return curves

def generate_bitstrings(cmap, num_curves):
    """
    Generate region bitstrings based on curve inclusion.
    Placeholder: assumes each face assigned an index per curve.
    """
    # For now, assign empty bitstrings
    bits = {face_index: [0]*num_curves for face_index in range(len(cmap.faces))}
    return bits

def save_gauss_code(code, path):
    with open(path, 'w') as f:
        for entry in code:
            f.write(str(entry) + '\n')
