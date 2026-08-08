-- squaring.net named-graph axis (SPEC-4)
-- Human/historical curation (Duijvestijn, Mrs Perkins's Quilt family, etc.),
-- kept off `graphs` proper and entirely separate from dissection-specialness
-- (is_crossed/corner_elements/boundary_square_indices on `dissections`).
-- A name is a fact about the graph, independent of which rooting/rotation
-- is being displayed.

CREATE TABLE graph_names (
    id             BIGINT  GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    graph_id       BIGINT  NOT NULL REFERENCES graphs (graph_id),
    common_name    TEXT    NOT NULL,   -- e.g. 'Duijvestijn's square'
    discoverer     TEXT,
    discovery_year SMALLINT,
    source         TEXT,               -- citation / catalogue reference
    is_primary     BOOLEAN NOT NULL DEFAULT true,
    notes          TEXT
);

-- one canonical display name per graph; aliases allowed via is_primary = false
CREATE UNIQUE INDEX idx_graph_names_primary ON graph_names (graph_id) WHERE is_primary;
CREATE INDEX idx_graph_names_graph ON graph_names (graph_id);
