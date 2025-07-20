def read_plantri_graph(stream):
    n_byte = stream.read(1)
    if not n_byte:
        return None

    n = int.from_bytes(n_byte, 'big')
    adj = {v: [] for v in range(n)}
    
    for v in range(n):
        while True:
            byte = stream.read(1)
            if not byte:
                return None
            u = int.from_bytes(byte, 'big')
            if u == 0:
                break
            adj[v].append(u - 1)  # Convert 1-based to 0-based

    return adj

