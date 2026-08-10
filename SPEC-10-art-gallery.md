# SPEC-10 — Art/Gallery section

**Version 0.1 (scoped in a live design conversation with Stuart) · 2026-08-11**
**Role:** a new site section for Stuart's generative-art work, built on the
same catalogue data as the rest of the site but rendered/decorated
client-side rather than server-side. Distinct technical domain from
SPEC-9 (content/markdown), scoped separately.

---

## What Stuart wants

Not a static image gallery / media-served database. Two explicit
requirements from the design conversation:
1. Dissections pulled from the database, illustrated **client-side** with
   **user-controllable parameters**, using SVG + JavaScript — an
   interactive playground, not a fixed set of pre-rendered pictures.
2. **Both live and curated** — every visit can generate a fresh pattern
   from user-chosen parameters, *and* Stuart can save/feature specific
   pieces he's happy with as a curated highlights page.

## Two independent tiling sources

Both feed the same decoration engine (Truchet first, more pattern types
later — same extensible-content-type pattern as SPEC-9's Topics):

1. **Real catalogue dissections** — irregular square sizes, pulled from the
   DB via a new JSON endpoint (see Architecture below).
2. **A binary/power-of-2 square-packing construction** — regular,
   generated for any integer n, **no database involved at all**. The
   packing construction itself is Stuart's own (see attribution note
   below); it's then decorated using Carlson's Truchet edge-connection
   technique. Carlson reference:
   <https://christophercarlson.com/portfolio/multi-scale-truchet-patterns/>.

## The binary/half-ring square-packing construction

**Attribution**: per Stuart, this packing construction is his own — not
knowingly sourced from Carlson or anyone else, though he can't be certain
no one else has thought of or published it independently. Credit it to
Stuart on the site; don't attribute it to Carlson (whose page covers the
Truchet *decoration* technique below, confirmed separately).

For an integer n, write n in binary. For each `1` bit (largest to
smallest), grow a square by wrapping an L-shaped "half-ring" (two adjacent
sides, not all four — hence "half") of that power-of-2 size around the
current square, until reaching n×n.

**Verified independently, both check out exactly:**
- n=13 (binary `1101` = 8+4+1): place an 8×8 square. Growing 8→12 needs a
  half-ring of 4×4 squares along two sides — a 4×8 strip (2 squares) plus a
  4×12 strip (3 squares), 5 total. Area check: 12²−8² = 80 = 5×16 ✓.
  Growing 12→13 needs a half-ring of 1×1 squares — a 1×12 strip plus a
  1×13 strip, 25 unit squares. Area check: 13²−12² = 25 ✓.

Fetching Carlson's page directly (2026-08-11) confirmed the edge-decoration
technique below in his own words, and did not describe this packing
construction — consistent with Stuart's own account above, not a
discrepancy to resolve.

## The Truchet decoration technique (confirmed via Carlson's own page)

Fetched and quoted directly, not paraphrased from memory:
- "Successive tiles in the set are scaled by 1/2, and black and white are
  swapped at each step."
- Tiles are "assembled by adjoining along the dotted lines, letting the
  wings overlap adjacent tiles. Place smaller tiles on top of larger
  tiles."
- **The key connection-point detail, confirmed exactly matching Stuart's
  description**: "the boundaries between black and white meet the dotted
  lines at 1/3 and 2/3" of each edge — not the classic single-midpoint
  connection. This is what lets "two points in a larger tile connect with
  points in adjoining smaller tiles," enabling genuinely multi-scale
  pattern continuity rather than each scale level looking disconnected
  from its neighbors.
- The "winged tile" mechanism: tiles have "wings" extending beyond their
  own content area; when a smaller tile is placed on top of a larger one
  and their wings overlap, the colored domains emerge automatically —
  described as the trick that makes the whole multi-scale system work
  without manual per-junction color-matching logic.
- Carlson's own tooling is a **Wolfram Language package**
  (`MultiScaleTruchetPatterns.wl`) — his page gives conceptual description
  and visual examples, not public algorithm pseudocode. Reproducing this
  faithfully in JS (client-side) or Python will likely need working from
  the visual examples and Stuart's own understanding, not a drop-in port
  of existing code.

## Architecture

- **New JSON data endpoint** — not server-rendered HTML/SVG like the rest
  of SPEC-8. Returns a dissection's raw elements/coordinates so client-side
  JS can do its own rendering. Cheap addition: same underlying query as
  `dissection_detail()`, different output format (JSON instead of an
  SVG string).
- **Client-side JS**: the Truchet pattern-decoration engine operating on
  SVG, plus parameter controls (color palette, pattern type, seed/
  randomization, etc.) for the live/interactive mode. This is the
  substantial new-build part of this spec — nothing like it exists yet
  anywhere in the codebase.
- **Curated pieces**: needs a small "featured pieces" table (dissection
  reference or generated-n, chosen parameters, a title) and some way for
  Stuart to save a piece he likes. Not designed yet — genuinely open, see
  below.
- **Extensible pattern-type system**: Truchet is the first pattern, not
  the only one ("some other colouring and patterning" per Stuart) — the
  engine should be built so a second pattern type doesn't require
  reworking the data endpoint or the tiling-source abstraction.

## Open items
- The actual Truchet-decoration algorithm needs to be worked out in
  enough implementable detail to code — Carlson's page is conceptual/
  visual, not pseudocode. Likely needs iterative experimentation, not a
  one-shot port.
- Curated-piece storage and Stuart's own "save this" admin workflow — not
  designed at all yet. Given SPEC-9 deliberately avoided building any
  admin UI (markdown files + git instead), worth deciding whether curated
  art pieces follow the same philosophy (a small file/JSON list Stuart
  edits by hand) or genuinely need a DB table + save action.
- UI relationship between the two tiling sources (real dissections vs.
  the binary-packing construction) — same page with a mode switch,
  separate pages, or something else — not decided.
- Color/pattern variation rules beyond Carlson's black/white swap-per-level
  aren't specified yet for a multi-color version, if Stuart wants one.
