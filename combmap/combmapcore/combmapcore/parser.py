import os
import subprocess


def stream_plantri_binary(n_vertices=16, extra_args=None):
    if extra_args is None:
        extra_args = []

    binary_path = os.path.join(os.path.dirname(__file__), "..", "plantri")
    binary_path = os.path.abspath(binary_path)

    args = [binary_path, "-q", str(n_vertices)] + extra_args
    print(f"🔧 Launching Plantri quadrangulations with: {args}")

    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return process.stdout


def plantri_graphs_planarcode_stream(stream):
    # Skip 15-byte planar_code header
    stream.read(15)

    while True:
        n_byte = stream.read(1)
        if not n_byte:
            break  # EOF

        n = n_byte[0]
        rotation = {}

        for i in range(n):
            neighbors = []
            while True:
                byte = stream.read(1)
                if not byte:
                    raise EOFError("Unexpected EOF while reading neighbor list")
                v = byte[0]
                if v == 0:
                    break
                neighbors.append(v - 1)  # Convert to 0-based
            rotation[i] = neighbors

        yield rotation

