# SPEC-4 — Special-property / geometry columns

**Version 0.1 · 2026-08-07 · depends on:** SPEC-3 (clean schema)
**Grounded in:** `bk2svg.py`'s `tile_using_strip_data_bigint` (the existing skyline placer — returns `[{id, x, y, size}, ...]` per square), the legacy `dissections.boundary_square_indices integer[]` column (`nauty/squaring_db/database-build.txt:7750` — declared, never populated), and the cross-point/reflex discussion in the same log (`database-build.txt:4035-4087`, Smith & Tutte Theorem IV).
**Role:** schema only. The query API that filters on these columns is SPEC-5, not here.

---

## Resolves a named contradiction

From the plan collation: *"Specialness on the graph vs. the dissection... resolved by splitting: dissection-specialness + a separate named-graph axis."* This spec is that split, made concrete:

- **Dissection-specialness** — structural/geometric facts about one tiling's layout (crossed, corner squares, boundary squares). Lives on `dissections`, because the collation's own example (`CPSS isomers of one graph differ in crossedness`) is exactly why this can't live on `graphs` — two dissections from the same graph can disagree.
- **Named-graph axis** — human/historical curation (Duijvestijn, Mrs Perkins's Quilt family, etc.). Lives on a new `graph_names` table, off `graphs`, because a name attaches to the graph itself, not to any one rooting/rotation of it.

## One shared geometry function, not two

`crossed`, `corner_elements`, and `boundary_square_indices` are all derived from the same thing: the (x, y, size) placement of every square, which is exactly what `tile_using_strip_data_bigint` already computes to draw the SVG. Computing them a second, independent way at load time is how the two would eventually disagree. So:

**`squaringlib.geometry.place_elements(bouwkamp_code, width, height) -> list[{id, x, y, size}]`** is specified as the single placement function, factored out of `bk2svg.py`'s skyline tiler (not rewritten — same algorithm, same exact-integer arithmetic, `id` is the 1-based position in the canonical element sequence). Both the loader (Stage C, to populate the three columns below) and the renderer (`squaringlib.render`, to draw the SVG) call it. Neither computes placement independently.

## The three columns

### `is_crossed BOOLEAN NOT NULL`
A dissection is **crossed** if some interior point is a corner of four distinct squares at once (a "cross point" — Smith & Tutte's Theorem IV language for reflex-derived rectangles, `database-build.txt:4035,4067`). Computed by tallying corner-point occurrences over `place_elements()`'s output: for each square, its four corners `(x,y)`, `(x+size,y)`, `(x,y+size)`, `(x+size,y+size)`; any interior point (`0 < x < width`, `0 < y < height`) with multiplicity 4 makes the dissection crossed. Cheap (single boolean, ~1 byte/row even at billions of rows) and needed for a plain `WHERE is_crossed` filter, so it stays on the hot partitioned table rather than being deferred to on-demand computation.

### `corner_elements SMALLINT[4] NOT NULL`
The size of the square occupying each of the four corners, fixed order `[top-left, top-right, bottom-left, bottom-right]` — the same top-left convention `sqtv4_3.cpp` already uses for canonicalization ("the code for the rectangle with the largest corner square in the top-left is canonical"). Found by scanning `place_elements()`'s output for the square covering each corner point. Fixed-width 4-element array, a few bytes/row — cheap enough to store inline and index for "which dissections have a size-N square in a corner" queries (SPEC-5).

### `boundary_square_indices SMALLINT[] NOT NULL`
1-based indices (matching `place_elements()`'s `id`, i.e. position in the canonical element sequence packed into `bouwkamp_code`) of every square touching an outer edge: `x=0`, `y=0`, `x+size=width`, or `y+size=height`. This is the same column the legacy schema declared and never filled in — SPEC-4 gives it real semantics and a real populate step. Bounded by `order` (≤ 30 entries even in the worst case), so it's cheap despite being variable-length. Used by the renderer to highlight the frame and, later, by boundary-based search (SPEC-5).

All three are computed once, in the loader (SPEC-1 Stage C), immediately after the area check — both need the same `place_elements()` call, so they're one pass, not three.

## DDL

Folded directly into `db/schema/dissections.sql` rather than issued as an `ALTER TABLE` migration, since SPEC-3's schema has never been deployed with data — there's nothing to migrate yet.

```sql
ALTER TABLE dissections
    ADD COLUMN is_crossed              BOOLEAN     NOT NULL,
    ADD COLUMN corner_elements         SMALLINT[4] NOT NULL,
    ADD COLUMN boundary_square_indices SMALLINT[]  NOT NULL;

CREATE INDEX idx_dissections_crossed ON dissections (order_val, is_crossed) WHERE is_crossed = true;
CREATE INDEX idx_dissections_corner  ON dissections USING GIN (corner_elements);
```

(Shown as `ALTER TABLE` here only to isolate the diff against SPEC-3; the actual `dissections.sql` gets these columns added to the `CREATE TABLE` directly — see the updated file.)

## Named-graph axis

```sql
CREATE TABLE graph_names (
    id              BIGINT  GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    graph_id        BIGINT  NOT NULL REFERENCES graphs (graph_id),
    common_name     TEXT    NOT NULL,   -- e.g. 'Duijvestijn''s square'
    discoverer      TEXT,
    discovery_year  SMALLINT,
    source          TEXT,               -- citation / catalogue reference
    is_primary      BOOLEAN NOT NULL DEFAULT true,
    notes           TEXT
);

-- one canonical display name per graph, multiple aliases allowed
CREATE UNIQUE INDEX idx_graph_names_primary ON graph_names (graph_id) WHERE is_primary;
CREATE INDEX idx_graph_names_graph ON graph_names (graph_id);
```

A graph can carry more than one name (aliases); `is_primary` picks the one the site displays by default. Nothing here touches `dissections` — a name is a fact about the graph, independent of which rooting/rotation is being displayed.

## Regression tie-in

SPEC-2 §6 already has the Duijvestijn 112² presence/linkage check. SPEC-4 adds the natural follow-on once `graph_names` exists: that graph's row should carry `common_name = 'Duijvestijn's square'`, `discoverer = 'A.J.W. Duijvestijn'`, `discovery_year = 1978` — a concrete seed row, not a placeholder, and a second regression test (name resolves via `graph_id`, not a second lookup path).

## Invariants
- `place_elements()` is the only geometry-placement implementation; the loader and the renderer both call it, neither reimplements it.
- All three geometry columns are computed together, in one pass, right after the area check in Stage C — not deferred, not computed lazily at query time (that's what made `boundary_square_indices` dead weight in the legacy schema: declared, never populated).
- Dissection-specialness (crossed/corner/boundary) never migrates onto `graphs`; named-graph curation never migrates onto `dissections`. That boundary is the whole point of the split.

## Open items
- `place_elements()` doesn't exist yet as a standalone `squaringlib.geometry` function — it needs factoring out of `bk2svg.py`'s `tile_using_strip_data_bigint` (same algorithm, just relocated so the loader can import it without pulling in SVG/rendering code).
- Whether `corner_elements` needs a documented tie-break when a corner point is exactly a graph's rotation axis (self-dual, degenerate placements) — not yet hit in the real data, flagged rather than guessed.
- Named-graph seed list beyond Duijvestijn (Mrs Perkins's Quilt family, other named discoveries) — content task, not a schema blocker.
