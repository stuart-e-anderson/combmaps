from combmapcore.walktools import extract_walks

def classify_walks(cmap):
    walks = extract_walks(cmap)
    num_curves = len(walks)
    walk_lengths = [len(w) for w in walks]
    is_knot = (num_curves == 1)

    return {
        "is_knot": is_knot,
        "num_curves": num_curves,
        "walk_lengths": walk_lengths,
        "walks": walks,
    }

