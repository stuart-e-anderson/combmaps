from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


# Maps filename suffixes to (simple, perfect, is_square)
_TYPE_MAP: dict[str, tuple[bool, bool, bool]] = {
    "spsr": (True,  True,  False),
    "spss": (True,  True,  True),
    "cpsr": (False, True,  False),
    "cpss": (False, True,  True),
    "sisr": (True,  False, False),
    "siss": (True,  False, True),
    "cisr": (False, False, False),
    "ciss": (False, False, True),
}


@dataclass
class BouwkampCode:
    order:     int
    width:     int
    height:    int
    elements:  tuple[int, ...]
    type_code: str = ""
    simple:    bool = field(init=False)
    perfect:   bool = field(init=False)
    is_square: bool = field(init=False)

    def __post_init__(self):
        props = _TYPE_MAP.get(self.type_code, (None, None, None))
        self.simple, self.perfect, self.is_square = props

    @property
    def bouwkamp_string(self) -> str:
        """Compact canonical string: 'order width height e1 e2 ...'"""
        parts = [self.order, self.width, self.height] + list(self.elements)
        return " ".join(str(x) for x in parts)

    @property
    def aspect_ratio(self) -> float:
        return self.width / self.height

    def __repr__(self) -> str:
        return (f"BouwkampCode(order={self.order}, {self.width}x{self.height}, "
                f"type={self.type_code or '?'})")


def parse_line(line: str, type_code: str = "") -> BouwkampCode | None:
    """Parse one Bouwkamp code line. Returns None for blank/comment lines."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    nums = list(map(int, line.split()))
    order = nums[0]
    width = nums[1]
    height = nums[2]
    elements = tuple(nums[3:])
    return BouwkampCode(
        order=order,
        width=width,
        height=height,
        elements=elements,
        type_code=type_code,
    )


def parse_file(path: Path | str, type_code: str = "") -> Iterator[BouwkampCode]:
    """Yield BouwkampCode objects from a text file, one per line."""
    path = Path(path)
    if not type_code:
        # Infer from filename suffix e.g. '6.bin-spsr.txt' → 'spsr'
        for tc in _TYPE_MAP:
            if tc in path.name:
                type_code = tc
                break
    with path.open() as fh:
        for line in fh:
            code = parse_line(line, type_code)
            if code is not None:
                yield code
