# SPEC-2 — Reconciliation gate (runnable SQL)

**Version 0.2 · 2026-08-08 · one representative stored per graph/dual pair, N corrected from a flat x4 to an e-per-graph upper bound**
**Runs against:** the clean schema (SPEC-3), populated only by the frozen pipeline (SPEC-1).
**Role:** forward gate only. No regenerated partition commits until green (SPEC-1 Stage D). The old database attempts are archived and dropped without analysis — nothing here inspects or repairs them.

---

## The identity, and why the gate measures rather than asserts

**Correction (v0.2):** the original v0.1 draft asserted `Σdissections ≈ 4·graphs(k)`, on the theory that each stored graph contributes a flat "4 rootings". Verified wrong against real order-21 data (build session 2026-08-08): sampled graphs independently produced 11-22 tablecode rows each, not 4, and the ratio actually *grows* with order (0.20 at order 9, 0.73 at order 21) rather than holding near a constant — ruling out small-sample noise. Ground truth, per Stuart: **every edge of a graph can be the battery edge**, so a graph with `e` edges yields up to `e` distinct dissections (fewer only because some battery-edge choices fail the `s1<=0 || s2<=0` validity check inside `sqt`, or because two choices canonicalise to a byte-identical tablecode and `sqt`'s own `map`/`std::set` naturally collapses them — no automorphism computation, no orbit theory, just literal string dedup, same as the dual-pair elision already does). So the corrected identity is an **upper bound**, not a target ratio:

```
Σ(all d_types + DEGN, order k)  ≤  e(order k) · graphs(order k)         [e = order k + 1]
```

This bound held cleanly across every order tested (9, 11, 13, 21) once the Stage C elision bug (below) was fixed. There is no fixed expected ratio to assert — the fraction of the `e·graphs` ceiling that survives as distinct, valid dissections is order- and topology-dependent (more battery-edge choices fail validity at small orders), so the gate reports the ratio as **diagnostic**, not pass/fail-banded, and only hard-fails if the ceiling is *exceeded* (a mathematical impossibility signalling real corruption — e.g. a graph's `num_edges` mismatched against its own dissections, or a loader regression reintroducing duplicate rows).

**Elision bug found and fixed in the same session:** Stage C's loader must skip dissection rows sourced from an *elided* graph (`graphs.dual_of IS NOT NULL`). For `v>f` classes this is automatic (the elided `v<f` dual is only ever derived, never fed to `sqt`, so it can't appear in a tablecode file). But for `v==f` classes, **both** members of a non-self-dual pair physically sit in the same plantri file, so `sqt` — which has no concept of "elided" — genuinely solves both, producing real, duplicate-of-the-partner's-rotated-dissections output that the loader must filter out. Verified empirically: 8/8 sampled `v==f` pairs, run through independent `sqt` processes, produced identical (width/height-swapped) dissection sets — confirming a stored graph and its elided partner really are "the same dissection rotated 90°", so dropping the elided side loses nothing.

Two scoping facts baked into the SQL, both from your schema:
- `graphs` has **no `order_val`** — order is `num_edges − 1`. (This is the column that errored in your Gemini session.)
- The identity is over the **3-connected c-nets**. `graphs.category` / `surface_type` must isolate that population; the SQL parameterises it so you set the predicate once (see `§0`).

---

## §0 — Parameters to confirm once

```sql
-- Confirm which predicate isolates the 3-connected plane c-nets that the
-- reconciliation upper bound (§3) covers. Inspect the distribution first:
SELECT surface_type, category, count(*)
FROM graphs
GROUP BY surface_type, category
ORDER BY surface_type, category;
-- Then set the c-net predicate used throughout below, e.g.:
--   surface_type = 'plane' AND category = 1
```

## §1 — Dissection type pivot per order (your query, cleaned)

```sql
-- Legacy version: works while the text `elements` column still exists.
SELECT
  order_val,
  count(*) FILTER (WHERE d_type='SPSR') AS spsr,
  count(*) FILTER (WHERE d_type='SPSS') AS spss,
  count(*) FILTER (WHERE d_type='SISR') AS sisr,
  count(*) FILTER (WHERE d_type='SISS') AS siss,
  count(*) FILTER (WHERE d_type='CPSR') AS cpsr,
  count(*) FILTER (WHERE d_type='CPSS') AS cpss,
  count(*) FILTER (WHERE d_type='CISR') AS cisr,
  count(*) FILTER (WHERE d_type='CISS') AS ciss,
  count(*) FILTER (WHERE d_type='DEGN') AS degn,
  count(*)                              AS grand_total
FROM dissections
GROUP BY order_val
ORDER BY order_val;
```

DEGN must remain countable after its rows are discarded, so persist the counts:

```sql
CREATE TABLE IF NOT EXISTS order_counts (
  order_val    int PRIMARY KEY,
  d_type_counts jsonb NOT NULL,   -- {"SPSR":..., "DEGN":..., ...}
  degn_count   bigint NOT NULL,   -- kept after DEGN rows are dropped
  graph_count  bigint NOT NULL,
  recorded_at  timestamptz DEFAULT now()
);
```

## §2 — Graph counts per order

Total graphs including elided duals (informational -- e.g. for `graph_names` curation, which can name either member of a pair). **§3's reconciliation uses stored graphs only** (`dual_of IS NULL`), not this total, since only the stored side is ever fed through `sqt`.

```sql
SELECT (num_edges - 1) AS order_val, count(*) AS graph_count
FROM graphs
WHERE surface_type = 'plane' AND category = 1   -- the §0 c-net predicate
GROUP BY num_edges
ORDER BY order_val;
```

## §3 — The reconciliation (upper-bound check + diagnostic ratio)

`dissections` never stores DEGN rows (counted then discarded per SPEC-1 Stage C), so the true "incl_degn" total has to pull `degn_count` back in from `order_counts` -- a bare `count(*) FROM dissections` silently undercounts and was a v0.1 bug in this same query.

```sql
WITH d AS (
  SELECT dis.order_val, count(*) + max(oc.degn_count) AS dissections_incl_degn
  FROM dissections dis
  JOIN order_counts oc USING (order_val)
  GROUP BY dis.order_val
),
g AS (
  SELECT (num_edges - 1) AS order_val, num_edges, count(*) AS graphs
  FROM graphs
  WHERE surface_type = 'plane' AND category = 1 AND dual_of IS NULL   -- stored graphs only
  GROUP BY num_edges
)
SELECT
  g.order_val,
  g.graphs,
  d.dissections_incl_degn                                        AS dissections,
  g.num_edges * g.graphs                                         AS upper_bound,   -- e * graphs(k): the combinatorial ceiling (e battery-edge choices per graph)
  g.num_edges * g.graphs - d.dissections_incl_degn                AS headroom,
  round(d.dissections_incl_degn::numeric / (g.num_edges * g.graphs), 4) AS fraction_of_ceiling,  -- diagnostic only, order/topology-dependent, no fixed target
  CASE
    WHEN g.graphs = 0 THEN 'NO GRAPHS (missing slab)'
    WHEN d.dissections_incl_degn > g.num_edges * g.graphs
         THEN 'IMPOSSIBLE -- exceeds e*graphs ceiling, real corruption (duplicate rows, or graph/dissection num_edges mismatch)'
    ELSE 'OK (within ceiling)'
  END AS verdict
FROM g FULL OUTER JOIN d USING (order_val)
ORDER BY g.order_val;
```

On clean regeneration the verdict is always **OK**; `fraction_of_ceiling` is expected to vary by order (more battery-edge choices fail `sqt`'s `s1<=0 || s2<=0` validity check at small orders, so the fraction climbs with order -- observed 0.20 at order 9 up to 0.73 at order 21) and is reported for visibility, not compared against a fixed band. The only hard failure is exceeding the ceiling at all, which is mathematically impossible on a correct load and means something upstream is broken (most likely the `v==f`-class elision filter regressing, or a genuine duplicate-row bug).

## §4 — Structural gates (hard fails, any order)

```sql
-- (a) graph_id linkage — the NULL-graph_id corruption. Target: 0.
SELECT order_val, count(*) AS null_graph_id
FROM dissections WHERE graph_id IS NULL
GROUP BY order_val ORDER BY order_val;

-- (b) duplicate canonical codes — dedup safety net. Target: 0 rows.
SELECT bouwkamp_code, count(*)
FROM dissections GROUP BY bouwkamp_code HAVING count(*) > 1;
-- NOTE: this full-table GROUP BY is what ran for 8–9 hours in your session.
-- Do it per partition after loading, on the UNIQUE index, not table-wide:
--   it is O(1) to enforce at load via UNIQUE(bouwkamp_code); this query is
--   only a belt-and-braces audit, so scope it: WHERE order_val = :k.

-- (c) order-range sanity — no rows above the ingested ceiling. Target: 0.
SELECT order_val, count(*) FROM dissections
WHERE order_val > :max_ingested_order GROUP BY order_val;

-- (d) area check. Every dissection: sum of element squares = width*height.
-- Legacy (text `elements` present):
SELECT dissection_id, order_val, width, height
FROM dissections
WHERE ( SELECT sum((e::numeric)^2)
        FROM regexp_split_to_table(trim(elements), '\s+') AS e
        WHERE e <> '' ) <> (width::numeric * height::numeric)
LIMIT 100;
-- Post-diet (elements dropped): the loader enforces this at COPY time from the
-- packed bouwkamp bytea; this SQL becomes a sampled re-audit via a parse fn.
```

## §5 — Catalogue / OEIS asserts

Seed a reference table from **published** per-order counts (OEIS / your own catalogue), never from the corrupt DB. Then diff.

```sql
CREATE TABLE IF NOT EXISTS ref_counts (
  order_val int NOT NULL,
  d_type    text NOT NULL,
  ref_count bigint NOT NULL,
  source    text,                         -- 'OEIS Axxxxxx' / 'catalogue vN'
  PRIMARY KEY (order_val, d_type)
);

-- Example SPSR-by-order reference (CONFIRM each against OEIS/your catalogue
-- before trusting — these are the values discussed, not yet re-verified):
-- 9..24: 2,6,22,67,213,744,2609,9016,31426,110381,390223,1383905,
--        4931308,17633773,63301427,228130926
INSERT INTO ref_counts(order_val,d_type,ref_count,source) VALUES
 (9,'SPSR',2,'catalogue'),(10,'SPSR',6,'catalogue'),(24,'SPSR',228130926,'catalogue')
 -- ... fill the rest ...
ON CONFLICT DO NOTHING;

-- The assert: any order/type where the DB disagrees with the reference.
SELECT r.order_val, r.d_type, r.ref_count,
       coalesce(a.actual,0) AS actual,
       coalesce(a.actual,0) - r.ref_count AS delta, r.source
FROM ref_counts r
LEFT JOIN (
  SELECT order_val, d_type, count(*) AS actual
  FROM dissections GROUP BY order_val, d_type
) a ON a.order_val=r.order_val AND a.d_type=r.d_type
WHERE coalesce(a.actual,0) <> r.ref_count
ORDER BY r.order_val, r.d_type;
```

The order-24 SPSR reference is **228,130,926**. (An earlier attempt produced 228,130,900 — 26 short, and there are 26 SPSS at order 24; a small, silent, type-boundary slip of exactly the kind this assert catches.) The regenerated order 24 must hit the reference exactly, delta zero. That's the target, not a thing to diagnose in the old data.

## §6 — Duijvestijn regression (the exact query that returned 0 rows)

```sql
-- Presence: the order-21 112x112 must exist and be typed SPSS.
SELECT dissection_id, d_type, order_val, width, height
FROM dissections
WHERE width=112 AND height=112 AND order_val=21 AND d_type='SPSS';
-- Expect exactly 1 row. In the legacy table this returned 0 — it is the
-- canonical regression for the filter_v=f / V=13-class fix.

-- Linkage: all dissections sharing the 112^2 SPSS's graph resolve by graph_id.
SELECT d.d_type, count(*)
FROM dissections d
WHERE d.graph_id = (
  SELECT graph_id FROM dissections
  WHERE width=112 AND height=112 AND order_val=21 AND d_type='SPSS' LIMIT 1)
GROUP BY d.d_type;
-- Expect a populated set (the family of dissections from that graph),
-- not 0 rows — the graph_id-NULL fix is what makes this work.
```

## Gate procedure (per regenerated order k)

1. Load order k into its partition (SPEC-1 Stage C), DEGN rows counted into `order_counts` then dropped.
2. Run §3 → verdict must be **OK (~4)**.
3. Run §4 → (a),(c) = 0; (d) = 0; (b) scoped to `order_val=k` = 0 rows.
4. Run §5 → zero deltas on every type with a reference.
5. Run §6 when k=21.
6. Only then build indexes on the partition and mark `order_counts.status='committed'`.

## Invariants
- `dissections_incl_degn ≤ e·graphs(k)` on regenerated data (§3); exceeding it is impossible on a correct load and is the diagnostic signal, not tuned away.
- Elided graphs (`dual_of IS NOT NULL`) contribute zero dissection rows -- Stage C's loader filters them out even though `v==f`-class elided partners are genuinely solved by `sqt` (see §3 correction above).
- DEGN counted before discard; `order_counts` is the durable record.
- Reference counts come from OEIS/catalogue, never from the DB being tested.
- The table-wide duplicate scan is never run unscoped in production — enforce uniqueness at load, audit per partition.

## Open items
- §0 predicate: confirm `category`/`surface_type` values that isolate the 3-connected c-nets.
- Fill `ref_counts` from your catalogue + OEIS (SPSR, SPSS, SISS, CISS, CPSR, CISR by order); I can generate the full INSERT once you confirm the sequences.
- Post-diet area-check parse function over the packed `bouwkamp bytea`.
