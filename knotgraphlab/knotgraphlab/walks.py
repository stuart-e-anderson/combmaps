from .encoder import encode_oriented_gauss
from .filters import is_valid_knot_graph
from .exporters import save_gauss_code, export_diagram
from combmapcore.walktools import extract_walks

def classify_walks(cmap):
    walks = extract_walks(cmap)
    num_curves = len(walks)
    walk_lengths = [len(w) for w in walks]
    is_knot = (num_curves == 1)  # Knot candidate if a single closed curve
    print(f"Number of walks: {len(walks)}")
    print(f"Walk lengths: {[len(w) for w in walks]}")
    return {
        "is_knot": is_knot,
        "num_curves": num_curves,
        "walk_lengths": walk_lengths,
        "walks": walks,
    }

