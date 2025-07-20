def read_next_graph(stream):
    n_byte = stream.read(1)
    if not n_byte:
        return None
    n = int.from_bytes(n_byte, byteorder='big')
    adjacency = [[] for _ in range(n)]
    
    for i in range(n):
        while True:
            byte = stream.read(1)
            v = int.from_bytes(byte, byteorder='big')
            if v == 0:
                break
            adjacency[i].append(v - 1)  # 1-based to 0-based indexing
    return adjacency

