# SPEC-7 — Surfaces pipeline (squared cylinders and tori)

**Version 0.2 (scoped, not yet implemented) · 2026-08-11**
**Role:** resolves the storage-sizing question SPEC-1 flagged as blocking
("Surfaces (cylinder/torus) generation — separate spec... blocked on the
count question for storage sizing") using real enumeration data already on
disk. **Cylinders and tori turned out to be structurally different problems,
not just two instances of the same one:**
- **Cylinders are genus 0** — the same graphs `plantri` already enumerates
  for the plane pipeline. No new graph generation at all; a different
  *solve* over graphs SPEC-1's Stage A already produced. Real, explosive,
  well-characterized growth (real data through order 13), so gets the same
  magnitude-based per-type stopping rule SPEC-6 used for CISR/CISS.
- **Tori are genus 1** — a genuinely different graph population, needing
  `surftri`'s exhaustive genus-1 generation (confirmed by Stuart, below),
  and currently have almost no real enumeration data (one known graph).
  This spec scopes what's needed to *get* real data, not a sizing decision
  — there's nothing to size yet.

Both need the `d_type` taxonomy extended (done — see below) and the new
**SPST**/SIST/CPST/CIST types (Stuart's terms) for "squared square tori."

---

## Background

`graphs.surface_type` already supports `'plane' | 'cylinder' | 'torus'` in
the schema, and squared cylinders/tori were explicitly in Stuart's original
v1 answer (`Rebuilding-squaring.net-with-database-driven-design.md`, Q1),
alongside the eight plane types. Surfaces were deferred at the SPEC-1 stage
specifically because their per-order dissection counts were unknown, and
the 2TB total storage budget's "~1.2TB surface reserve" was provisioned
without a real number behind it.

Existing tooling: `/home/stuart/Dev/surface_cycles/surftri_0989/` — a
research/exploration codebase (SageMath solvers, not the production C++/
Python SPEC-1 pipeline), containing `cylinder_solver.sage`/
`cylinder_solver_batch.sage` (the cycle-basis solver — see below, this is
the right tool, not a placeholder), `bk2ps` (rendering), driver scripts
(`batch_test_cyl*.sh`), and the compiled `surftri` binary (Thom Sulanke,
built on plantri's own code/data structures) for genuinely non-planar
graph generation.

## How cylinder dissections are actually produced (resolved 2026-08-11)

Asked Stuart directly why the raw cylinder data has folders literally named
`SPSR`/`SISR` — the same codes as the plane catalogue — sitting next to
cylinder-specific ones (`SPSC`/`SISC`/etc). It's neither a naming collision
nor inconsistent labeling. The mechanism:

**The cylinder solver runs a full cycle-basis decomposition** (take a
spanning tree of the graph; the co-tree edges define the fundamental
cycles) **on an ordinary 3-connected planar graph — the same graphs
`plantri` already enumerates for the plane pipeline, confirmed directly by
Stuart: "it works directly."** No separate graph generation step for
cylinders at all. The cycle basis splits into two kinds of cycle:
- **Face cycles** — bound an actual face of the planar embedding. Solving
  with these reproduces exactly the same object as the plane pipeline's
  electrical-network construction: an ordinary squared rectangle. Hence
  the `SPSR`/`SISR`/`CISR`/`CISS`-named folders in the raw data — correctly
  labeled, and **genuinely redundant with what SPEC-1 already loaded.**
- **Homological cycles** — don't bound a face; they wrap around the
  surface. Solving with these is what actually produces the squared
  cylinder (`SPSC`/`SISC`/`CPSC`/`CISC`).

One solver run over one graph yields both. **The real loader should
discard the face-cycle output and load only the homological-cycle
output.** No `surface_type` disambiguation problem to solve — the
redundant rows should simply never be inserted.

**Consequence for `graphs.category`/`surface_type` — confirmed with
Stuart, 2026-08-11.** A cylinder dissection's underlying graph is a
perfectly ordinary 3-connected planar graph — the same `graph_id`,
`category=1`, `surface_type='plane'` row a plane dissection from that
graph would use. There's no separate "cylinder graph" population, so
`graphs.surface_type='cylinder'` is likely never actually used — the
cylinder-ness lives entirely in `dissections.d_type`.

**Consequence for `order_counts` — revised after discussion, then
implemented.** My first instinct (cylinder counts just become more keys
on the *same* `(order_val, category=1)` row plane already populates) was
wrong: `order_counts` isn't just a count cache, it's a **provenance
record** (`tool`/`tool_version`/`git_sha`/`plantri_version`/
`plantri_classes_fed` exist specifically so a partition's origin is
honestly checkable — the same mechanism that already correctly flags
CISR/CISS as partial). Plane and cylinder dissections at the same order
come from **different generation runs** (`sqt` vs. the cylinder
cycle-basis solver) even though they draw on the same graphs, so folding
them into one row would make that row's single `tool` column dishonest
about its own provenance. **Resolved: `order_counts`' primary key is now
`(order_val, category, tool)`, not `(order_val, category)`** — done
2026-08-11, live DB + `db/schema/reconciliation.sql`, 17 existing rows
preserved (all `category=1, tool='sqt'`), smoke-tested that a second row
for the same order+category under a different tool is now possible.

This also **supersedes the previous plan to evaluate `surftri` for the
cylinder track** — no generator to evaluate, cylinder Stage A doesn't
exist as a separate thing. `surftri` is now understood to matter for
**torus only** (below).

## Tori: genuinely need a new graph population (confirmed 2026-08-11)

Asked Stuart directly whether the same "works directly on existing plane
graphs" simplification extends to tori, given torus has one more
independent homological direction than cylinder (rank 2 vs. rank 1 — see
the alpha/beta 2D kernel search below). Confirmed no: **"plantri produces
graphs on the sphere... genus 0, these can produce cylinders, for other
higher graph genus like the torus we use `surftri` to generate the graphs
and like plantri can generate them exhaustively by node, edge to embed in
the surface."** So the original SPEC-7 plan for torus was right —
`surftri` with a genus parameter is a real, necessary Stage A for this
track, not an optional evaluation.

**What's actually there today.** Only **one** base graph is known to admit
a perfect torus dissection at all: a 9-vertex rotation system Gambini found
via "a packing backtracker program" (Stuart's description) — a
fundamentally different, ad-hoc search method, not graph-enumeration-then-
solve. That graph is hardcoded directly into `torus_master_solver.sage`
(`line = "bgficd,adch,..."`). Because a torus has genus 1, its cycle space
has rank 2 (vs. cylinder's rank 1) — so unlike the plane/cylinder solver,
which picks *one* battery edge (or, per the mechanism above, one homological
cycle direction) and gets a unique solution, this solver computes a full
2-dimensional integer kernel (basis vectors `v1`, `v2`) and scans **integer
linear combinations** `alpha*v1 + beta*v2` for `alpha, beta` in `[-50, 50]`
(10,201 combinations), keeping the ones that reduce to a set of distinct
positive integers. **3,077 of those combinations produced a valid perfect
solution** — that's 3,077 different numeric scalings of *one* combinatorial
graph, not 3,077 distinct dissections the way cylinder's order-13 count is.
Comparing that number directly to cylinder or plane counts would compare
different things entirely.

**So "how many squared tori exist" is currently unknown at the level that
actually matters** (distinct graphs), not just under-measured — one known
example, an unknown-but-presumably-large space of undiscovered ones, no
systematic search run yet. `surftri`'s usage line
(`[-uaAgsh -c#xm#pe#f#qy -odb -v -n] n g [res/mod] [outfile]`) takes a
genus parameter `g`; the source (`surftri.c`) shows support for genus 0
(with boundary/holes), genus 1 (torus), and beyond, backed by precomputed
irreducible-triangulation basis files already in the directory
(`genus1.alpha`, `genus1.holes`, etc.) — real, usable, unused so far.

**SPST and friends.** Per Stuart: `T` (torus) extends the existing shape
axis the same way `C` (cylinder) does — the taxonomy is (simple/compound)
× (perfect/imperfect) × (rectangle/square/cylinder/torus). Confirmed name:
**SPST** = Simple Perfect Squared Torus (the one known example is this
type), extending by direct analogy to **SIST**/**CPST**/**CIST**. Given
exactly one SPST is known and nothing about the other three, there's no
basis yet for guessing which will turn out rare vs. common.

**Space constraints, honestly.** Tori don't have a real number to design
storage against yet — one row's worth of data. The only actionable design
goal right now is not structurally blocking torus rows when they do turn
up (`d_type` already widened, `surface_type='torus'` already exists) —
not computing a budget from a sample size of one.

## Decision: magnitude-based stopping, per type (cylinder track)

Same principle as SPEC-6's CISR/CISS criterion: **not** a fixed order
target matching plane's backfill range — run each type until its per-order
count reaches roughly SPSR-order-16-18 magnitude (~9,016-110,381), then stop
generating further orders *for that type specifically*. (This section is
about the cylinder-specific `d_type`s only, i.e. `SPSC`/`SISC`/`CPSC`/
`CISC` and their trivial-compound instances — the redundant `SPSR`-named
etc. output from the same solver run is discarded per the mechanism above,
never loaded, so it has no stopping decision of its own.)

Real data (orders 7-13, all types the raw solver output produced — includes
the now-understood-to-be-discarded plane-duplicate columns for reference):

| order | SPSR* | SPSC | SISR* | SISC | SISS* | CISR* | CISS* | TCISR* | TCPSR* |
|---|---|---|---|---|---|---|---|---|---|
| 9  | 13 | 7 | 222 | 104 | — | 18 | — | 604 | — |
| 10 | 38 | 52 | 2,317 | 972 | 89 | 793 | — | 4,218 | 7 |
| 11 | 153 | 318 | 18,610 | 8,663 | 201 | 6,262 | 145 | 27,492 | 46 |
| 12 | 417 | 983 | 66,428 | 43,348 | 639 | 16,280 | 113 | 100,912 | 148 |
| 13 | 1,467 | 4,909 | 574,144 | 389,835 | 1,736 | 160,092 | 537 | 731,694 | 592 |

*= face-cycle output, redundant with the existing plane catalogue, will
not be loaded by the real pipeline — kept in this table only because it's
what's actually on disk right now, not because it's a target.

**`SISC` and `SPSC` are the only genuinely cylinder-specific columns
confirmed above** (`CPSC`/`CISC` weren't seen broken out separately in the
raw data reviewed — may be folded into the starred columns there, or may
not have appeared yet at these orders; worth checking directly against the
solver's actual output categories, not assumed from this table). Applying
the stopping rule to what's confirmed: `SISC` crosses into the target band
around order 12 (43,348) and is likely past it by order 13 (389,835) — a
very early natural stopping point, same shape of finding as the original
version of this table showed for the (misidentified) `SISR`/`CISR`/`TCISR`
columns.

**Total dissection files by order** (all types, orders 7-13): 7→67, 8→370,
9→962, 10→8,478, 11→61,881, 12→229,259, **13→1,864,997**, 9.1GB as SVG (not
the real storage format). By order 13, this raw total (before discarding
the redundant plane-duplicate rows) is already comparable to plane order
20-21's dissection volume — confirms the original "order of magnitude
larger" concern was a real understatement, even though a meaningful chunk
of that raw count turns out to not need storing at all.

## What needs to change / build

1. **Confirm the solver's actual output categories** against
   `cylinder_solver.sage`/`cylinder_solver_batch.sage` directly (read the
   code, don't infer from folder names) — need to know precisely which
   `d_type`s it can emit before writing the discard/keep filter.
2. **Build the discard/keep filter**: load only `SPSC`/`SISC`/`CPSC`/
   `CISC` (and trivial-compound instances thereof) from the cylinder
   solver's output; discard everything that duplicates the plane
   catalogue. This is now the core of "Stage C for cylinders" — there's no
   separate Stage A.
3. **Decide sage-based vs. ported-to-frozen-pipeline** for the cylinder
   solver — SPEC-1's whole design philosophy is a frozen, auditable solver
   binary; the existing sage solver works (produced the real data above)
   but porting is a real question, not an assumed yes.
4. ~~Confirm the `graphs.category`/`order_counts` inference above~~ —
   **done 2026-08-11.** `graphs.category`/`surface_type` need no change
   (cylinder dissections reuse the same plane `category=1` graphs);
   `order_counts` needed more than first thought — see above, key is now
   `(order_val, category, tool)`, implemented.
5. **Per-type stopping logic** for the cylinder track, once (1)-(2) land —
   genuinely new, not in the existing tooling: keep generating an order's
   graphs but stop loading dissections of a type that's already crossed
   its magnitude target, while continuing types that haven't.
6. **`d_type` extensibility — done 2026-08-10.** 16 values total (see
   SPEC-6 for the shared history); `is_trivial_compound` also done
   2026-08-10 as a boolean column, not more `d_type` codes.
7. **Build the `surftri`-based genus-1 Stage A for torus** — real,
   necessary work now that "works directly" is confirmed *not* to extend
   here. Needs its own `valid_vf_classes`-equivalent bound for genus-1
   graphs (not yet derived — SPEC-6's Euler-based reasoning doesn't
   directly transfer to a different genus without rework).
8. **Generalize the torus solver** away from Gambini's one hardcoded graph:
   a Stage-A-style loop over `surftri`-enumerated genus-1 graphs, each fed
   through the 2D-kernel (alpha/beta) solve `torus_master_solver.sage`
   already implements for one graph. Real research/engineering work.
9. **`ref_counts`**: not attempted for either track — no OEIS search done
   for cylinder/torus sequences. Same empirical-validation discipline as
   SPEC-6: don't guess.

## Suggested order of work

1. ~~Widen `d_type`'s `CHECK` constraint~~ / ~~add `is_trivial_compound`~~
   — both done 2026-08-10.
2. Read the cylinder solver's actual code (item 1 above) — cheap,
   unblocks the filter design, no dependencies.
3. Build the discard/keep filter (item 2 — the `category`/`order_counts`
   schema question, item 4, is now done) — this is most of what "cylinder
   Stage C" is.
4. Decide sage-based vs. ported (item 3), then build cylinder's per-type
   stopping logic (item 5).
5. Torus track — genuinely separate, not blocked on 1-4: build the
   `surftri`-based genus-1 Stage A (item 7), then generalize the alpha/
   beta solver (item 8). Only after real per-graph data exists does a
   stopping/sizing decision become possible for torus — nothing to decide
   yet.
6. `ref_counts` for both tracks (item 9), once real data exists to test
   candidate sequences against — same method that worked for SISR/SISS.

## Open items carried forward
- The solver's exact emitted `d_type` set (item 1) — read the code before
  trusting the folder-name-derived table above as complete.
- `valid_vf_classes`-equivalent bound for genus-1 (torus) graphs — not
  derived; SPEC-6's Euler-based reasoning was specific to genus 0.
- Generalizing the torus solver beyond one hardcoded graph — the actual
  blocker on ever having real torus enumeration data.
- `d_type` CHECK-constraint vs. lookup-table decision, once it's actually
  touched (unchanged from v0.1).
