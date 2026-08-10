# future_squaring.md — ideas from prior AI sessions, not yet in scope

**2026-08-11.** Source: 6 PDF exports of prior AI chat sessions in
`/media/stuart/T5_EVO/squaring_net_backup/*.pdf` (412 pages total),
extracted in full by a research agent, then filtered here against the
actual current scope (`SPEC-1` through `SPEC-8`, the design doc, and the
old-site architecture map done the same session — see
`squaring-net/README.md` for all of those). Almost none of this duplicates
existing specs — the PDFs are mostly about **content, features, and
research directions** the pipeline/schema/query specs never touch, not
about the pipeline itself. Organized by theme, each idea summarized in
enough detail to judge later without re-reading the source PDFs. Items I
think are worth pulling into scope *now* are flagged inline and repeated
at the bottom — see that section first if short on time.

---

## 1. Site content sections not in any current spec

SPEC-1–8 are entirely about the dissection catalogue (pipeline → schema →
query/render). None of them account for narrative/theoretical content —
and the old-site architecture map (same session) independently found the
same gap from the other direction: `history_theory/` (bios, theory essays)
has no equivalent anywhere in the new site's scope.

- **A "theory" section, with content already drafted.** In the Tutte-formula
  PDF (260 pages, mostly deep research — see §3), Stuart explicitly told
  the model: *"I'm looking forward to doing a major upgrade of my
  squaring.net website and putting up a lot of this theoretical
  material... designing a place for these kinds of explanations."* A
  concrete 4-part structure was proposed and not rejected: Foundations
  (what's a squared rectangle, the mod-4 parity rule, a one-paragraph
  "why not all-odd") → Smith diagrams/electrical networks (Kirchhoff,
  parity reduction) → Global obstructions (the full "no all-odd" proof) →
  Historical threads (Brooks–Smith–Tutte–Stone, Duijvestijn/Skinner/Red
  Book lineage). Two pieces of content are already essentially
  publication-ready: a short "one formula, one table, one paragraph" note
  on the corrected Tutte asymptotic (with real error-term data), and the
  mod-4 parity theorem writeup (both short and long/public-friendly
  versions exist in the chat).
- **Historical/biographical narrative.** Stuart corresponded directly with
  William Tutte before his death, showed him a novel (ultimately
  non-generalizing) method for reconstructing Duijvestijn's smallest
  squared square, was connected by Tutte to Jasper Skinner, and worked
  with Skinner's inherited "Red Book" (Federico's complete hand-drawn
  historical catalogue) and Skinner's own extended dataset. This is
  personal, citable history with Stuart's explicit consent to document it
  — a natural "history" page, and the old site already has bio stubs for
  Duijvestijn, Bouwkamp, Gardner, and Stuart himself to build from.
- **⭐ Worth flagging now**, not because it needs building immediately, but
  because site IA/navigation planning (part of SPEC-8) should leave room
  for it structurally rather than being designed around "just the
  catalogue" and needing rework later.

## 2. An existing spectral-invariants dataset, disconnected from the new pipeline

The "Modular analysis patterns" PDF describes real, already-computed work
that has no connection to the SPEC-1 pipeline at all:

- **Dataset**: a CSV per squared rectangle with Width, Height, AspectRatio,
  MinBoundary, **Complexity** (spanning-tree count of the graph),
  LogComplexity, **Fiedler value** (λ₂ of the graph Laplacian —
  algebraic connectivity), **Kirchhoff index** (effective-resistance-
  related), and **spectral Gap** — computed for the *complete* order-21
  SPSR collection (4,931,307 records — matches the exact count this
  session independently verified against OEIS) with orders 22–24 "in
  progress" at the time.
- **A full Python analysis package already built and handed over**:
  correlation/distribution analysis, PCA/k-means clustering ("shape
  clusters" vs. "topology clusters"), extremal-case identification
  (max/min Fiedler, Complexity, Kirchhoff, Gap per order — directly
  useful as a way to surface "interesting" dissections), cross-order
  scaling studies, and a mod-m/toy Ramanujan-congruence search module.
- **Why this matters for the rebuild**: none of `dissections`' columns
  today capture anything spectral — only geometry (width/height/
  bouwkamp_code/corner_elements/is_crossed/boundary_square_indices). If
  Stuart wants "find the dissection with the smallest spectral gap at
  order 19" or curated "interesting specimens" as a feature, the
  computation already exists; it's a schema-and-integration question, not
  a from-scratch build.
- **⭐ Worth flagging now** as a real decision point: fold spectral
  invariants into `dissections` (new columns, computed once at load time
  the same way SPEC-4's geometry columns are), keep it as a separate
  research-only DuckDB artifact per the existing two-layer architecture,
  or leave it out of v1 entirely. Not urgent to build, but worth an
  explicit decision rather than the dataset just sitting orphaned.

## 3. Deep math research (Tutte formula PDF) — mostly not site-architecture, catalogued for reference

The 260-page file is ~90% number-theory/asymptotics research, much of it
exploratory and explicitly inconclusive. Genuinely new results worth
knowing exist:

- **A real, apparently novel theorem** (developed and proved two
  independent ways in this conversation): for a squared square of side N
  with reduced element sizes, the count of odd-sided squares O satisfies
  O ≡ N² (mod 4). Clean proof, empirically confirmed against Stuart's own
  order 21–37 census data with zero violations.
- **A rigorously reconstructed "no all-odd squared rectangle exists"
  theorem**, attributed to Arthur Stone (of the Brooks–Smith–Stone–Tutte
  group) via Jasper Skinner's book — Stuart's own memory of the argument
  was reconstructed and a real gap in an early draft was found and closed
  during the conversation. Two independent proofs exist (checkerboard-
  coloring, and a Smith-diagram/bipartite-graph argument).
- **Corrected/extended Tutte asymptotic formula** with finite-size
  correction terms, validated against real OEIS-linked census data through
  order 26, reducing error from ~3.9% (leading term only) to ~0.02–0.14%
  (corrected). Extrapolated order 27–30 count predictions exist too
  (speculative, single-digit-point-count fits).
- **A citation-chain correction** for existing OEIS entries (A002839/
  A219766): the "almost all polyhedral graphs are asymmetric" assumption
  is properly cited to Richmond & Wormald (1982), not the "Cameron"
  attribution Stuart initially recalled — a rewritten OEIS commentary
  paragraph was drafted. This is an OEIS-maintenance task, not a site
  task, but Stuart mentioned prior editor pushback on this exact point, so
  it may be worth doing independent of the redesign.
- **A speculative, self-described-as-uncertain research idea**: whether a
  c-net's Kirchhoff-matrix determinant being prime forces all its
  battery-edge-derived squared rectangles to be pairwise distinct — tied
  to critical/sandpile group structure. A long C++/plantri/nauty tooling
  effort to test this computationally was **explicitly deprioritized by
  Stuart** ("that can wait for a rainy day... not high priority") after
  repeated build/tooling frustration — noted here for completeness, not
  recommended for near-term action.
- Not recommending any of this get "brought into scope" beyond the theory
  section itself (§1) — it's real, interesting math, but it's research
  content to eventually publish, not a pipeline/architecture requirement.

## 4. Rendering/technical notes, some directly actionable

- **⭐ Worth flagging now**: the "SVG vs PostScript limits" PDF gives a
  concrete, cheap-to-adopt safe-rendering pattern for very large
  dissections — rescale/normalize actual SVG geometry into a bounded
  coordinate range (e.g. [0, 10⁴]–[0, 10⁵]), store the true exact large
  integers as `data-*` attributes for exact combinatorics, and use
  `viewBox` for display scaling. Directly relevant: this project's own
  schema already anticipates huge coordinates (`width`/`height` are
  `BIGINT` specifically because "wheel/surface tilings run Fibonacci-scale
  dims," and `ratio_cf` already hit a term of 32,821 at order 21). SVG's
  64-bit floats are safe well beyond any realistic dissection size here,
  so this isn't an urgent bug — but it's a one-paragraph addition to
  SPEC-8 (still being scoped, not yet built) that prevents a known failure
  mode for free, cheaper to bake in now than retrofit later.
- **Affine/exact-rational transformation formalization**: each square in a
  dissection can be represented as a rational similarity transform of the
  unit square (side = element/scale ∈ ℚ, position as a complex number or
  2×2+translation matrix), with optional 90°-rotation via roots of unity.
  Framed as a "canonical data structure" enabling exact non-overlap/
  adjacency/area-sum checks. Interesting, but the current `bouwkamp_code`
  bytea + `place_elements()` skyline-packing approach already achieves
  exact-integer correctness (SPEC-2's area-check audit already passed
  100% across 7.36M rows) — no evidence this representation is *needed*,
  just noted as an alternative worth knowing about if the current approach
  ever hits a real limitation.
- **Recursive "squared square of squared squares" fractal tiling**: a
  working (Stuart + Stijn van Dongen) generator (`bk2sss.cpp`) that
  replaces every square in a Bouwkamp tiling with another copy of the same
  tiling (graph substitution G → G∘G), plus a fixed-rotation-per-level
  PostScript fractal variant (bug found and fixed in this conversation —
  the rotation line was commented out). A fun, visually distinct gallery
  feature, not part of the core catalogue — no urgency, noted for later.

## 5. Adjacent, not squaring.net scope

- **"Knowledge graph as Schramm-tiled square atlas"** (112-page PDF): a
  substantial, mostly-repetitive design conversation about a *separate*
  side-project — using square-tiling math (Schramm's 1993 theorem, a
  different, node-per-square construction than the classical electrical/
  Brooks–Smith–Stone–Tutte edge-per-square one this whole project uses) as
  a knowledge-graph visualization/navigation engine, with MCL clustering,
  finite-subdivision-rule zoom, and AI-generated per-cluster summaries.
  Genuinely creative, but it's a distinct application of the underlying
  math, not squaring.net content — flagged here so it doesn't get lost,
  not recommended for any near-term action on *this* project. The most
  concrete part is a self-contained 10-point engineering gap-analysis for
  that separate prototype (data schema, MCL preprocessing, planarity
  fallback policy, etc.) — only relevant if that side-project gets picked
  up independently.

## 6. Generic launch/business planning — likely superseded

- The "Website Redesign and E-commerce Strategy" PDF is a generic,
  non-squaring.net-specific 5-phase project plan (Discovery → Design →
  Dev → Testing → Launch) recommending WordPress+WooCommerce or similar
  off-the-shelf CMS/e-commerce platforms. This doesn't match the direction
  already committed to (a custom Flask/Postgres pipeline purpose-built for
  the catalogue's scale — millions of rows, exact-integer data, packed
  storage — none of which a generic CMS handles). Not recommending
  adoption of the platform suggestions.
- **One genuinely transferable, currently-unaddressed idea**: a
  **301-redirect/URL-preservation plan**. The old site has ~472 hand-built
  HTML pages, presumably indexed and linked-to externally after years live.
  No current SPEC addresses what happens to those URLs when the new site's
  routing (`/order/<n>`, `/dissection/<id>`, etc.) replaces them entirely.
  **⭐ Worth flagging now** — not because redirects need building yet, but
  because it's much cheaper to design the new URL scheme with a mapping
  strategy in mind than to retrofit one after routes are locked in.
  Content-marketing "pillar page" framing (long-form authoritative
  articles linking to smaller related pages) is also a reasonable fit for
  the theory section in §1, if Stuart wants to think about SEO for it —
  not urgent.
- Merchandise/e-commerce itself: no evidence elsewhere that Stuart actually
  wants this — flagging as an open question rather than assuming either
  way.

---

## Summary: what's now decided (2026-08-11)

All four flagged items confirmed in scope by Stuart the same day:

1. **SVG large-coordinate safe-rendering pattern** (§4) — folded into
   SPEC-8 as item 10.
2. **URL/redirect strategy for the old site's ~472 pages** (§6) — folded
   into SPEC-8 as item 11; the actual mapping plan waits on the new site
   structure conversation.
3. **Theory/history content section** (§1) — confirmed. Stuart: *"this is
   what I want more quality content for the website."* Feeds directly into
   the site-structure conversation (see project memory / whatever doc that
   conversation produces).
4. **Spectral-invariants dataset** (§2) — confirmed in scope, **and
   generalized**: Stuart's own framing was *"there will be a number of
   topics like that one, with their own write-up"* — so this isn't a
   single dataset-integration decision, it's confirmation that the site
   needs an **extensible "research topic write-up" content pattern**,
   of which spectral invariants is the first concrete example, not a
   special case. The Tutte-asymptotic-correction note and the mod-4
   parity theorem (§3) are two more instances of the same pattern already
   sitting as drafted content. This reframes §1's "theory section" from a
   handful of fixed pages into a genuinely open-ended content type — a
   real input to the site-structure design, not just a content backlog
   item.

Everything else in this document is lower-urgency or genuinely separate
(the knowledge-graph side-project, the deep Tutte-formula research beyond
what's needed for actual topic-page content, generic e-commerce advice) —
kept here for future reference, not proposed for near-term action.
