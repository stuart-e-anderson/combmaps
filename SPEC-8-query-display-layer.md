# SPEC-8 — Query/display layer (extracting dissections for HTML/SVG)

**Version 0.1 (scoped, not yet implemented) · 2026-08-11**
**Role:** the v1 website's browse/render layer was built and works, but
predates SPEC-6/7/8's own-session additions (16 `d_type`s, `surface_type`/
`category` axes, `is_trivial_compound`) and is now visibly out of sync with
the schema. Scopes what's stale vs. what needs genuinely new work, the same
way SPEC-6/7 did — grounded in reading the actual code, not guessing.

This is deliberately **not** SPEC-5. SPEC-5 is the longer-horizon "query
API" (graphs as general object, multiple representations, deletion-
contraction lineage) — explicitly drafted, not implemented, deliberately
separate from v1. This spec is the much narrower, concrete question: what
does the *existing* Flask site need to keep working now that the schema
it queries has grown.

**Scope update, 2026-08-11 (see `SPEC-9-site-structure.md`)**: resolved
with Stuart that the site has no standalone "Search" feature — a rich
"detailed dissection selection" filter interface (order, `d_type`,
`surface_type`, `category`, exact dimensions, `is_crossed`,
`is_trivial_compound`, corner elements, etc.) *is* search for the
catalogue, not a separate thing to build alongside it. So this spec's job
is now explicitly "let someone find any dissection by any property," not
just "paginate what SPEC-1 loaded" — a real scope increase, not just a
rename. Topics/History content (SPEC-9) gets its own much smaller,
separate search mechanism; not unified with this one.

---

## What exists today (read directly, not from memory)

- **`website/db.py`** (90 lines): hand-written `psycopg` queries, no ORM,
  bypasses `squaringlib.queries` entirely (that module is still an empty
  stub — docstring only, no functions, despite existing as a directory).
  Four functions: `orders_summary()`, `dissections_for_order()` (paged,
  `d_type`-filterable), `type_counts_for_order()`, `dissection_detail()`.
- **`squaringlib/render/render_svg(elements, width, height, ...)`**
  (42 lines): one function, draws a flat bounding rectangle plus every
  placed square. Calls `squaringlib.geometry.place_elements()` for
  coordinates — skyline packing, which assumes an ordinary rectangle.
  Neither function has any concept of a surface topology.
- **Three routes** (`website/routes.py`): `/` (orders list), `/order/<n>`
  (paged grid, filterable by type — the template loops over `db.D_TYPES`
  and only renders a tab `if type_counts.get(t)`), `/dissection/<id>`
  (single view: SVG + a `<dl>` of properties).
- **Templates** (`website/templates/*.html`): straightforward Jinja2, no
  surprises — confirmed by reading them, not assumed.

## Two things that are stale right now, not hypothetically

1. **`db.D_TYPES = ["SPSR","SPSS","SISR","SISS","CPSR","CPSS","CISR","CISS"]`**
   — hardcodes exactly the original 8. `order.html`'s type-filter tabs loop
   over this list, so even once cylinder/torus rows exist, none of the 8
   new types (`SPSC`/`SISC`/`CPSC`/`CISC`/`SPST`/`SIST`/`CPST`/`CIST`) would
   ever show a filter tab — the loop simply never reaches them.
2. **`dissection_detail()`'s `SELECT` doesn't include `is_trivial_compound`**,
   and `dissection.html`'s property list doesn't display it. Added to the
   schema this session; the site can't surface it for any row, including
   existing compound ones, until this is wired through.

Both are mechanical, no design decision needed — same category as SPEC-7's
`d_type` CHECK widening was.

## The decision SPEC-7 left open, and why this is the forcing function

SPEC-7 flagged "lookup table vs. growing the `CHECK` list" for `d_type` as
open, deferred "until the taxonomy grows past these 16." It already has:
16 real values plus a still-undecided trivial-compound-as-its-own-code
question (resolved as a boolean instead, but the type count itself keeps
growing — CISR/CISS's own completeness caveat, `surftri`-based cylinder
work, real torus data once it exists, are all still ahead). The website
needs *some* authoritative list of "what types exist and are filterable"
regardless — right now that's a Python list maintained by hand, completely
decoupled from the database's own `CHECK` constraint, which is exactly the
kind of drift this project has hit before (the `order_counts`/`ref_counts`
sync problems earlier this session were the same shape of bug). Recommend:
build the small `d_types` reference table now (code, `simple`, `perfect`,
`shape`, maybe a human-readable label for display) while this exact area is
already being touched, and have `db.py` read from it instead of hardcoding
a list a second time. Not required to unblock the two stale fixes above —
those can land with a one-line list edit — but doing it now avoids a third
manual sync point once cylinder/torus rows actually start loading.

## New filter dimensions SPEC-6/7 introduce

- **`is_trivial_compound`** — straightforward addition to the existing
  query/template pattern once wired through (see stale fix #2).
- **`graphs.surface_type`** (`'plane'|'cylinder'|'torus'`) and
  **`graphs.category`** (connectivity population, per SPEC-6) — neither is
  currently joined or filterable in `dissections_for_order()` at all; every
  query today implicitly assumes plane.
- **These two are coupled to SPEC-7's still-open naming question**: the raw
  cylinder data on disk has folders literally named `SPSR`/`SISR`/`SISS`/
  `CISR`/`CISS` — the *same* codes as the plane types, not `SPSC`-style
  cylinder-distinct codes for every case. If that turns out to mean
  "this cylinder dissection also happens to be a valid plane dissection,
  reuse the plane code," then `d_type` alone is ambiguous for those rows
  and the website *must* filter/display by `surface_type` too to show the
  right thing. If it turns out those folder names were just inconsistent
  labeling and every cylinder row should really be `SPSC`/`SISC`/etc., then
  `surface_type` filtering is still useful (browsing "all cylinders") but
  not load-bearing for correctness. **This needs resolving before the
  query layer can be built correctly, not worked around** — guessing here
  risks silently mixing shapes in a filtered view.

## The real gap: rendering non-plane shapes

`render_svg()`/`place_elements()` only know how to draw a flat bounding
rectangle. Checked one of the actual cylinder SVGs already on disk
(`squared_cylinders/order_9/SPSR/g0004_...svg`) — it's rendered as a plain
rectangle, **no visual indication that the left/right edges identify into a
cylinder at all**. Whether that's an intentional simplification (the
topology is implicit, described in text rather than drawn) or a gap in the
existing exploration tooling isn't confirmed — worth asking rather than
assuming either way before deciding what the *website's* cylinder renderer
should do.

Torus is a bigger, confirmed gap: the only code that draws a torus
dissection is the ad-hoc "wrap into fundamental domain" logic inside
`torus_master_solver.sage` (draws the dashed-border fundamental domain box,
then places each square at the position — among a small search radius of
lattice-translated copies — that maximizes overlap with that box). That
logic is real and works (it's what produced `auto_torus_minimal.svg`), but
it's one-off script code tied to Gambini's single hardcoded graph, not a
reusable `squaringlib.render` function. Porting/generalizing it is real
work, not a quick add — and can't be usefully scoped further until SPEC-7's
torus-generation track produces more than one example to design against.

## `squaringlib.queries` — still an open architecture question

Still genuinely empty. Two live options, not decided here: (a) keep
`website/db.py` as the site's own query layer and leave
`squaringlib.queries` for the DuckDB/research side only (the two-layer
data architecture the README describes), accepting some duplication
between "queries for the site" and "queries for research"; or (b) have
`db.py` call into shared functions in `squaringlib.queries` so both layers
use the same logic against their respective backends. Given the site's
queries are still small (4 functions, ~90 lines) this isn't urgent, but
worth deciding before the query surface grows with `surface_type`/
`category`/`is_trivial_compound` filtering.

## Showcase handling for rare examples (SPST)

The existing browse model (order → paginated grid → detail page) assumes
"many rows per order," which is exactly wrong for something like the one
known SPST — Stuart described real public interest in squared-square-tori
specifically. A single, rare, notable example probably wants its own
curated presentation (like a dedicated page or a "notable dissections"
section) rather than being buried as one paginated grid cell among however
many SIST/CIST rows eventually turn up alongside it once real torus
generation exists. Not a technical problem, a product/UX one — flagged so
it doesn't get silently steamrolled by the generic per-order template once
torus data starts loading.

## Scale note, already true today, more visible with cylinders

`dissections_for_order()` uses `LIMIT`/`OFFSET` pagination. Plane order 21
already has 5.3M rows; cylinder order 13 alone is already 1.86M (SPEC-7).
`OFFSET`-based pagination degrades at high page numbers on tables this
size — not a new problem cylinders create, but one they make more acute at
much lower orders than plane ever did. Not blocking v1's existing scope,
worth a keyset-pagination note for whenever this gets revisited.

## What needs to change / build

1. **Add the 8 new values to `db.D_TYPES`** (or supersede it with the
   `d_types` table below) — mechanical, unblocks filter tabs for cylinder/
   torus rows once they exist.
2. **Add `is_trivial_compound` to `dissection_detail()`'s `SELECT` and
   `dissection.html`'s property list** — mechanical.
3. **Decide and build (or explicitly defer) the `d_types` reference table**
   — see "the decision SPEC-7 left open" above.
4. **Resolve the cylinder `SPSR`-vs-`SPSC` naming question** (SPEC-7's open
   item, now blocking this spec too) before building `surface_type`/
   `category` filtering — get it wrong and filtered views can silently mix
   shapes.
5. **Add `surface_type`/`category` joins and filters** to
   `dissections_for_order()` once (4) is resolved.
6. **Confirm whether the existing cylinder SVGs' lack of a wrap indicator
   is intentional** before designing the website's cylinder renderer.
7. **Port/generalize the torus wrap-into-fundamental-domain rendering**
   from `torus_master_solver.sage` into `squaringlib.render` — blocked on
   SPEC-7 producing more than one real torus example to design against.
8. **Decide `squaringlib.queries`'s role** relative to `website/db.py` —
   not urgent, worth deciding before the query surface grows further.
9. **Design a showcase/notable-dissection presentation** for rarities like
   SPST, separate from the generic per-order paginated browse.
10. **SVG safe-rendering pattern for large coordinates — confirmed in scope
    2026-08-11** (from `future_squaring.md`, a prior AI session's
    technical note): normalize/rescale actual SVG geometry into a bounded
    coordinate range (e.g. `[0, 10⁴]`–`[0, 10⁵]`), store the true exact
    integer values as `data-*` attributes, use `viewBox` for display
    scaling. Not an urgent bug fix (SVG's 64-bit floats are safe far
    beyond anything this project has hit — `ratio_cf` maxed out at 32,821
    at order 21), but cheap to bake into `render_svg()` now while it's
    still unbuilt for cylinder/torus shapes anyway, rather than retrofit
    once large-coordinate cases (surface tilings, "Fibonacci-scale dims"
    per `width`/`height`'s own column comment) actually show up.
11. **URL/redirect strategy — confirmed in scope 2026-08-11.** The old
    site has ~472 hand-built, presumably-indexed pages under paths like
    `sq/sr/spsr/o17/order17_spsr.html`. The new site's routing
    (`/order/<n>`, `/dissection/<id>`, plus whatever the site-structure
    conversation lands on for theory/history/topic content) replaces that
    scheme entirely. Needs a mapping plan (old path → new path or a
    generic "moved, here's the new catalogue" redirect) designed
    *alongside* the new URL scheme, not after it's fixed — cheap now,
    expensive later. Not scoped further here; depends on the site
    structure decision this spec's still-open items feed into.

## Suggested order of work

1. Items 1-2 (mechanical, no dependencies, unblocks nothing else but
   immediately correct).
2. Resolve the `SPSR`-vs-`SPSC` naming question (item 4) — gates items 5
   and the correctness of any cylinder filtering.
3. Decide the `d_types` table question (item 3) while touching this area.
4. Build `surface_type`/`category` filtering (item 5) once (2) is resolved.
5. Cylinder rendering (item 6) — cheap to check, may turn out to need
   nothing beyond confirming the existing plain-rectangle render is fine.
6. Torus rendering (item 7) — deliberately last, blocked on SPEC-7's
   torus-generation track producing more real examples first.
7. `squaringlib.queries` role (item 8) and showcase design (item 9) —
   lower urgency, revisit once the above is settled.

## Open items carried forward
- Whether the raw cylinder folder names (`SPSR`/`SISR`/etc., reusing plane
  codes) reflect real semantic reuse or inconsistent labeling in the
  exploration tooling — the single biggest blocker to building correct
  surface filtering.
- Whether the existing cylinder SVGs' lack of a topology indicator is
  intentional.
- `squaringlib.queries` vs. `website/db.py` duplication — not urgent, but
  will compound if left unresolved while the query surface grows.
