-- squaring.net graph index (SPEC-3)
-- One row per planar c-net identified by nauty/plantri. dual_of records the
-- duality relationship (which graph is this graph's dual) as descriptive
-- metadata only — it is NOT a signal to skip loading dissections.
--
-- Correction (2026-08-09): SPEC-2 v0.1 assumed a graph and its dual give
-- "the same dissections rotated 90 degrees" and should therefore be
-- deduplicated at load (one representative per pair). Verified geometrically
-- true (both members of a sampled v==f pair, solved independently, produce
-- identical (x,y,size) placements under some dihedral transform) but this
-- does NOT match the standard cataloguing convention: OEIS A002839 counts
-- both members of a non-self-dual pair separately (confirmed exact match at
-- every tested order, 9 through 21, once the dedup-at-load was removed).
-- Graph and dual are catalogued as distinct combinatorial objects regardless
-- of their dissections being congruent under rotation. See
-- SPEC-2-reconciliation.md v0.3 for the full writeup.
--
-- The one case where a graph genuinely has zero dissection rows: the v<f
-- side of a v>f class is only ever derived (dualised in Python), never fed
-- to plantri/sqt at all — not because of any load-time filtering, but
-- because it was never solved in the first place (SPEC-1 Stage A).

CREATE TABLE graphs (
    graph_id     BIGINT       GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    hash_code    TEXT         NOT NULL,                -- nauty canonical certificate; join key sqt emits per SPEC-1 Stage B
    num_edges    SMALLINT     NOT NULL,                -- order = num_edges - 1 (graphs has no order_val column, per SPEC-2)
    surface_type TEXT         NOT NULL DEFAULT 'plane', -- 'plane' | 'cylinder' | 'torus' (surfaces use surftri_0989 cycle-basis code)
    category     SMALLINT     NOT NULL DEFAULT 1,       -- isolates the 3-connected c-net population the reconciliation upper bound covers; exact predicate is SPEC-2 §0, still open
    is_self_dual BOOLEAN      NOT NULL DEFAULT FALSE,
    dual_of      BIGINT       REFERENCES graphs (graph_id),  -- descriptive only (see header note); NULL for self-dual graphs and for one arbitrary member of each dual pair
    CONSTRAINT graphs_hash_code_uniq UNIQUE (hash_code),
    CONSTRAINT graphs_dual_of_not_self CHECK (dual_of IS NULL OR dual_of <> graph_id),
    CONSTRAINT graphs_self_dual_no_partner CHECK (NOT (is_self_dual AND dual_of IS NOT NULL))
);

CREATE INDEX idx_graphs_num_edges ON graphs (num_edges);
CREATE INDEX idx_graphs_dual_of   ON graphs (dual_of) WHERE dual_of IS NOT NULL;
CREATE INDEX idx_graphs_surface_category ON graphs (surface_type, category);
