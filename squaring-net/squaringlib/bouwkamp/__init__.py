"""
bouwkamp — parse, validate and represent Bouwkamp codes.

A Bouwkamp code line has the form:
    order width height e1 e2 ... eN

where order == N == len(elements), width and height are the outer rectangle
dimensions, and e1..eN are the sizes of the constituent squares.

The type_code (spsr, spss, cpsr, cpss, sisr, siss, cisr, ciss) encodes:
    s/c  simple / compound
    p/i  perfect / imperfect
    s/r  square / rectangle
"""

from .code import BouwkampCode, parse_line, parse_file

__all__ = ["BouwkampCode", "parse_line", "parse_file"]
