import subprocess

def stream_plantri_graphs(plantri_args):
    process = subprocess.Popen(
        ['plantri'] + plantri_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1,
        universal_newlines=True
    )
    for line in process.stdout:
        yield line.strip()  # or parse binary if using planar_code
        
import subprocess



