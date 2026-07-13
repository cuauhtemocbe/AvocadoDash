---
title: Dashboard Visual Identity Redesign
status: in-progress
created: 2026-07-12
updated: 2026-07-12
issue: "#9, #10, #11, #12, #13, #14"
---

# Dashboard Visual Identity Redesign

## Objective

Replace AvocadoDash's current stock-template look with a visual identity
grounded in the actual subject — the Hass avocado itself and the produce/
crop-report market it's traded in — so the dashboard reads as a deliberate
piece of design rather than a generic Dash tutorial skin, while changing
zero filtering/business logic.

## Context

Design review of `src/app.py` + `src/assets/style.css` (2026-07-12) found
the current look is the stock Dash "avocado analytics" tutorial template,
effectively unmodified since the project's origin, even though the app has
since grown real functionality (bilingual UI, multi-region comparison,
summary KPIs, CSV export):

- Near-black header (`#222222`) + a single teal accent (`#17B897`/
  `#079A82`) — a recognizable AI-dashboard/template default, not a choice
  made for this subject.
- Body font is Lato only — no display/body pairing, no typographic
  personality.
- Cards are plain white boxes with a generic drop shadow
  (`0 4px 6px rgba(0,0,0,.18)` reused everywhere — header menu, charts,
  summary stats, empty states).
- The only "brand" mark is a 🥑 emoji in the header — placeholder-grade,
  not a designed signature.
- Chart chrome (gridlines, backgrounds, box-plot colors `#17B897`/
  `#E12D39`) is Plotly's stock light theme, disconnected from the app's own
  palette.
- Fixed-pixel widths (`.menu { width: 912px }`, `.Select-control { width:
  256px }`, `.wrapper { max-width: 1024px }`) mean the layout has no real
  mobile story.
- Price-change up/down is color-only (green/red) with no secondary
  (shape/glyph) signal — a color-blindness accessibility gap.

None of this is broken — the app works and every prior US shipped
correctly — but the visual layer has never been treated as a design
decision. This spec defines a distinctive identity and breaks it into
shippable user stories.

## Design Plan

### Color

The current cream/dark-neutral-plus-single-accent options were rejected as
too close to generic AI-dashboard defaults (warm cream + serif + terracotta;
near-black + one neon accent). Instead the palette is read directly off a
real Hass avocado cross-section — pebbled near-black skin, brown pit, olive
flesh — plus a "bruise" red already implied by the existing (and worth
keeping) red/green up-down convention:

| Token | Hex | Use |
|---|---|---|
| `--ink` | `#1F1710` | Page/header background (warm pit-skin near-black, not neutral `#000`) |
| `--parchment` | `#F6F1E4` | Content-area background (kraft/crate-paper, used sparingly behind cards only) |
| `--flesh` | `#7C8F3E` | Primary accent — links, positive trend, primary data series |
| `--pit` | `#8B5A2B` | Secondary accent — dividers, secondary marks, hover states |
| `--bruise` | `#B4432E` | Negative trend / alerts (muted brick, not stock red) |
| `--cream-text` | `#EDE6D6` | Text on `--ink` backgrounds |

### Type

- **Display** — `Fraunces` (variable serif, warm/high-contrast, distinct
  optical sizes), used only for `H1`/`H2` — the brand title and the two
  section headers. Used sparingly, large, so it stays a display face, not
  body text.
- **Body** — `Inter`, replaces Lato for all UI copy, labels, tooltips,
  filters — a clean, highly legible grotesk that doesn't compete with
  Fraunces.
- **Data/utility** — `IBM Plex Mono`, tabular numerals, used for every
  displayed number: summary-panel KPI values, price/volume figures. Ties
  the dashboard's numbers to a market-ticker/crop-report register and
  makes figures easier to compare at a glance (fixed-width digits).

### Layout

Current: a white "pill" menu card floats over the dark header via a
negative margin — a recognizable Dash-tutorial trick.

New: a **crop-report ledger** — the filter bar becomes a full-width band
on `--parchment` with hairline (`1px solid --pit` at low opacity) dividers
between filter groups instead of a box-shadowed floating card. Chart/
summary cards drop the generic drop-shadow for a thin kraft-colored
border, echoing a produce crate label rather than a Bootstrap panel.

```
┌────────────────────────────────────────┐  --ink
│  [mark]  Avocado Analytics    ES | EN   │
│          subtitle / description         │
└────────────────────────────────────────┘
┌── Region ──┆── Type ──┆── Date Range ──┐  --parchment, hairline dividers
└────────────────────────────────────────┘
┌─ $2.14 ┆ 12.4M ┆ ▲ 3.2% ┆ Best: X ┆ Worst: Y ─┐  mono numerals, ticket row
└────────────────────────────────────────┘
┌──────────────┐  ┌──────────────┐
│  price chart │  │ volume chart │   kraft-bordered cards
└──────────────┘  └──────────────┘
```

### Signature element

**The Cross-Section Mark** — a small radial SVG motif (concentric rings in
`--ink` / `--flesh` / `--pit`, echoing the avocado's actual skin/flesh/pit
layering) replaces the 🥑 emoji in the header. The same mark, in outline
form, becomes the loading-state motif shown while charts refresh. This is
the one deliberately memorable element; everything else stays quiet and
disciplined around it.

### Self-critique (per design process)

- Rejected: warm-cream-bg + serif + terracotta (too close to the
  generic-AI cluster #1 look) → resolved by pushing the background to
  `--ink` (dark, warm-black) with parchment reserved for content bands
  only, and by deriving every hex from the literal avocado cross-section
  rather than a trend palette.
- Rejected: keeping the stock teal/red pair — it's the app's current
  accent, but it's also Bootstrap/Material's default success/danger pair
  with the serial numbers filed off. Replaced with the olive/brick pair
  above, still colorblind-distinguishable, but sourced from the fruit.
- Considered numbered step markers (01/02/03) for the filter bar — rejected:
  filters aren't a sequence, so numbering would decorate rather than
  inform. Hairline dividers instead, which describe grouping without
  implying order.

## Requirements

### Functional Requirements

- [ ] Global color tokens (`--ink`, `--parchment`, `--flesh`, `--pit`,
      `--bruise`, `--cream-text`) defined once in `style.css` and used
      everywhere the current hard-coded hex values appear.
- [ ] Fraunces (display) + Inter (body) + IBM Plex Mono (data) loaded and
      applied per the Type section above, replacing Lato.
- [ ] Header redesigned on `--ink` with the Cross-Section Mark replacing
      the 🥑 emoji.
- [ ] Filter bar redesigned as a full-width `--parchment` band with
      hairline dividers, replacing the floating white pill + box-shadow.
- [ ] Chart chrome (`plot_bgcolor`, `paper_bgcolor`, `gridcolor`, box-plot
      `color_map`, region line palette) updated to the new token colors.
- [ ] Summary panel KPI values render in the mono face; price-change
      trend shows a ▲/▼ glyph in addition to color (accessibility fix).
- [ ] Fixed pixel widths in `style.css` (`.menu`, `.Select-control`,
      `.wrapper`) replaced with fluid/relative sizing so the layout
      doesn't overflow below ~768px.

### Non-Functional Requirements

- [ ] No change to any `data.query()` expression, DataFrame column access,
      or callback filtering logic — this is a display-only change.
- [ ] No new Python runtime dependency (fonts load via
      `external_stylesheets`/Google Fonts, same mechanism as the existing
      Lato link).
- [ ] `make lint` / `make format-check` stay clean.

## Boundaries & Constraints

### In Scope

- Color tokens, typography, header/filter-bar/card layout, chart chrome
  colors, summary-panel styling, the Cross-Section Mark, and the
  responsive fixed-width fixes listed above.

### Out of Scope

- Any new chart type, filter, or data capability (pure restyle).
- Dark/light theme toggle (the new palette is fixed, not user-switchable).
- Persisting user preferences.
- Redesigning the ES/EN toggle's interaction model (only its visual
  styling changes).

### Technical Constraints

- Must not add new Python dependencies to `pyproject.toml`.
- Must pass `make lint` / `make format-check`.
- Chart builder functions must keep returning plain dict figures (see
  CLAUDE.md architecture note) — only the color/font *values* inside those
  dicts change.

## Success Criteria

- [ ] All Functional Requirements implemented.
- [ ] `make lint` and `make format-check` are clean.
- [ ] No existing test regresses.
- [ ] Broken into GitHub issues (see `/user-stories`), each independently
      shippable.

## Implementation Plan

Broken into per-area user stories rather than a single plan file:

- [#9](https://github.com/cuauhtemocbe/AvocadoDash/issues/9) — Establish
  avocado-derived color tokens and typography system (do first — the rest
  depend on these tokens)
- [#10](https://github.com/cuauhtemocbe/AvocadoDash/issues/10) — Redesign
  header with the Cross-Section Mark signature
- [#11](https://github.com/cuauhtemocbe/AvocadoDash/issues/11) — Redesign
  filter bar as a full-width ledger band
- [#12](https://github.com/cuauhtemocbe/AvocadoDash/issues/12) — Recolor
  chart chrome to match the new design tokens
- [#13](https://github.com/cuauhtemocbe/AvocadoDash/issues/13) — Restyle
  summary panel with mono numerals and trend glyphs
- [#14](https://github.com/cuauhtemocbe/AvocadoDash/issues/14) — Fix
  fixed-width CSS breaking the layout on narrow viewports (independent of
  the others)
