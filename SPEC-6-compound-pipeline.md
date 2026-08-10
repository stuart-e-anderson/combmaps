# SPEC-6 — Compound pipeline (CPSR/CPSS/CISR/CISS)

**Version 0.1 (scoped, not yet implemented) · 2026-08-10**
**Role:** two new Stage-A-family generation tracks alongside SPEC-1's existing
3-connected one, extending the `graphs.category` axis SPEC-2 §0 left open.
Scoped through a session of direct back-and-forth with Stuart; every decision
below reflects an actual answer he gave, not an assumption.

---

## Why this is separate from SPEC-1

SPEC-1's Stage A enumerates **3-connected** planar maps only (`-c3` in
`stage_a_driver.py`). That's correct for SPSR/SPSS/SISR/SISS, but a compound
squared rectangle/square is (informally) an assembly of smaller perfect
squared rectangles, and that assembly is generically not 3-connected — so
CPSR/CPSS/CISR/CISS need genuinely different graph populations. SPEC-1
itself already flagged this: *"CISS/CISR (and any 2-connected-dependent
type) are marked partial honestly rather than implied complete."*

Confirmed empirically 2026-08-10: the DB's existing CPSR counts from the
3-connected population (1, 3, 11, 42, 108 at orders 17-21) are rare
incidental byproducts (a zero-current edge in the electrical solve causing a
cross-intersection), ~1000x smaller than every OEIS compound sequence found
at the same orders. Nothing dishonest is currently claimed —
`order_counts.plantri_classes_fed` already only lists the 3-connected
classes fed, for every order — this spec is about closing the gap, not
fixing a bug.

## Two populations, not one

| | connectivity | min degree | why |
|---|---|---|---|
| **CPSR/CPSS** | exactly 2-connected | 3 | perfect tilings still need no degree-2 vertices (same reason SPSR/SPSS require it) |
| **CISR/CISS** | exactly 2-connected | 2 | *imperfect* tilings are what degree-2 vertices produce (forced equal-current, equal-size adjacent squares) — this population is the point, not a thing to exclude |

`-m2` is very likely redundant with `-c2` alone — a 2-connected graph can't
have a degree-1 (or lower) vertex, so minimum degree 2 should already be
automatic. Worth passing explicitly for self-documenting code either way;
not confirmed to be doing independent filtering work, not blocking.

## Generation strategy: reuse the existing pattern, no `-d` needed

Considered and rejected using plantri's `-d` switch (writes the dual graph
instead of the original, filters still apply to the original — confirmed in
`plantri-guide.txt`) to generate both sides of each population. Rejected
because: **the dual side is never solved, only hashed**, for every one of
these types, same as SPSR/SPSS today — Stuart confirmed the "dual gives the
same dissection rotated 90°" rule holds for 2-connected graphs exactly as it
does for 3-connected ones. Since the existing `process_v_gt_f_class`/
`process_v_eq_f_class` pattern in `stage_a_driver.py` already gets every
graph's full rotation system from a single plantri search and derives the
dual's canonical hash locally in Python (`dual_rotation_system` +
`canonical_hash_codes_batch`, no new search), using `-d` to get the dual
side would mean **paying plantri's full combinatorial search cost a second
time** for something already available for free from data already in
memory. So: **reuse the exact existing pattern for both new populations**,
parameterized by:
- the plantri connectivity/degree flag (`-c3` → `-c2m3` or `-c2`)
- the `valid_vf_classes` bound (below)

## `valid_vf_classes` bounds

Derived from Euler's formula plus the relevant degree constraint (worked
through with Stuart, cross-checked against his 2-connected-graph identities):
- **Upper bound** (`e <= 3v-6`, i.e. `min_v = ceil((e+6)/3)`) comes from the
  general simple-planar bound and is **connectivity-independent** — same for
  every population.
- **Lower bound** comes from the degree constraint: min-degree-3 gives
  `e >= ceil(3v/2)` (today's bound, `max_v = floor(2e/3)`); min-degree-2
  relaxes this to `e >= v` (`max_v = e`).

So:
- **CPSR/CPSS**: identical bounds to today's SPSR/SPSS
  (`ceil((e+6)/3) <= v <= floor(2e/3)`) — **no code change needed**. The
  triangulation boundary class (`v = max_v`) will simply come back empty
  under `-c2m3`, since triangulations are exclusively 3-connected — expected
  behavior, not a bug to special-case.
- **CISR/CISS**: `min_v` unchanged, `max_v` grows to `e` — a much wider
  range than today, matching Stuart's "far more numerous" warning. Sanity
  check: the extreme case `v = e` forces `F = 2` by Euler's formula, which
  is exactly a simple `e`-cycle (2-connected, every vertex degree exactly
  2) — the bound is tight and the boundary case is a real, sensible graph.

`valid_vf_classes` needs a `min_degree` parameter (3 default, matching
today; 2 for CISR/CISS) rather than being CPSR/CISR-specific.

## What's reusable unchanged

- **Stage B (`sqt`)**: no code changes expected — it's a generic electrical-
  network solver, multi-edges are just parallel resistors, and the 8-type
  classification (`is_compound`/`is_perfect`/`is_square`) is a property of
  the solved tiling, not of which population fed it in. One doc comment
  ("3-connected planar map files") is descriptive, not an enforced
  assumption — worth eyes-on confirmation before fully trusting, not just a
  grep.
- **`squaringlib.planar.run_plantri`/`run_plantri_sharded`**: already accept
  arbitrary `extra_args` and the verified `res/mod` sharding — the
  connectivity/degree flag is a drop-in swap.
- **Stage C's dedup-at-load** (`ON CONFLICT (order_val, bouwkamp_code) DO
  NOTHING`): the ~285 existing incidental CPSR rows are a subset of what the
  correct population will regenerate, so they just no-op on reload, no
  special reconciliation needed.
- **`graphs.category`**: already exists, unused so far, exactly for this
  (`category=1` current; `category=2` CPSR/CPSS; `category=3` CISR/CISS).
- **`dissections` table**: already treats all eight `d_type`s completely
  equally — one table, one CHECK constraint listing all eight, no per-type
  hierarchy. No schema change needed here; this already satisfies Stuart's
  requirement that every type have equal status as a queryable/displayable
  collection.

## What needs to change

1. **Stage A**: parameterize the existing driver (connectivity/degree flag,
   `valid_vf_classes(e, min_degree=3)`) rather than write a new script from
   scratch — the `v>f`/`v==f` split, sharding, and dual-hash derivation all
   carry over unchanged.
2. **Stage C loader**: currently never sets `category`/`surface_type` on
   `INSERT`/`COPY` (always the schema default, `category=1`). Needs a
   `--category` argument (or read it from Stage A's `provenance.json`).
   **This is the one change that actively matters for correctness** —
   without it, the new populations would silently merge into `category=1`
   and corrupt SPEC-2 §3's upper-bound reconciliation.
3. **`order_counts` schema**: **resolved this session** — add a `category`
   column, widen the primary key to `(order_val, category)`. Chosen over a
   separate bolt-on table per Stuart's explicit requirement that every
   population have equal status, not an implicit primary-vs-secondary
   hierarchy. Each `(order, category)` pair gets its own independent
   `graph_count`/`plantri_classes_fed`/`status` row.
4. **SPEC-2 §0/§3 predicates**: needs confirmed predicates for `category=2`
   and `category=3` (probably just `surface_type='plane' AND category=N`,
   symmetric with today's check), and — not yet re-derived — whether
   `e·graphs(k)` (battery-edge-per-graph) is still the right upper-bound
   ceiling for these relaxed-connectivity populations, or whether the
   relaxation changes what "every edge can be the battery edge" means.
5. **`ref_counts`**: deliberately **not** populated by guessing a symmetry
   convention. CPSR candidates: A217153/A217152 (nontrivial, two
   subrectangle-symmetry conventions), A217374/A217375 (trivial, same two
   conventions) — starts at order 13. CPSS candidates: A217155 (square
   symmetries only), A181340 (square + subrectangle symmetries) — **starts
   at order 24**, confirmed via `A217156` (=SPSS+CPSS: orders 21-23 equal
   the already-loaded SPSS-only values exactly, i.e. CPSS=0 there; order 24
   = 30, and 30−26(SPSS) = 4, matching A217155(24) exactly). No CISR/CISS
   candidates searched yet — plausibly obscure enough that none exist in
   OEIS at all, in which case correctness needs a different anchor (internal
   structural consistency, or Stuart's own prior results, rather than an
   external reference). Resolution method, per Stuart: **the same empirical
   method that worked for SISR/SISS** — build the pipeline, generate real
   per-order counts, test them against every candidate sequence, keep
   whichever matches exactly. Not resolvable by reasoning about names alone.
6. **General principle for filling in any future `ref_counts` row**: per
   Stuart, OEIS (following the 1940 Brooks-Smith-Stone-Tutte paper and
   Duijvestijn's convention) often counts squares *within* "squared
   rectangle" sequences. This schema deliberately splits by shape (matching
   how the public actually thinks about squares vs. rectangles, not the
   mathematical convention that conflates them) — this is exactly the
   A002839-vs-A219766 trap already hit once this session. Always check
   whether a candidate sequence is the combined or shape-split version
   before trusting it, and verify empirically against real loaded data
   wherever that's possible.

## CISR/CISS completion criterion (not a full backfill)

Per Stuart: CISR/CISS graph populations grow much faster than SPSR's, so the
target isn't matching SPSR's order range — it's running each order **until
its per-order dissection count reaches roughly the magnitude of SPSR orders
16-18** (~9,000 to ~110,000 dissections), then stopping. This can't be
predicted analytically ahead of running it — needs to be measured order by
order.

## Cost: unknown, not yet measured

2-connected populations are supersets of the corresponding 3-connected ones
at the same `(v,e)` (looser connectivity constraint = more graphs), so both
new tracks are very plausibly more expensive per order than the existing
3-connected backfill — which itself needed sharding by order 20-21. No
benchmarking done this session. First move for either track should be
timing/counting at small test orders (13-17 for CPSR, wherever CISR first
appears for that track) before committing to any backfill range — same
discipline as order 22's Stage B/C being deliberately not started without a
cost check-in first.

## Suggested order of work

1. Parameterize Stage A + `valid_vf_classes` (CPSR/CPSS track first — bounds
   already match today's, lowest-risk starting point).
2. Add `--category` to Stage C loader.
3. Migrate `order_counts` to `(order_val, category)`.
4. Run CPSR/CPSS at small orders (13-17), measure cost, check in before
   scaling.
5. Test real CPSR/CPSS output against the candidate `ref_counts` sequences
   above; only then fill in `ref_counts` for real.
6. Extend SPEC-2's gate SQL for `category=2`/`3`.
7. CISR/CISS track: same Stage A/C machinery, `min_degree=2`, run per-order
   until Stuart's magnitude-based stopping point, no fixed order target set
   in advance.

## Open items carried forward
- Confirm `sqt`'s "3-connected planar map files" comment is descriptive
  only, not an enforced assumption, by reading (not just grepping) the
  solver before the first real CISR/CISS run.
- SPEC-2 §3's upper-bound identity re-derivation for the relaxed-degree
  population (item 4 above).
- CISR/CISS `ref_counts` reference — may not exist in OEIS at all.
