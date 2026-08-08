# SPEC-5 — Graph as the general object: representations, lineage, and tiered storage

**Version 0.1 · 2026-08-09 · depends on:** SPEC-1 (pipeline), SPEC-3 (schema), SPEC-4 (dissection specialness)
**Role:** architecture + schema hooks for a longer-horizon direction, agreed as a separate track from the squared-rectangle v1 (SPEC-1-4). Additive only — nothing here should require migrating what SPEC-1-4 already built. Implementation is phased and largely **not started**; this spec exists to capture the shared design intent before building against it.

---

## The reframing

The current schema treats `graphs` as supporting cast for `dissections` — a graph exists to be solved into squared rectangles. Stuart's direction: invert that. A graph is the primary object; a squared-rectangle dissection is *one* of several visual representations that can be derived from it (others: circle packing, Schlegel diagram, sphere/stereographic embedding via Koebe–Andreev–Thurston, Tutte embedding). Over time the site's center of gravity may shift from "squared rectangles, with graphs as plumbing" to "graphs, with squared dissection as one lens among several."

This does not replace SPEC-1-4. Squared-rectangle generation stays the frozen, gate-checked, bulk pipeline it already is. SPEC-5 is about what sits *around* it once graphs are treated as the thing users actually browse.

## Two-tier storage, not one order ceiling

SPEC-1's open item Q4 ("order ceiling for the bulky types") was framed as a single number. It's actually two, with a real gap between them:

- **Dissection cap** (lower): orders up to here get graphs *and* their full solved dissection set stored via the existing SPEC-1 pipeline, for fast browse/search/filter. Bounded by the same exponential growth SPEC-1's README already measured (order 21: ~243K graphs → ~5.3M dissections, ~35 minutes of compute across all three stages; roughly 3-4x growth per order in this range).
- **Graph cap** (higher): orders between the dissection cap and here get graphs stored, but *not* their dissections — those are generated on request, not precomputed at scale. Graphs alone are far cheaper to store and enumerate than their full dissection sets (Stage A's own cost, not Stage B/C's), so this ceiling can sit meaningfully higher.

Concrete numbers are Q4's job (tracked separately, grounded in the measured cost curve above) — SPEC-5's job is establishing that the two caps are architecturally distinct, and that "graph-only" is a first-class stored state, not a gap.

### The on-demand generation gap this creates

Making the graph-only tier actually useful — "show me a dissection of this higher-order graph when asked" — needs a **synchronous, single-graph solve path**, which does not exist today. `sqt` (SPEC-1 Stage B) is a batch tool: it reads a `planar_code` file and writes output files, with no notion of "solve this one graph and return an answer in a web request." Two ways to close this gap:

1. Shell out to the existing frozen `sqt` binary per request. Simple, reuses tested code, but awkward for a web request (subprocess spawn, temp files, unbounded runtime risk for a pathological graph, no natural request cancellation).
2. Port the actual solve — it's Kirchhoff/Smith network linear algebra, not an inherently batch-shaped computation — into `squaringlib.electrical` (currently a stub) as a real-time function. More engineering up front, but the right shape for a request/response path, and testable independently of the frozen batch tool.

Not deciding between these here. Flagging it as its own spec-sized follow-on, because it's easy to underestimate as "just call sqt."

### The graph-structure gap this exposes (relevant to both tracks)

**`graphs.hash_code` is an identity, not a structure.** It's a nauty canonical certificate — sound as a join key, useless for reconstructing the actual graph. The real adjacency/rotation system currently exists only transiently: in Stage A's Python process, and in the raw `planar_code` files under `data/planar_code/` (gitignored, treated as regeneratable, not part of the database).

Every capability this spec proposes — on-demand dissection solving, circle packing, Schlegel/Tutte/sphere embeddings, deletion-contraction — needs the *actual graph*, not just its hash. This means `graphs` needs a column holding a compact, retrievable encoding of the structure itself (candidates: raw `planar_code` bytes, a graph6 string, or an adjacency-list JSON/array — leaning toward `planar_code` bytes since Stage A already produces exactly that format and `squaringlib.planar.parse_planar_code()` already reads it). This is a real schema gap, not a future nice-to-have — even SPEC-1's own graph-only tier can't do anything with a graph-only row today beyond knowing it exists.

## Multiple representations

`squaringlib.geometry.place_elements()` already establishes the pattern SPEC-4 wants generalized: one function per representation, called on demand by whoever needs it (loader, renderer, API), never precomputed and stored as HTML. The same shape should apply to other representations:

- **Circle packing** — Stuart has prior art (`CirclePack/`, Ken Stephenson's Java tool) worth checking for algorithm reference, though it's Java, not a drop-in Python dependency.
- **Schlegel diagram**
- **Sphere / stereographic projection** (Koebe–Andreev–Thurston circle-packing-derived embedding of 3-connected planar graphs)
- **Tutte embedding** (barycentric/spring embedding — well-trodden, likely the cheapest to implement first as a proof of the on-demand-representation pattern)

Likely home: a new `squaringlib.representations` module (or representation-specific submodules alongside the existing `squaringlib.geometry`), each exposing a `place_*(graph_structure) -> ...` function mirroring `place_elements()`'s contract. Whether SageMath becomes a hard dependency (heavier install, but has circle-packing and embedding algorithms built in) or these get built on NetworkX/pure Python is an open implementation question, not decided here.

## Graph lineage (deletion-contraction)

A new table linking graphs to graphs by derivation, in support of walking the deletion-contraction recursion at the heart of the Tutte polynomial (`T(G) = T(G−e) + T(G/e)` for an edge `e` that's neither a bridge nor a loop, with base cases for the rest).

```sql
CREATE TABLE graph_lineage (
    lineage_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    parent_graph_id BIGINT NOT NULL REFERENCES graphs (graph_id),
    child_graph_id  BIGINT NOT NULL REFERENCES graphs (graph_id),
    operation       TEXT   NOT NULL CHECK (operation IN ('deletion', 'contraction')),
    edge_ref        TEXT,   -- identifies which edge of the parent; format depends on the
                             -- graph-structure column above being resolved first
    CONSTRAINT graph_lineage_uniq UNIQUE (parent_graph_id, operation, edge_ref)
);
CREATE INDEX idx_graph_lineage_parent ON graph_lineage (parent_graph_id);
CREATE INDEX idx_graph_lineage_child  ON graph_lineage (child_graph_id);
```

**Sparse and as-computed, not exhaustive.** A graph with `e` edges has `e` first-level deletion-contraction children, recursing out to the full Tutte polynomial computation tree — enormous even for modest graphs. This table should behave like `graphs.dual_of` already does: additive metadata recorded for operations actually performed, never a required closure over all possible operations.

**Deletion/contraction breaks the current population assumption.** `graphs` today is scoped to 3-connected planar c-nets from plantri — the kind of graph `sqt` can solve. Most delete/contract results won't be 3-connected, won't be planar in the same useful sense, and won't be squaring-solvable at all. That's a different graph population living in the same table. `graphs.category` (currently only value `1`, and SPEC-2 §0 already has its exact predicate as an open item) is the likely extension point, but needs a real taxonomy defined before more values get added ad hoc — see open items.

## Invariants

- Nothing in this spec changes SPEC-1's frozen pipeline or SPEC-2's gate. The dissection cap tier is exactly what already exists.
- On-demand-generated representations (dissections above the dissection cap, circle packings, embeddings) are never silently persisted as new `dissections` rows — that would quietly break SPEC-2's reconciliation identity for an order that's supposed to be graph-only. If a computed result is worth keeping, promoting it is a deliberate, explicit action, not a side effect of serving a request.
- `graph_lineage` is sparse by design; absence of a row means "not computed," never "doesn't exist."
- `graphs.category` values must be defined with an explicit predicate before use, matching the discipline SPEC-2 §0 already established for `category = 1`.

## Open items

- Resolve `graphs`' missing structure column (see above) — this blocks everything else in this spec and arguably should land alongside whatever Q4 lands on, since the graph-only tier needs it regardless of SPEC-5's broader scope.
- Define the `category` taxonomy: what distinguishes a squaring-solvable c-net (`1`) from a lineage-derived general graph, and whether that's a small closed enum or something more open-ended.
- On-demand single-graph solve architecture (subprocess vs. ported real-time solver) — own spec-sized decision, not resolved here.
- SageMath as a dependency: yes/no, and if yes, how that interacts with the existing plain-`venv` Python environment (`squaring-net/pyproject.toml` currently has no SageMath dependency).
- `edge_ref`'s exact encoding depends on settling the graph-structure column first — can't finalize `graph_lineage`'s shape until then.
- Whether representation functions belong in one `squaringlib.representations` module or several, and whether `squaringlib.render` (currently a stub, meant for SVG per SPEC-4) is the same thing as this or a separate concern (render *is* a representation — output format — arguably render should be the layer that takes any of these representations' output and draws it, not a representation itself).
