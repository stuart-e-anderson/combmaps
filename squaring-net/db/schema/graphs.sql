-- squaring.net graph index (SPEC-3)
-- One row per planar c-net identified by nauty/plantri.
-- Dual pairs are stored once: the dual partner is represented by dual_of
-- pointing back at the stored graph, so dissections are only computed and
-- stored for one member of each pair — a graph and its dual give the same
-- dissections, rotated 90 degrees at display time (see SPEC-2's N=4 identity).
-- Self-dual graphs have no partner to elide.

CREATE TABLE graphs (
    graph_id     BIGINT       GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    hash_code    TEXT         NOT NULL,                -- nauty canonical certificate; join key sqt emits per SPEC-1 Stage B
    num_edges    SMALLINT     NOT NULL,                -- order = num_edges - 1 (graphs has no order_val column, per SPEC-2)
    surface_type TEXT         NOT NULL DEFAULT 'plane', -- 'plane' | 'cylinder' | 'torus' (surfaces use surftri_0989 cycle-basis code)
    category     SMALLINT     NOT NULL DEFAULT 1,       -- isolates the 3-connected c-net population the x4 identity covers; exact predicate is SPEC-2 §0, still open
    is_self_dual BOOLEAN      NOT NULL DEFAULT FALSE,
    dual_of      BIGINT       REFERENCES graphs (graph_id),  -- set only on the elided partner; NULL for the stored member and for self-dual graphs
    CONSTRAINT graphs_hash_code_uniq UNIQUE (hash_code),
    CONSTRAINT graphs_dual_of_not_self CHECK (dual_of IS NULL OR dual_of <> graph_id),
    CONSTRAINT graphs_self_dual_no_partner CHECK (NOT (is_self_dual AND dual_of IS NOT NULL))
);

CREATE INDEX idx_graphs_num_edges ON graphs (num_edges);
CREATE INDEX idx_graphs_dual_of   ON graphs (dual_of) WHERE dual_of IS NOT NULL;
CREATE INDEX idx_graphs_surface_category ON graphs (surface_type, category);
