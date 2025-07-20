def compute_dual_adjacency(adj):
    """
    Given a quadrangulation (planar graph), compute the dual graph.
    The dual will be 4-regular, with a vertex for each face.

    Parameters:
        adj (dict): adjacency list of primal graph {v: [u1, u2, ...]}

    Returns:
        dict: adjacency list of the dual graph
    """
    # Face detection via combinatorial map logic
    from combmapcore import CombinatorialMap
    cmap = CombinatorialMap()
    cmap.build_from_adjacency(adj)
    cmap.compute_faces()

    faces = cmap.faces
    face_count = len(faces)
    dual_adj = {i: [] for i in range(face_count)}

    # Build dual edges: if two faces share an edge, they are adjacent in the dual
    edge_to_faces = {}

    for f_idx, face in enumerate(faces):
        edges = [(face[i], face[(i+1) % len(face)]) for i in range(len(face))]
        for u, v in edges:
            key = tuple(sorted(((u.origin, u.target), (v.origin, v.target))))
            edge_to_faces.setdefault(key, []).append(f_idx)

    for face_indices in edge_to_faces.values():
        if len(face_indices) == 2:
            f1, f2 = face_indices
            dual_adj[f1].append(f2)
            dual_adj[f2].append(f1)

    return dual_adj

