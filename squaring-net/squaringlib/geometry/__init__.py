"""
geometry -- skyline placement and structural properties for squared rectangles.

place_elements() is factored out of bk2svg.py's tile_using_strip_data_bigint
(same algorithm, same exact-integer arithmetic) per SPEC-4: the loader
(Stage C) and squaringlib.render both call this one function for placement,
neither reimplements it.
"""
from collections import defaultdict

__all__ = ["place_elements", "corner_elements", "boundary_square_indices", "is_crossed"]


def _normalize_segments(segments):
    out = []
    for x0, x1, h in segments:
        if x0 >= x1:
            continue
        if out and out[-1][1] == x0 and out[-1][2] == h:
            out[-1] = (out[-1][0], x1, h)
        else:
            out.append((x0, x1, h))
    return out


def _find_anchor_from_skyline(segments):
    if not segments:
        return None
    min_h = min(h for _, _, h in segments)
    for x0, _, h in segments:
        if h == min_h:
            return x0, min_h
    return None


def _interval_is_flat_at_height(segments, x, size, y):
    x_end = x + size
    pos = x
    for x0, x1, h in segments:
        if x1 <= pos:
            continue
        if x0 > pos:
            return False
        if h != y:
            return False
        pos = min(x1, x_end)
        if pos == x_end:
            return True
    return False


def _raise_interval(segments, x, size, y_new):
    x_end = x + size
    out = []
    for x0, x1, h in segments:
        if x1 <= x or x0 >= x_end:
            out.append((x0, x1, h))
            continue
        if x0 < x:
            out.append((x0, x, h))
        mid0 = max(x0, x)
        mid1 = min(x1, x_end)
        out.append((mid0, mid1, y_new))
        if x1 > x_end:
            out.append((x_end, x1, h))
    return _normalize_segments(out)


def place_elements(bouwkamp_code, width, height):
    """
    Place every square of a canonical element sequence via exact-integer
    skyline packing.

    bouwkamp_code: list[int] of square sizes in canonical (packed) order,
    or a whitespace-separated string of the same.

    Returns [{'id': 1-based position, 'x', 'y', 'size'}, ...], top-left origin,
    id matching the position in the packed element sequence (bouwkamp_code).
    """
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive integers")

    if isinstance(bouwkamp_code, str):
        sizes = [int(s) for s in bouwkamp_code.split() if s.strip()]
    else:
        sizes = list(bouwkamp_code)

    skyline = [(0, width, 0)]
    placed = []
    square_id = 1
    idx = 0

    while idx < len(sizes):
        anchor = _find_anchor_from_skyline(skyline)
        if anchor is None:
            raise RuntimeError("no anchor found but squares remain unplaced")
        anchor_x, start_y = anchor
        current_x = anchor_x
        temp_idx = idx
        strip_sizes = []

        while temp_idx < len(sizes):
            sq_size = sizes[temp_idx]
            if sq_size <= 0:
                raise ValueError(f"non-positive square size: {sq_size}")
            if current_x + sq_size > width or start_y + sq_size > height:
                break
            if not _interval_is_flat_at_height(skyline, current_x, sq_size, start_y):
                break
            strip_sizes.append(sq_size)
            current_x += sq_size
            temp_idx += 1

        if not strip_sizes:
            raise RuntimeError(
                f"could not place square {sizes[idx]} at anchor ({anchor_x}, {start_y})"
            )

        curr_x = anchor_x
        for size in strip_sizes:
            skyline = _raise_interval(skyline, curr_x, size, start_y + size)
            placed.append({"id": square_id, "x": curr_x, "y": start_y, "size": size})
            curr_x += size
            square_id += 1

        idx += len(strip_sizes)

    if len(skyline) != 1 or skyline[0] != (0, width, height):
        raise RuntimeError(f"tiling did not finish cleanly: final skyline {skyline[:10]}")

    return placed


def corner_elements(width, height, placed):
    """[top-left, top-right, bottom-left, bottom-right] square sizes."""
    tl = tr = bl = br = None
    for sq in placed:
        x, y, s = sq["x"], sq["y"], sq["size"]
        if x == 0 and y == 0:
            tl = s
        if x + s == width and y == 0:
            tr = s
        if x == 0 and y + s == height:
            bl = s
        if x + s == width and y + s == height:
            br = s
    return [tl, tr, bl, br]


def boundary_square_indices(width, height, placed):
    """1-based ids (place_elements()'s id) of every square touching an outer edge."""
    return [
        sq["id"] for sq in placed
        if sq["x"] == 0 or sq["x"] + sq["size"] == width
        or sq["y"] == 0 or sq["y"] + sq["size"] == height
    ]


def is_crossed(width, height, placed):
    """True if some interior point is a corner of four distinct squares at once (Smith & Tutte cross-point)."""
    point_counts = defaultdict(int)
    for sq in placed:
        x, y, s = sq["x"], sq["y"], sq["size"]
        for px, py in ((x, y), (x + s, y), (x, y + s), (x + s, y + s)):
            if 0 < px < width and 0 < py < height:
                point_counts[(px, py)] += 1
    return any(c >= 4 for c in point_counts.values())
