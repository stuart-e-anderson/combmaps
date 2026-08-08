-- squaring.net reconciliation-gate support tables (SPEC-2 §1, §5)
-- Carried from SPEC-2 verbatim, with one gap filled: SPEC-2's gate
-- procedure step 6 sets order_counts.status='committed', but SPEC-2's own
-- table definition never declared a status column. Added here.

CREATE TABLE IF NOT EXISTS order_counts (
    order_val          SMALLINT     PRIMARY KEY,
    d_type_counts       JSONB        NOT NULL,   -- {"SPSR":..., ...} the eight real types
    degn_count          BIGINT       NOT NULL,   -- kept after DEGN rows are counted then discarded (never loaded to dissections)
    graph_count         BIGINT       NOT NULL,
    tool                TEXT         NOT NULL DEFAULT 'sqt',
    tool_version         TEXT,
    git_sha              TEXT,
    plantri_version       TEXT,
    plantri_classes_fed  TEXT[],                  -- which (v,f) classes were fed; the honest basis for CISS/CISR completeness flags
    status               TEXT         NOT NULL DEFAULT 'pending'
                          CHECK (status IN ('pending', 'committed', 'rejected')),
    recorded_at           TIMESTAMPTZ  DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ref_counts (
    order_val  INT    NOT NULL,
    d_type     TEXT   NOT NULL,
    ref_count  BIGINT NOT NULL,
    source     TEXT,                              -- 'OEIS Axxxxxx' / 'catalogue vN'
    PRIMARY KEY (order_val, d_type)
);
