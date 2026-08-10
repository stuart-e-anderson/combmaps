-- squaring.net dissection index (SPEC-3)
-- One row per squared rectangle / square, generated only by the frozen
-- SPEC-1 pipeline and admitted only after the SPEC-2 reconciliation gate.
-- Partitioned by order_val, matching the data/parquet/order=NN/ layout and
-- letting SPEC-2's per-partition dedup audit stay scoped (never a
-- table-wide GROUP BY — that's what hung for 8-9 hours on the old DB).
--
-- Schema diet from SPEC-1 Stage C: no `elements` (derive from bouwkamp_code
-- at serve time), no `sb_path` (ratio_cf's continued-fraction terms *are*
-- the Stern-Brocot path). DEGN rows are counted into order_counts and
-- never loaded here, so d_type never carries DEGN -- SPEC-7 (2026-08-10)
-- widened it from the original eight plane types to sixteen, adding
-- cylinder ('C' shape) and torus ('T' shape) equivalents.
--
-- is_crossed / corner_elements / boundary_square_indices are SPEC-4: all
-- three come from one squaringlib.geometry.place_elements() call per row
-- (the same skyline placement squaringlib.render uses to draw the SVG),
-- done once in the loader right after the area check.

CREATE TABLE dissections (
    dissection_id           BIGINT       GENERATED ALWAYS AS IDENTITY,
    order_val                SMALLINT     NOT NULL,
    graph_id                 BIGINT       NOT NULL REFERENCES graphs (graph_id),
    d_type                   CHAR(4)      NOT NULL
                              CHECK (d_type IN ('SPSR','SPSS','SISR','SISS',    -- plane rectangle/square
                                                 'CPSR','CPSS','CISR','CISS',
                                                 'SPSC','SISC','CPSC','CISC',    -- SPEC-7: cylinder ('C' shape)
                                                 'SPST','SIST','CPST','CIST')),  -- SPEC-7: torus ('T' shape) -- SPST = Stuart's
                                                                                 -- one confirmed example so far (Gambini's graph)
    simple                   BOOLEAN      NOT NULL,
    perfect                  BOOLEAN      NOT NULL,
    is_square                BOOLEAN      NOT NULL,
    is_trivial_compound      BOOLEAN      NOT NULL DEFAULT FALSE,  -- SPEC-7/2026-08-10, per Stuart: a compound
                              -- dissection made by gluing a square whose side equals an existing squared
                              -- rectangle's full height/width onto that edge. Adds no new pattern beyond the
                              -- rectangle it was glued to -- "not an important category". Deliberately NOT
                              -- backfilled as a full catalog (combinatorially trivial/infinite: applicable to
                              -- any existing dissection); this flag exists so a handful of illustrative
                              -- examples can be curated for the website, not for exhaustive generation.
                              -- Only meaningful when d_type is one of the compound types (CHECK below).
    width                    BIGINT       NOT NULL,   -- BIGINT: wheel/surface tilings run Fibonacci-scale dims
    height                   BIGINT       NOT NULL,
    bouwkamp_code            BYTEA        NOT NULL,   -- packed canonical element sequence; order/width/height already columns, not repeated here. Area check (Σ elementᵢ² = width·height) is enforced by the loader at COPY time, not here — it can't be expressed without unpacking the bytea.
    ratio_cf                 INTEGER[],               -- continued-fraction terms of width/height = the Stern-Brocot path; NULL for squares. INTEGER not SMALLINT: extreme-aspect-ratio dissections produce CF terms > 32767 (hit at order 21: a term of 32821)
    is_crossed               BOOLEAN      NOT NULL,   -- SPEC-4: an interior point where 4 squares' corners meet (Smith & Tutte reflex/cross-point)
    corner_elements           SMALLINT[4]  NOT NULL,   -- SPEC-4: [top-left, top-right, bottom-left, bottom-right] square sizes
    boundary_square_indices    SMALLINT[]   NOT NULL,   -- SPEC-4: 1-based positions (in the packed element sequence) of every square touching an outer edge
    PRIMARY KEY (dissection_id, order_val),
    CONSTRAINT dissections_trivial_compound_implies_compound
                              CHECK (NOT is_trivial_compound OR NOT simple)
) PARTITION BY LIST (order_val);

CREATE TABLE dissections_o05 PARTITION OF dissections FOR VALUES IN (5);
CREATE TABLE dissections_o06 PARTITION OF dissections FOR VALUES IN (6);
CREATE TABLE dissections_o07 PARTITION OF dissections FOR VALUES IN (7);
CREATE TABLE dissections_o08 PARTITION OF dissections FOR VALUES IN (8);
CREATE TABLE dissections_o09 PARTITION OF dissections FOR VALUES IN (9);
CREATE TABLE dissections_o10 PARTITION OF dissections FOR VALUES IN (10);
CREATE TABLE dissections_o11 PARTITION OF dissections FOR VALUES IN (11);
CREATE TABLE dissections_o12 PARTITION OF dissections FOR VALUES IN (12);
CREATE TABLE dissections_o13 PARTITION OF dissections FOR VALUES IN (13);
CREATE TABLE dissections_o14 PARTITION OF dissections FOR VALUES IN (14);
CREATE TABLE dissections_o15 PARTITION OF dissections FOR VALUES IN (15);
CREATE TABLE dissections_o16 PARTITION OF dissections FOR VALUES IN (16);
CREATE TABLE dissections_o17 PARTITION OF dissections FOR VALUES IN (17);
CREATE TABLE dissections_o18 PARTITION OF dissections FOR VALUES IN (18);
CREATE TABLE dissections_o19 PARTITION OF dissections FOR VALUES IN (19);
CREATE TABLE dissections_o20 PARTITION OF dissections FOR VALUES IN (20);
CREATE TABLE dissections_o21 PARTITION OF dissections FOR VALUES IN (21);
CREATE TABLE dissections_o22 PARTITION OF dissections FOR VALUES IN (22);
CREATE TABLE dissections_o23 PARTITION OF dissections FOR VALUES IN (23);
CREATE TABLE dissections_o24 PARTITION OF dissections FOR VALUES IN (24);
CREATE TABLE dissections_o25 PARTITION OF dissections FOR VALUES IN (25);
CREATE TABLE dissections_o26 PARTITION OF dissections FOR VALUES IN (26);
CREATE TABLE dissections_o27 PARTITION OF dissections FOR VALUES IN (27);
CREATE TABLE dissections_o28 PARTITION OF dissections FOR VALUES IN (28);
CREATE TABLE dissections_o29 PARTITION OF dissections FOR VALUES IN (29);
CREATE TABLE dissections_o30 PARTITION OF dissections FOR VALUES IN (30);
CREATE TABLE dissections_default PARTITION OF dissections DEFAULT;  -- safety net; SPEC-2 §4(c) asserts this stays empty above the ingested ceiling

-- Cross-class dedup safety net (SPEC-1 Stage C). Local per partition, which
-- is exactly the scoping SPEC-2 §4(b) wants for the duplicate audit.
CREATE UNIQUE INDEX idx_dissections_bouwkamp ON dissections (order_val, bouwkamp_code);
CREATE INDEX idx_dissections_type    ON dissections (order_val, d_type);
CREATE INDEX idx_dissections_graph   ON dissections (graph_id);          -- SPEC-2 §6 linkage query
CREATE INDEX idx_dissections_dims    ON dissections (order_val, width, height);
CREATE INDEX idx_dissections_perfect ON dissections (order_val, perfect) WHERE perfect = true;
CREATE INDEX idx_dissections_crossed ON dissections (order_val, is_crossed) WHERE is_crossed = true;
CREATE INDEX idx_dissections_corner  ON dissections USING GIN (corner_elements);
