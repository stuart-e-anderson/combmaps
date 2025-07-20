import subprocess

def stream_plantri_binary(n_vertices, extra_args=[]):
    args = ['./plantri', '-p'] + extra_args + [str(n_vertices)]
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return process.stdout


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


def plantri_graphs(n_vertices, extra_args=[]):
    stream = stream_plantri_binary(n_vertices, extra_args)
    while True:
        graph = read_plantri_graph(stream)
        if graph is None:
            break
        yield graph

