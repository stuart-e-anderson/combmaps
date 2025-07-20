import subprocess

def stream_plantri_binary(n_vertices, extra_args=[]):
    args = ['./plantri', '-p'] + extra_args + [str(n_vertices)]  # -p: planar code output
    process = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL
    )
    return process.stdout

