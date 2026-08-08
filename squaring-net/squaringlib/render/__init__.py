"""
render -- SVG output for squared rectangles.

Draws only. Placement math lives in squaringlib.geometry.place_elements()
(SPEC-4's "one shared geometry function, not two") -- this module's job is
turning that placement into markup, nothing else.
"""
from squaringlib.geometry import place_elements

__all__ = ["render_svg"]


def render_svg(elements, width, height, scale_to=800, label_min_size_px=14):
    """
    elements: list[int] of square sizes in canonical (packed) order.
    Returns a standalone SVG document (str) -- outer rectangle plus every
    placed square, size-labelled where there's room to read it.
    """
    placed = place_elements(elements, width, height)
    scale = scale_to / max(width, height)
    svg_w, svg_h = width * scale, height * scale

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w:.2f} {svg_h:.2f}" '
        f'width="{svg_w:.0f}" height="{svg_h:.0f}" font-family="sans-serif">',
        f'<rect x="0" y="0" width="{svg_w:.2f}" height="{svg_h:.2f}" '
        f'fill="none" stroke="black" stroke-width="1.5"/>',
    ]
    for sq in placed:
        x, y, s = sq["x"] * scale, sq["y"] * scale, sq["size"] * scale
        parts.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{s:.2f}" height="{s:.2f}" '
            f'fill="none" stroke="#333" stroke-width="1"/>'
        )
        if s >= label_min_size_px:
            font_size = min(s * 0.28, 13)
            parts.append(
                f'<text x="{x + s / 2:.2f}" y="{y + s / 2:.2f}" font-size="{font_size:.1f}" '
                f'text-anchor="middle" dominant-baseline="middle" fill="#555">{sq["size"]}</text>'
            )
    parts.append("</svg>")
    return "\n".join(parts)
