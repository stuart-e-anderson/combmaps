# SPEC-7 — Surfaces pipeline (squared cylinders and tori)

**Version 0.1 (scoped, not yet implemented) · 2026-08-10**
**Role:** resolves the storage-sizing question SPEC-1 flagged as blocking
("Surfaces (cylinder/torus) generation — separate spec... blocked on the
count question for storage sizing") using real enumeration data already on
disk. Two genuinely different situations: **cylinders** have real,
explosive, well-characterized growth, so get the same magnitude-based
stopping rule SPEC-6 used for CISR/CISS; **tori** turn out to have almost
no real enumeration data at all (one known graph, per Stuart's steer) so
this spec instead scopes what's needed to *get* real data — including
naming the new **SPST**/SIST/CPST/CIST types (Stuart's terms) for "squared
square tori" and the concrete `d_type` schema-flexibility gap that blocks
loading any of them, cylinder or torus, today.

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

## Tori: a fundamentally different problem, not just "less data"

Read `torus_dissections_output/00_summary.txt` and `torus_master_solver.sage`
in full before writing this — the 3,077 number is **not** what it looks
like at first glance, and the real situation calls for a different kind of
scoping than cylinders got.

**What's actually there.** Only **one** base graph is known to admit a
perfect torus dissection at all: a 9-vertex rotation system Gambini found
via "a packing backtracker program" (Stuart's description) — a
fundamentally different search method from graph-enumeration-then-solve.
That graph is hardcoded directly into `torus_master_solver.sage` (`line =
"bgficd,adch,..."`). Because a torus has genus 1, its cycle space has rank
2 (vs. a planar graph's rank 1) — so unlike the plane/cylinder solver,
which picks *one* battery edge and gets a unique electrical solution, this
solver computes a full 2-dimensional integer kernel (basis vectors `v1`,
`v2` from the combined KCL/KVL matrix) and scans **integer linear
combinations** `alpha*v1 + beta*v2` for `alpha, beta` in `[-50, 50]` (10,201
combinations), keeping the ones that reduce (dividing out the GCD) to a
set of distinct positive integers. **3,077 of those combinations produced a
valid perfect solution** — that's 3,077 different numeric
scalings/embeddings of *one* combinatorial graph, not 3,077 combinatorially
distinct dissections the way order-13's 1.86M cylinder count is. Comparing
that number directly to cylinder or plane counts would be comparing
different things entirely.

**So "how many squared tori exist" is currently unknown at the level that
actually matters** (distinct graphs), not just under-measured. There is no
order-by-order torus enumeration to characterize the way cylinders were
characterized this session — there's exactly one known example, an
unknown-but-presumably-large space of undiscovered ones, and no systematic
search run yet.

**The real fix exists but hasn't been used.** SPEC-1 was already right to
point at `/home/stuart/Dev/surface_cycles/surftri_0989` — but the actual
generator there is a compiled binary, **`surftri`** (by Thom Sulanke,
explicitly built on plantri's own code/data structures, per its own header
comment), not the sage scripts. `surftri`'s usage line
(`[-uaAgsh -c#xm#pe#f#qy -odb -v -n] n g [res/mod] [outfile]`) takes a
genus parameter `g` — the source (`surftri.c`) shows support for genus 0
(with boundary/holes — the cylinder case), genus 1 (torus), and beyond
(higher genus, plus non-orientable surfaces via negative genus), backed by
precomputed irreducible-triangulation basis files already sitting in the
directory (`genus0.alpha`, `genus1.alpha`, `genus-1.alpha`, `genus0.holes`,
`genus1.holes`, etc.). This is a real, systematic, plantri-equivalent
enumerator for exactly this problem — **and it appears to have been used
for neither cylinders (which used plain `plantri -pe{N}a` instead) nor
tori (which used the one hardcoded Gambini graph) in what's on disk.**
Worth treating "should Stage A actually be built on `surftri`, for both
cylinder *and* torus, instead of plain `plantri`" as a live question that
could also affect SPEC-7's cylinder section above, not a torus-only
concern.

**SPST and friends.** Per Stuart: `T` (torus) extends the existing
shape axis the same way `C` (cylinder) did in the section above — so the
taxonomy becomes (simple/compound) × (perfect/imperfect) × (rectangle/
square/cylinder/torus). Confirmed name: **SPST** = Simple Perfect Squared
Torus (the one known example is this type). By direct analogy: **SIST**
(Simple Imperfect), **CPST**/**CIST** (Compound Perfect/Imperfect), and
presumably trivial-compound variants (`TCIST` etc.) once compounds are
findable at all. Given exactly one SPST is known and nothing is known yet
about the other three, there's no basis for guessing which will turn out
rare and which common — plane/cylinder both show imperfect and compound
types vastly outnumbering simple-perfect ones once they appear at all, so
that pattern (SIST/CIST possibly far more numerous than SPST once real
search exists) is a reasonable prior, not a conclusion.

**Schema flexibility — a concrete, mechanical gap, true for cylinders too.**
`dissections.d_type` is `CHECK (d_type IN ('SPSR','SPSS','SISR','SISS',
'CPSR','CPSS','CISR','CISS'))` — a hardcoded 8-value enum. **Every single
new type from both this section and SPEC-6/the cylinder section above
(SPSC/SISC/CPSC/CISC, SPST/SIST/CPST/CIST, plus trivial-compound variants)
is currently impossible to insert at all** until that constraint is
widened. This is exactly the flexibility gap Stuart asked about — not a
future concern, a blocking one the moment any surface or compound row is
loaded. Cheapest fix is probably just growing the CHECK list as new types
are confirmed; a lookup table (`d_types(code, simple, perfect, shape)`)
would be more open-ended if the taxonomy keeps growing (it's already at
16+ plausible values across rectangle/square/cylinder/torus), worth
deciding when the CHECK constraint is actually touched rather than now.

**Space constraints, honestly.** Cylinders had a real number to design
against (explosive but *known* growth). Tori don't yet — one row's worth of
data. The only design goal that's actually actionable right now is making
sure the schema doesn't structurally block storing torus rows when they do
turn up (the `d_type` fix above, plus `surface_type='torus'` already
existing), not computing a storage budget from a sample size of one.

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
6. **`d_type` extensibility — done 2026-08-10.** Widened
   `dissections_d_type_check` (both the live DB, via `DROP`/`ADD CONSTRAINT`
   on the partitioned parent -- confirmed it propagates to every partition,
   28 matching constraints afterward -- and `db/schema/dissections.sql` so a
   fresh install matches) to add the 8 new shape values: `SPSC`/`SISC`/
   `CPSC`/`CISC` (cylinder) and `SPST`/`SIST`/`CPST`/`CIST` (torus), 16
   total. Smoke-tested: an `SPST` row now passes the `d_type` check (test
   insert only failed on an unrelated NOT NULL column, rolled back, zero
   rows left behind). Deliberately did **not** add `TCISR`/`TCPSR`-style
   trivial-compound variants seen in the raw cylinder data -- whether
   trivial-vs-nontrivial compound should be its own `d_type` code (and if
   so, `CHAR(4)` needs widening too, since `TCISR` is 5 characters) or a
   separate boolean column is still an open design question, not resolved
   by this migration. Lookup-table-vs-CHECK-list tradeoff also still open,
   deferred until the taxonomy grows past these 16.
7. **Evaluate `surftri` as the real Stage A generator** for both cylinder
   and torus (genus 0-with-holes and genus 1 respectively), rather than
   plain `plantri` for cylinders and a hardcoded one-off script for tori —
   it's already built for exactly this, unused so far.
8. **Generalize the torus solver** away from Gambini's one hardcoded graph:
   needs a Stage-A-style loop over `surftri`-enumerated genus-1 graphs, each
   fed through the 2D-kernel (alpha/beta) solve `torus_master_solver.sage`
   already implements for one graph. Real research/engineering work, not a
   parameter tweak.
9. **`ref_counts`**: not attempted — no OEIS search done yet for cylinder/
   torus sequences. Same empirical-validation discipline as SPEC-6 applies:
   don't guess.

## Suggested order of work

1. ~~Widen `d_type`'s `CHECK` constraint~~ — **done 2026-08-10**, see item 6
   above. The lookup-table-vs-CHECK-list question is still open but not
   blocking anything right now.
2. Evaluate `surftri` against the existing plain-`plantri` cylinder
   approach (item 7 above) — decide whether cylinder Stage A should be
   rebuilt on it before investing further in the current one.
3. Confirm `-e{N}a` semantics either way, and whether cylinder's sage-solver
   output can be trusted as-is for real loading or needs the same scrutiny
   SPEC-1's `sqt` got (byte-identical-output verification etc.).
4. Decide sage-based vs. ported-to-frozen-pipeline for cylinders — gates
   the rest of that track.
5. Build cylinder's per-type stopping logic.
6. For tori — a genuinely separate track, not blocked on 1-5: build a
   `surftri`-based genus-1 Stage A, then generalize the alpha/beta solver
   to run over every graph it produces instead of Gambini's one hardcoded
   example. Only after real per-graph data exists does a stopping/sizing
   decision become possible — there's nothing to decide yet.
7. Once both tracks produce real data: `category`/`surface_type`
   interaction, `order_counts` key, `ref_counts`.

## Open items carried forward
- Exact semantic difference between e.g. `SPSR` and `SPSC` (and the other
  paired type names) in the cylinder context — not blocking the sizing
  conclusion, but needed before building a loader that classifies correctly.
- Whether cylinder Stage A should be rebuilt on `surftri` instead of plain
  `plantri` — open question raised by finding `surftri` unused for both
  surface types.
- Generalizing the torus solver beyond one hardcoded graph — the actual
  blocker on ever having real torus enumeration data.
- Whether cylinder/torus graphs need their own connectivity axis on top of
  `surface_type`, interacting with SPEC-6's `category` column.
- `d_type` CHECK-constraint vs. lookup-table decision, once it's actually
  touched.
