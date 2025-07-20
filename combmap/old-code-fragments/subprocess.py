def stream_plantri_output(n_vertices):
    process = subprocess.Popen(
        ["./plantri", str(n_vertices)],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL
    )
    return process.stdout


