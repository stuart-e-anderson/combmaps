# SPEC-7 — Surfaces pipeline (squared cylinders and tori)

**Version 0.1 (scoped, not yet implemented) · 2026-08-10**
**Role:** resolves the storage-sizing question SPEC-1 flagged as blocking
("Surfaces (cylinder/torus) generation — separate spec... blocked on the
count question for storage sizing") using real enumeration data already on
disk, and sets the completion criterion the same way SPEC-6 did for
CISR/CISS: a magnitude-based stopping rule per type, not a fixed order
target.

---

## Background

`graphs.surface_type` already supports `'plane' | 'cylinder' | 'torus'` in
the schema, and squared cylinders/tori were explicitly in Stuart's original
v1 answer (`Rebuilding-squaring.net-with-database-driven-design.md`, Q1),
alongside the eight plane types. But every graph currently loaded is
`'plane'` — surfaces were deferred at the SPEC-1 stage specifically because
their per-order dissection counts were unknown, and the 2TB total storage
budget's "~1.2TB surface reserve" was provisioned without a real number
behind it (the design conversation: *"If they're comparable to the plane
counts, the... reserve holds... If they're an order of magnitude larger,
the plane ceiling drops back to 24 to make room."*).

Existing tooling: `/home/stuart/Dev/surface_cycles/surftri_0989/` — a
research/exploration codebase (SageMath solvers, not the production C++/
Python SPEC-1 pipeline), containing `cylinder_solver.sage`/
`cylinder_solver_batch.sage`, `bk2ps` (rendering), and driver scripts
(`batch_test_cyl*.sh`) that run plantri with an `-e{N}a` flag pattern
(exact semantics of the trailing `a` not confirmed — worth checking before
reuse) piped into the sage solver.

## Real enumeration data (orders 7-13, squared cylinders)

`squared_cylinders/order_{N}/` holds one subdirectory per type, one SVG file
per dissection — confirmed this is a genuine exhaustive per-order plantri
enumeration, not a sample: `batch_test_cyl.sh`'s comments document the exact
expected graph count per plantri class per order (e.g. "order 17... 14
graphs... 768 graphs... 2635 graphs, total: 3417 graphs") and the script
runs every class through the solver in turn. Types found on disk: `SPSR`,
`SPSC`, `SISR`, `SISC` (Simple Imperfect Squared Cylinder, per Stuart),
`SISS`, `CISR`, `CISS`, `TCISR`, `TCPSR` (`T` prefix = trivial, matching the
CPSR naming pattern from SPEC-6). Exact semantic distinction between e.g.
`SPSR` and `SPSC` in this cylinder context not yet confirmed — noted as an
open item, not blocking the sizing question.

Per-type file counts (= dissection counts):

| order | SPSR | SPSC | SISR | SISC | SISS | CISR | CISS | TCISR | TCPSR |
|---|---|---|---|---|---|---|---|---|---|
| 9  | 13 | 7 | 222 | 104 | — | 18 | — | 604 | — |
| 10 | 38 | 52 | 2,317 | 972 | 89 | 793 | — | 4,218 | 7 |
| 11 | 153 | 318 | 18,610 | 8,663 | 201 | 6,262 | 145 | 27,492 | 46 |
| 12 | 417 | 983 | 66,428 | 43,348 | 639 | 16,280 | 113 | 100,912 | 148 |
| 13 | 1,467 | 4,909 | 574,144 | 389,835 | 1,736 | 160,092 | 537 | 731,694 | 592 |

**Total dissection files by order** (all types): 7→67, 8→370, 9→962,
10→8,478, 11→61,881, 12→229,259, **13→1,864,997**. Total disk (SVG, orders
7-13): 9.1GB — not the real storage format (`bouwkamp_code bytea` would be
far more compact, same as the plane pipeline), but the **counts** are what
matters for sizing.

**Comparison to plane at the same order**: by order 13, squared-cylinder
dissections already outnumber plane dissections at order 13 (296 total) by
~6,300x, and cylinder-order-13's raw volume (1.86M) is already comparable
to **plane order 20-21** (1.5M-5.3M). Confirms the design conversation's
"order of magnitude larger" concern was a significant understatement.

## Tori: much less characterized than cylinders

`torus_dissections_output/` (3,077 SVG files) and `torus_orthogonal_output/`
(1 example run, "Gambini 9-Vertex Graph") exist, but **neither is organized
by order or type** the way `squared_cylinders/` is — these read as
exploratory/prototype output, not a systematic per-order enumeration. No
sizing data available for tori yet. Treated as a separate open item, not
assumed to follow the same growth curve as cylinders without evidence.

## Decision: magnitude-based stopping, per type

Same principle as SPEC-6's CISR/CISS criterion: **not** a fixed order
target matching plane's backfill range — run each type until its per-order
count reaches roughly SPSR-order-16-18 magnitude (~9,016-110,381), then stop
generating further orders *for that type specifically*.

Applying that to the real data above, growth rates differ sharply by type,
so the natural stopping order is **not uniform across types** — this is a
genuinely per-type decision, not a single "stop the whole cylinder run at
order N":

- **Already crossed the target band by order 12-13** (would stop very early
  in a first pass): `SISR` (crosses ~order 11), `SISC` (~order 12), `CISR`
  (~order 12), `TCISR` (~order 11-12, already at 731,694 by order 13, well
  past the upper bound).
- **Still well below the band at order 13**, would need several more
  orders run to reach it: `SPSR` (1,467), `SPSC` (4,909), `SISS` (1,736),
  `CISS` (537), `TCPSR` (592).

Practical implication: continuing a single combined batch run to "catch up"
the slow types would let the fast types balloon far past their stopping
point for no benefit (`TCISR` alone would likely exceed a million more
dissections per additional order). The existing sage-based tooling was
built for exploration, not for this kind of selective per-type early
stopping — **needs new logic** (or a wrapper) to keep generating a given
order's graphs but stop *loading/solving* dissections of a type that's
already crossed its target, while continuing types that haven't. Not a
small tweak, worth scoping as its own implementation task before running
anything further.

## What needs to change / build

1. **Confirm the `-e{N}a` plantri flag's exact meaning** (not yet checked
   against `plantri-guide.txt` the way `-c2m3`/`-d` were for SPEC-6) before
   trusting or reusing the existing driver scripts.
2. **Decide whether this stays SageMath-based or gets ported into the
   SPEC-1-style pipeline** (plantri driver → frozen solver → Postgres loader
   → gate) for consistency with the rest of the system. Not decided here —
   the existing sage solver clearly works (produced the real data above),
   but SPEC-1's whole design philosophy is a frozen, auditable solver
   binary; porting is a real question, not an assumed yes.
3. **Per-type stopping logic**, as above — genuinely new, not in the
   existing tooling.
4. **`graphs.category`/`surface_type` interaction**: `surface_type` already
   exists for this (`'cylinder'`/`'torus'`), separate from the `category`
   axis SPEC-6 is using for connectivity (3-connected vs 2-connected planar
   populations) — need to confirm both axes combine cleanly for surfaces
   (e.g. are cylinder graphs 3-connected-only, or do they need their own
   connectivity story analogous to SPEC-6's, on top of being non-planar?
   Not yet investigated).
5. **`order_counts`**: already getting a `category` column per SPEC-6; needs
   confirmation it also naturally extends to `surface_type`, or whether
   that's a separate key dimension again.
6. **Tori**: characterize real per-order-per-type counts the same way this
   session did for cylinders, before any sizing/stopping decision can be
   made for that surface type. Not started.
7. **`ref_counts`**: not attempted — no OEIS search done yet for cylinder/
   torus sequences. Same empirical-validation discipline as SPEC-6 applies:
   don't guess.

## Suggested order of work

1. Confirm `-e{N}a` semantics and whether the sage solver's output can be
   trusted as-is for real loading, or needs the same kind of scrutiny
   SPEC-1's `sqt` got (byte-identical-output verification etc.).
2. Decide sage-based vs. ported-to-frozen-pipeline (item 2 above) — this
   gates everything else.
3. Build the per-type stopping logic.
4. Characterize tori the same way cylinders were characterized this
   session, before assuming their growth curve.
5. Only then: schema decisions (`category`/`surface_type` interaction,
   `order_counts` key), and a real backfill.

## Open items carried forward
- Exact semantic difference between e.g. `SPSR` and `SPSC` (and the other
  paired type names) in the cylinder context — not blocking the sizing
  conclusion, but needed before building a loader that classifies correctly.
- Torus data is unorganized/exploratory only; no sizing conclusion possible
  yet for that surface type.
- Whether cylinder/torus graphs need their own connectivity axis on top of
  `surface_type`, interacting with SPEC-6's `category` column.
