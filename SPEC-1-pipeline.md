# SPEC-1 — Frozen generation pipeline

**Version 0.1 · 2026-08-07 · depends on:** answers Q4 (order ceiling), Q9 (dual multiplier)
**Grounded in:** `sqtv4_3.cpp`, `bk2svg.py`, `bk2ps.cpp`, `bouwkamp_bigint_v4.py`, and the directory pointers below.

---

## Goal
Produce, for each order, a clean, deduplicated, provenance-stamped set of dissection tablecodes plus per-order counts, generated deterministically from plantri and gated before anything touches Postgres. No stage "improves" a working stage; changes go through a version bump and a re-run of the gate.

## The pipeline (one job per stage, joined by files/pipes)

```
plantri driver ─▶ sqt (frozen) ─▶ typed tablecode files ─▶ loader ─▶ reconcile gate ─▶ COMMIT partition
   (Euler-        (solve+classify   (spss/spsr/siss/sisr/   (COPY,        (graphs×N vs
    correct        +canonical        cpss/cpsr/ciss/cisr     link         Σ types; OEIS
    v-class        +dedup+DEGN        + degenerate)          graph_id)    asserts)
    driver)        separate)
```

### Stage A — plantri driver
- **Job:** enumerate the correct planar-map classes for a target order, once, with correct Euler bookkeeping. Never skip a vertex class.
- **The bug to kill:** the old driver's `if [ $v -gt $f ]; then continue; fi` skipped V>F classes, which is why Duijvestijn's order-21 112² (13 vertices, 11 faces) was never generated. For a target order `k` (edges `e = k+1`), generate every valid `(v,f)` with `v+f = e+2`, `3 ≤ v`, `e ≤ 3v−6`. Generate the `v>f` classes as **triangulations** and derive the `f>v` duals post-generation rather than asking plantri for cubic graphs directly (plantri makes triangulations far more cheaply; the dual is the same dissection rotated 90°).
- **Dual/self-dual split:** use `/home/stuart/Dev/nauty/filter_v=f` to identify self-dual graphs and split the `v=f` class into {graph, dual, self-dual}; process only one of each graph/dual pair (they yield the same dissections up to rotation). This is what keeps graph counts honest for reconciliation.
- **Output:** plantri planar_code files, one per `(v,f)` class, named with order + class.
- **Provenance:** record plantri version + exact invocation per class.

### Stage B — sqt (FROZEN — do not refactor internals)
- **Job:** solve, classify, canonicalise, dedup, separate degenerates. This is `sqtv4_3.cpp`, version-locked.
- **Arithmetic model (as-built, accepted):** `K = AᵀA` reduced Laplacian; `det = InvertMatrix(K,V)` = spanning-tree count = `complexity`; currents recovered from the double-precision inverse by `round()` + per-row gcd (`R[i]`). Valid to ~order 69; warns at ≥70 edges. **Beyond the envelope**, route the class through `/home/stuart/Dev/Ramanujan/polyhedrons` (exact/bignum solver) instead — same tablecode contract out, so downstream stages don't care which solver produced a row.
- **Classification (verbatim, the logic that "worked perfectly"):** `is_square` = (s1==s2); `is_perfect` = (all |currents| distinct); `is_compound` = `simple_compound_test(...)` (pure `long long` sub-rectangle corner/edge test; simple iff `squares==order && rectangles==1` or `squares==order+1 && rectangles==0`). The eight types are the (compound?)×(perfect?)×(square?) product.
- **Canonical code:** representative with the largest top-left corner square (squares get the extra boundary-square tie-break); dedup within run via `std::set<string>`.
- **Degenerates:** any zero-size element (or `" 0 "` in the emitted code) → `-degenerate.txt`, **not** dropped silently — counted for reconciliation, loaded to no partition.
- **THE ONE ALLOWED CHANGE — graph linkage:** `sqt` currently writes tablecodes with no reference to the source graph, which is the root cause of the `graph_id`-NULL corruption. Add a minimal, additive emit: each tablecode line is prefixed (or paired in a sidecar) with the source graph's canonical key — reuse the existing `hash_code` (nauty canonical certificate) already stored in `graphs.hash_code`. This does not touch the solver or classifier; it records what `sqt` already knows at emit time (which graph it is processing). Output contract: `(graph_hashcode, d_type, tablecode)`.

### Stage C — loader
- **Job:** `COPY` typed files into the order partition, **populating `graph_id NOT NULL`** by joining `graph_hashcode → graphs.graph_id`.
- Load into an **unindexed, order-partitioned** table; build indexes once at the end. Binary `COPY`, never row `INSERT`.
- Enforce at load: `graph_id NOT NULL`; `bouwkamp_code` UNIQUE (cross-class dedup safety net); reject any row failing the area check `Σ elementᵢ² = width·height`.
- **Schema diet applied here** (from the budget work): pack `bouwkamp_code` as `bytea`; do **not** store `elements` (derive from the code) or the materialised `sb_path` string (keep only `ratio_cf`; the continued fraction *is* the Stern-Brocot path — index a prefix if search needs it).
- Stamp provenance per order: `(tool='sqt', version, git_sha, plantri_version, run_date, plantri_classes_fed, status)`.

### Stage D — reconcile gate (see SPEC-2)
- No partition commits until: `graphs(order) × N ≈ Σ dissection_type counts` (N = 4 or 8 per Q9); each type count matches OEIS/your published catalogue where one exists; zero NULL `graph_id`; zero duplicate tablecodes; area check passes for every row; Duijvestijn 112² present and typed **SPSS** (the specific regression that was failing).

## Renderers (separate lane — presentation, not generation)
`bk2svg.py` / `bouwkamp_bigint_v4.py` (SVG, unlimited size via Decimal-scaled skyline tiler) and `bk2ps.cpp` (PostScript, ≤ order 46 due to the 32-bit PS integer limit). These consume stored `bouwkamp_code` (or a freshly solved code for the on-demand tail) and are what the website calls to draw a dissection. They are not in the generation gate.

## Invariants
- Frozen binaries: `sqt`, the classifier, the canonicaliser do not change mid-project. Version bump + gate re-run for any change.
- `graph_id NOT NULL` always; the file-boundary graph-linkage gap never recurs.
- Degenerates are counted, then discarded — never silently dropped, never loaded.
- Double-precision within the validated envelope; exact/bignum fallback beyond it; same tablecode contract either way.
- Area check on every row at load.
- Completeness flag records *which plantri classes were fed*, so CISS/CISR (and any 2-connected-dependent type) are marked partial honestly rather than implied complete.

## Acceptance gates (machine-checkable)
1. End-to-end on orders 9–13 reproduces your existing catalogue tablecodes byte-for-byte.
2. Order 21 regenerated: Duijvestijn 112² present, typed SPSS; the "dissections from the 112² graph" query returns the full set (the exact query that returned 0 rows becomes a passing regression test).
3. Per-order eight-type split matches OEIS/your published counts on every order where a reference exists.
4. Zero NULL `graph_id`; zero duplicate `bouwkamp_code`; area check passes on 100% of rows.
5. Reconciliation identity green (SPEC-2).

## Non-goals (explicitly out of scope for SPEC-1)
- Splitting `sqt` into separate solver/classifier/canonicaliser binaries (the file-output boundary already provides the decomposition; re-splitting risks the exact bugs we're eliminating).
- Special-property / geometry columns (crossed, boundary, corner) — SPEC-4.
- The query API — SPEC-5.
- Surfaces (cylinder/torus) generation — see `SPEC-7-surfaces-pipeline.md`. The count question is resolved (real per-order-per-type cylinder data pulled from `/home/stuart/Dev/surface_cycles/surftri_0989`, 2026-08-10: cylinder dissections already outnumber plane's at the same order by ~6,300x by order 13); scoped, not yet implemented.

## Open items feeding this spec
- **Q4:** order ceiling for the bulky types (24 safe floor, 25 with the schema diet).
- **Q9:** does `graphs` store landscape-only representatives or both graph and dual? Sets N=4 vs N=8 in the reconciliation identity, and whether `dual_of` needs backfilling. Reading `filter_v=f` in Claude Code will confirm what the driver actually emitted.
- Confirm `graphs.hash_code` is the nauty canonical certificate (so it's a sound join key for the graph-linkage emit).
