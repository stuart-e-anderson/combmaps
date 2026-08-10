# SPEC-9 — Site structure & content system

**Version 0.1 (scoped in a live design conversation with Stuart) · 2026-08-11**
**Role:** pulls together the site-structure decisions from that conversation
— what's already in `future_squaring.md` as confirmed-in-scope items, plus
what emerged from discussing them — into one place. Extends SPEC-8 (search
folds into the catalogue query layer rather than being separate) and
introduces the Topics/History content type. The Art/Gallery section that
came out of the same conversation is big enough to be its own doc —
`SPEC-10-art-gallery.md`.

---

## Sections

- **Catalogue** — `/order/<n>`, `/dissection/<id>` etc. (SPEC-1/6/7/8).
  Unchanged by this doc except that its query/filter scope now explicitly
  includes what would otherwise have been a separate "search" feature (see
  below).
- **Topics** — `/topics/<slug>`. Markdown, extensible, auto-indexed.
- **History** — `/history/<slug>`. Same mechanism as Topics; bios plus the
  Tutte/Skinner/Red Book narrative (see `future_squaring.md` §1).
- **Downloads** — bulk catalogue files for orders beyond practical live
  browsing (already anticipated in the original design doc).
- **About** — site info, credits, and **Links** (Stuart wants to keep this
  from the old site, just not necessarily as prominent top-level nav).
- **Art/Gallery** — see `SPEC-10-art-gallery.md`.

## The core administrative principle

The old site's biggest administrative failure (per the architecture review)
was a hand-maintained master navigation file (`nav.html`, 835 lines) that
had to be manually kept in sync with two *different* incompatible nav
implementations across the site. The fix, applied consistently everywhere
in the new site: **no hand-maintained master nav.**
- Catalogue nav already derives from the DB (`type_counts_for_order()`).
- Topics/History nav derives from scanning the content directory + reading
  frontmatter — never a maintained list.

## Search = catalogue query, not a separate feature

Resolved directly with Stuart: "search" and "detailed dissection
selection" are the same thing, not two features that happen to overlap.
There is no standalone "Search" section. Instead:
- **The catalogue's query/filter scope (SPEC-8) is the site's search** —
  filter/combine by order, `d_type`, `surface_type`, `category`, exact
  width/height, `is_crossed`, `is_trivial_compound`, corner elements, etc.
  This reframes SPEC-8's job from "display what got loaded" to "let
  someone find any dissection by any property" — genuinely more scope than
  SPEC-8 currently describes, not just a naming change.
- **Topics/History get their own, much smaller mechanism** — simple
  browse + lightweight keyword search, since the corpus is dozens of files
  now and plausibly hundreds over years, never millions of rows. Doesn't
  need the DB's query power; a small in-memory or basic full-text search
  over the markdown corpus is enough. Deliberately not unified with the
  catalogue's query system — different data shape, different scale, no
  benefit to forcing one mechanism.

## Content authoring: Topics & History

Decided with Stuart: **markdown files in the repo**, not a DB-backed CMS.
Reasoning: this content is Stuart writing math essays and history, already
drafted as text in prior chat sessions — a direct paste-and-commit
workflow, git-versioned and diffable, no admin UI to build. Loses easy
non-technical collaborative editing, which isn't a real requirement here.

- Likely `content/topics/*.md` and `content/history/*.md` (or one
  directory with a `type: topic|bio` frontmatter field — simpler, one
  loader either way; not decided which).
- Frontmatter: title, slug, date, short summary for index listings —
  exact schema not chosen yet.
- Rendering: markdown → the same Jinja template shell the catalogue pages
  already use.

### Data-backed topics: essay-only, not schema changes (for now)

Some topics (spectral invariants is the first concrete example) have real
per-dissection data behind them, not just prose. Decided with Stuart:
**essay-only for v1** — static tables/plots embedded in the markdown page,
no new `dissections` columns, no catalogue filtering by these values yet.
Specific instance: the spectral-invariants dataset (Fiedler value,
Kirchhoff index, complexity, spectral gap — already computed for the
complete order-21 SPSR collection, 4.9M rows, full Python analysis package
already exists per `future_squaring.md` §2) gets written up as an essay,
not integrated into the schema. Can be promoted to real columns later if
demand shows up for filtering/sorting by a specific invariant — deliberately
not committing to that now.

**This generalizes**: per Stuart, spectral invariants is "one of a number
of topics like that, with their own write-up" — Topics is an open-ended
content type, not a fixed set of pages. Known candidates already drafted
in prior sessions (`future_squaring.md` §3): the corrected Tutte asymptotic
formula (with real error-term data through order 26), the mod-4 parity
theorem (`O ≡ N² mod 4`), and the reconstructed Arthur Stone "no all-odd
squared rectangle" proof.

## Open items
- Exact markdown library / frontmatter schema — not chosen.
- One content loader with a type field, or two separate ones for
  Topics vs. History — not decided.
- URL scheme for Topics/History (`/topics/<slug>`, `/history/<slug>`
  assumed but not finalized) — feeds directly into SPEC-8 item 11's old-
  site redirect plan, should be settled before that gets built.
- Topics/History search mechanism — not designed, just scoped as "small
  and separate from the catalogue's query system."
- Links/About page's actual content and prominence — Stuart wants Links
  kept, exact placement/prominence not settled beyond "not necessarily
  top-level nav."
