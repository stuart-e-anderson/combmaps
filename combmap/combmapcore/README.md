# CombmapCore

A modular Python library for analyzing planar graphs via combinatorial maps.

## ✨ Features

- Parse binary planar code from Plantri in-memory (no disk IO)
- Construct dart-based combinatorial maps with cyclic adjacency
- Traverse faces and build dual graphs
- Apply filters (valence, connectivity) to extract special structures
- Scaffold for Venn diagram analysis, knot graphs, squared rectangles, rhythm synthesis

## 🚀 Installation

```bash
pip install -e .
usage
from combmapcore import plantri_graphs, CombinatorialMap

for adj in plantri_graphs(7):
    cmap = CombinatorialMap()
    cmap.build_from_adjacency(adj)
    cmap.compute_faces()
    dual = cmap.compute_dual_adjacency()
    break

Projects Built on This

    KnotGraphLab

    VennDiagLib

    RectMapLab

    RhythmSynthLab
    
Stuart Anderson 📧 stuart.errol.anderson@gmail.com
