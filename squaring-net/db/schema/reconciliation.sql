-- squaring.net reconciliation-gate support tables (SPEC-2 §1, §5)
-- Carried from SPEC-2 verbatim, with two gaps filled:
--  1. SPEC-2's gate procedure step 6 sets order_counts.status='committed',
--     but SPEC-2's own table definition never declared a status column.
--  2. SPEC-6/7 (2026-08-11): once CPSR/CPSS/CISR/CISS (category=2/3
--     connectivity populations) and cylinder dissections (same graphs as
--     plane, category=1, but a genuinely different generation run/tool --
--     see SPEC-7's cylinder section) exist, order_val alone no longer
--     uniquely identifies a generation run. order_counts is a *provenance*
--     record (tool/tool_version/git_sha/plantri_version/plantri_classes_fed
--     exist specifically so a partition's origin is honestly checkable --
--     the same mechanism that already correctly flags CISR/CISS as
--     partial), so the key needs to capture "which population, which run,"
--     not just "which order." Added `category` (mirrors graphs.category)
--     and widened the primary key to (order_val, category, tool).

CREATE TABLE IF NOT EXISTS order_counts (
    order_val          SMALLINT     NOT NULL,
    category            SMALLINT     NOT NULL DEFAULT 1,  -- mirrors graphs.category: 1=3-connected plane/cylinder-source population, 2/3=SPEC-6 compound populations
    d_type_counts       JSONB        NOT NULL,   -- {"SPSR":..., ...} -- 16 possible types as of SPEC-7, not the original eight
    degn_count          BIGINT       NOT NULL,   -- kept after DEGN rows are counted then discarded (never loaded to dissections)
    graph_count         BIGINT       NOT NULL,
    tool                TEXT         NOT NULL DEFAULT 'sqt',
    tool_version         TEXT,
    git_sha              TEXT,
    plantri_version       TEXT,
    plantri_classes_fed  TEXT[],                  -- which (v,f) classes were fed; the honest basis for CISS/CISR completeness flags
    status               TEXT         NOT NULL DEFAULT 'pending'
                          CHECK (status IN ('pending', 'committed', 'rejected')),
    recorded_at           TIMESTAMPTZ  DEFAULT now(),
    PRIMARY KEY (order_val, category, tool)
);

CREATE TABLE IF NOT EXISTS ref_counts (
    order_val  INT    NOT NULL,
    d_type     TEXT   NOT NULL,
    ref_count  BIGINT NOT NULL,
    source     TEXT,                              -- 'OEIS Axxxxxx' / 'catalogue vN'
    PRIMARY KEY (order_val, d_type)
);
