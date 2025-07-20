def plantri_graphs(n_vertices):
    stream = stream_plantri_binary(n_vertices)
    while True:
        graph = read_plantri_graph(stream)
        if graph is None:
            break
        yield graph

