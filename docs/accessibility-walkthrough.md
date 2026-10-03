# Screen-reader walkthrough: filter-to-chart flow

A manual, repeatable procedure for checking what a screen reader announces
as a user filters the data and reads the charts. It complements the
automated checks (contrast ratios in `tests/test_style.py`, no positive
`tabIndex` and `alt=""` on the header mark in `tests/test_app.py`), which
cannot judge what is actually spoken. Tracking issue: #50.

**Status: procedure written; automated accessibility-tree pass done
(2026-10-03, section 5); spoken walkthrough with a real screen reader
still pending.** Every "Result" cell below stays empty until a person runs
it with a screen reader; section 5 records what could be established
without one. The
"Code check" column was verified by reading `src/app.py` and
`src/assets/style.css` at commit `f2c0af6` (2026-10-02) and is a
hypothesis, not a finding.

## 1. Setup

Fill in one row per pass. At least one screen reader + browser pair is
required; Orca + Firefox on Linux is acceptable if neither NVDA nor
VoiceOver is available.

| Pass | Screen reader (version) | Browser (version) | OS (version) | Language | Theme | Date | Tester |
|------|-------------------------|-------------------|--------------|----------|-------|------|--------|
| 1    |                         |                   |              | ES       | light |      |        |
| 2    |                         |                   |              | EN       | light |      |        |
| 3    |                         |                   |              | ES       | dark  |      |        |
| 4    |                         |                   |              | EN       | dark  |      |        |

Passes 1 and 2 cover everything below. Passes 3 and 4 need only sections
2.1 (load) and 2.6 (toggles) plus the focus-visibility check in 2.7, since
filtering and chart logic do not depend on the theme.

Start the app with `make docker-build` (once) and `make run`, then open
<http://localhost:8050>. The UI starts in Spanish (`INITIAL_LANG = "es"`);
the `ES` / `EN` toggle switches it at runtime and is not stored in the URL.
The `theme-toggle` follows the OS preference until it is used.

Optional, not a prerequisite: run the axe DevTools browser extension first
so the walkthrough can focus on what it cannot judge. No axe-core or
Lighthouse scan exists in the repo (a browser-based scan was ruled out in
#42).

Use keyboard only (Tab, Shift+Tab, arrows, Enter, Space, Esc) with the
screen reader running. Do not use the mouse.

## 2. Procedure and expected announcements

"Expected" is the target behavior. Record what was announced in "Result"
and mark Pass / Fail. A control's accessible name should be its visible
label text (not the tooltip), followed by its role and current value.

### 2.1 Loading the page (ES and EN; light and dark)

| # | Step | Expected | Result |
|---|------|----------|--------|
| 1 | Load the page with the screen reader running | Page title is announced; document language matches the UI language (Spanish voice in ES, English voice in EN) | |
| 2 | Read the page from the top (virtual cursor / browse mode) | Order: toggles, title, subtitle/description, filters, export, summary, charts, scatter section, box-plot section, footer. Header mark is skipped (`alt=""`) | |
| 3 | Jump by headings | One level-1 heading (the page title), then level-2 headings for the scatter and box-plot sections. Note which sections have no heading | |
| 4 | Jump by landmarks | Note which landmarks exist (Dash renders none by default) | |
| 5 | Wait for the initial render | Note whether the screen reader announces that content loaded or changed, and what the `dcc.Loading` spinner announces | |

### 2.2 Region filter (multi-select)

| # | Step | Expected | Result |
|---|------|----------|--------|
| 1 | Tab to the region filter | Name "Region" (ES: the visible label), role, and the current selection ("Albany") | |
| 2 | Open it, arrow through options, select a second region | Each option is announced; selecting announces the new selection or count | |
| 3 | Type to search | The result count or the focused option is announced | |
| 4 | Remove all regions | The "select a region" empty state is reachable and announced as a change | |
| 5 | Check the option tooltips (`title` on options) | Note whether any explanatory text is announced | |

### 2.3 Type filter and date range

| # | Step | Expected | Result |
|---|------|----------|--------|
| 1 | Tab to the type filter, change organic ↔ conventional | Name, role, value; the new value is announced on change | |
| 2 | Tab to the start date field | Name says "start date" (or the visible label), with its current value | |
| 3 | Open the calendar, move by day and month, pick a date | Dates are announced in full; the picked date is announced; Esc closes and returns focus | |
| 4 | Repeat for the end date | As above | |
| 5 | Pick an end date earlier than the start date | Note what is announced; the charts show the "try adjusting" empty state | |
| 6 | After each filter change, listen | Note whether anything announces that the summary and charts updated | |

### 2.4 Scatter axes and box-plot controls

| # | Step | Expected | Result |
|---|------|----------|--------|
| 1 | Tab to the scatter X axis dropdown | Name "X axis" (visible label), role, current value | |
| 2 | Change it, then the Y axis dropdown | New value announced; the chart title changes to match | |
| 3 | Tab to the box-plot column dropdown, change it | As above | |
| 4 | Tab to the group-by dropdown, try each of type / region / year | As above; note whether the per-option description (`title`) is announced | |
| 5 | Tab to each chart | Note what is announced on focus (Plotly renders SVG with no text alternative) | |

### 2.5 Reading the summary panel

| # | Step | Expected | Result |
|---|------|----------|--------|
| 1 | Read the panel with the virtual cursor | Each card reads as label then value, in a logical order | |
| 2 | Listen to cards with `▲` / `▼` prefixes | Direction of change is conveyed in words, not only by the glyph. Note how the glyph is read (e.g. "black up-pointing triangle") | |
| 3 | Change a filter while focus is elsewhere | Note whether the panel update is announced | |

### 2.6 Language and theme toggles

| # | Step | Expected | Result |
|---|------|----------|--------|
| 1 | Tab to the theme toggle | A group name (e.g. "Theme") is announced, then each option's name. Note how `☀` / `🌙` are read | |
| 2 | Switch theme with the arrow keys | New selection announced; colors change | |
| 3 | Tab to the language toggle | A group name is announced, then "ES" / "EN" | |
| 4 | Switch ES ↔ EN | Labels, placeholders, options and chart text change; document language changes with them; note whether the change is announced | |

### 2.7 Focus visibility (all passes, dark included)

`src/assets/style.css` has no `:focus`, `:focus-visible` or `outline`
rules, so focus indication is the browser default.

| # | Step | Expected | Result |
|---|------|----------|--------|
| 1 | Tab through every control in light mode | A visible focus indicator on each control | |
| 2 | Repeat in dark mode | The indicator is still visible against the dark background | |
| 3 | Note any control where focus is invisible or lost | | |

### 2.8 Downloading data

| # | Step | Expected | Result |
|---|------|----------|--------|
| 1 | Tab to the CSV button with data selected | Name (button label), role "button"; enabled | |
| 2 | Activate it | The file download starts; note whether any confirmation is announced | |
| 3 | Clear all regions so the button is disabled | The button reads as unavailable and `download-status` explains why; note whether that text is announced or reachable | |
| 4 | Tab to the chart's modebar PNG button | It is reachable by keyboard, named, and activates with Enter or Space. Only the download button is kept (`DOWNLOAD_ONLY_MODEBAR_CONFIG`) | |
| 5 | Confirm the data-equivalent for charts | The CSV export is the text alternative to the charts; note whether a user can discover that from the charts | |

## 3. Findings

One row per suspected finding. "Code check" is what reading the code
showed on 2026-10-02; "Verdict" is set only after the walkthrough:
**Confirmed**, **Not an issue**, or **Pending**. Every confirmed finding
must end up either fixed or filed as its own issue, linked in the last
column and back on #50.

| # | Suspected finding | Code check (f2c0af6) | Verdict | Fixed / issue |
|---|-------------------|----------------------|---------|---------------|
| 1 | No page `lang`; Spanish UI with a bare `<html>` may get the wrong voice | No `lang` or `index_string` customization in `src/app.py` | **Confirmed** (tree pass): `<html lang>` absent in ES and EN, and it does not change with the toggle | Fixed: `<html lang>` starts as `es`; the `lang-sync` callback follows the toggle |
| 2 | Controls have no accessible names; labels are `div.menu-title`, not `<label for>` | No `aria-*`, `htmlFor` or `html.Label` anywhere in `src/app.py` | **Confirmed** (tree pass): see 5.2 | Fixed: each control is a `role="group"` named by its label; date inputs named via localized placeholders |
| 3 | Tooltips are hover-only and unreachable by keyboard / screen reader | `info_icon` is `html.Span("i", title=...)`; not focusable. Dropdown option `title`s likewise | **Confirmed** (tree pass): the `i` icons are not in the Tab order | Fixed: icons are focusable, named by the tooltip and show it on focus. Dropdown option `title`s are still not exposed (dcc limitation; same text as the filter tooltip) |
| 4 | Dynamic updates are silent | `summary-panel`, `download-status` and the charts are not `aria-live` regions; charts sit in `dcc.Loading` | **Confirmed** (tree pass): 0 live regions on the page | Fixed: `summary-panel` and `download-status` are `role="status"`. Charts deliberately not live (too noisy) |
| 5 | Charts have no text alternative | `dcc.Graph` figures are SVG; the CSV button and the modebar PNG button are the only alternatives | **Confirmed** (tree pass): charts expose unnamed `img`; modebar PNG button is reachable and named | Partly fixed: each chart sits in a group named by a heading; modebar button name localized. No per-chart data description; the CSV export remains the alternative |
| 6 | Toggles have no group label; emoji may be read verbosely | `theme-toggle` and `language-toggle` are bare `dcc.RadioItems` | **Confirmed** (tree pass): unnamed `listbox` groups; how `☀`/`🌙` are spoken still pending | Partly fixed: both toggles are named groups. `☀` / `🌙` labels unchanged; needs a human pass |
| 7 | Sparse heading structure | One `H1`, two `H2` (scatter, box plot); no heading for the summary or the price/volume charts | **Confirmed** (tree pass): see 5.1 | Fixed: `header` / `main` / `footer` landmarks; hidden H2s for summary and both charts; Dash's empty `<footer>` turned into a `<div>` |
| 8 | Trend glyphs read oddly or carry meaning only by symbol | `TREND_GLYPHS` prefixes `▲ ` / `▼ ` to summary values | Pending: glyph is not `aria-hidden`; needs speech to judge | |
| 9 | Focus not visible, especially in dark mode | 0 `:focus` / `outline` rules in `style.css` | **Confirmed** (tree pass): see 5.4 | Fixed: 2px `--focus-ring` outline (3:1 checked in both themes), including modebar and date inputs |
| 10 | Page `H1` stays English when the UI is Spanish | Extra, found while writing this: `html.H1(children="Avocado Analytics")` is static and `update_ui_language` has no output for it | **Not an issue** (tree pass): it is the product name; same text in ES and EN | |

## 4. After the walkthrough

1. Fill in section 1 (versions) and every "Result" cell.
2. Set each verdict in section 3; for each confirmed one, fix it or open
   an issue and link it in the last column.
3. Comment on #50 with the table of verdicts and links.
4. Re-run this walkthrough when the filter or chart layout changes
   substantially, and update the "Code check" column.

## 5. Run log: accessibility-tree pass (2026-10-03)

**What this is and is not.** Run by Claude Code, not a person with a
screen reader. Tool: Playwright driving Chromium against the production
image (`avocadodash:latest`, `python src/app.py`, port 8050), reading the
browser's accessibility tree and sending real Tab key presses. This shows
the roles, names and focus order a screen reader is *given*; it does not
show what is *spoken*. Speech-dependent cells (emoji, glyphs, announcement
of changes, virtual-cursor reading order) are still pending a human pass.
Orca is installed on the dev machine but needs a desktop session and audio.

| Pass | Tool | Browser | Language | Theme |
|------|------|---------|----------|-------|
| T1 | Playwright accessibility tree + Tab | Chromium (Playwright build) | ES (and EN for 5.5) | light |
| T2 | same | same | ES | dark |

### 5.1 Structure (2.1)
- Title: `Avocado Analytics` once loaded (`Updating...` while Dash loads).
- `<html lang>`: absent, in ES and after switching to EN.
- Headings: `H1 Avocado Analytics`, `H2 Análisis de Dispersión`,
  `H2 Análisis de Caja y Bigotes`. Summary panel and the price and volume
  charts have none; chart titles are SVG text, not headings.
- Landmarks: only the footer (`contentinfo`). No `main`, `banner` or `nav`.
- Header mark: not in the tree (`alt=""` works).

### 5.2 Names and roles (2.2 to 2.4)
- Region / type / axis / group-by dropdowns are `button`s named by their
  **current value** (`Albany`, `Orgánico`, `Precio Promedio`), not by the
  visible label (`Región`, `Tipo`, ...). The label is a plain `div`.
- Date fields are `textbox`es named `Start Date` / `End Date` in English,
  also in ES.
- Open dropdown popup is a `listbox` with no accessible name.
- Tooltip `i` icons are `generic` with the tooltip as name; they are not
  focusable, so the explanatory text is unreachable by keyboard.
- Dropdown option `title`s were not exposed as descriptions.

### 5.3 Toggles and summary (2.5, 2.6)
- Theme and language toggles are `listbox` > `option` > `radio` with no
  group name. Radio names are `☀`, `🌙`, `ES`, `EN`.
- Summary cards are plain `generic` pairs (label, value). The trend card
  reads `▲ +1.6%` (glyph not `aria-hidden`; the `+` already carries the
  direction). Empty selection replaces the panel with the message
  `Select at least one region to see data.`
- No `aria-live`, `role=status` or `role=alert` anywhere: panel, charts and
  `download-status` update silently.

### 5.4 Focus (2.7)
Tab order is: theme, language, header links, region, type, start date,
end date, CSV button, modebar PNG buttons (interleaved with the chart
sections), axis and box-plot dropdowns, footer links. The `i` icons and
the charts themselves are never focused.

| Control | Light | Dark |
|---------|-------|------|
| Dropdowns | 1px purple outline | same, on a white field: visible |
| Links, CSV button | browser default ring | visible |
| Date fields | `outline: none`; only the selected text signals focus | same |
| Modebar PNG buttons | 1px **black** outline on a light chart | black on a dark chart: **not visible** (confirmed in a screenshot) |

### 5.5 Downloads and language (2.6, 2.8)
- CSV button: native `button`; with no region it is `disabled` and
  `download-status` shows `Select at least one region to see data.` as a
  plain `div` (not announced, not tied to the button).
- Switching to EN changes labels, options and `H2`s, but not `<html lang>`,
  the date field names, or the modebar label (`Download plot as a PNG` in
  both languages).

### 5.6 Still needs a person with a screen reader
2.1 steps 1, 2, 5; 2.2 steps 2 to 4; 2.3 steps 2 to 6; 2.5 steps 2, 3;
2.6 steps 1 to 4; 2.8 steps 2, 3, 5; and the speech side of findings 6 and 8.

## 6. Fixes applied (2026-10-03)

Verified with the same tree + Tab pass as section 5 (ES and EN, light and
dark) and `make validate` green (268 tests, 98.5 % coverage). Still **not**
verified by ear: re-run sections 2.1 to 2.8 with a screen reader and
update the "Result" cells.

- `src/app.py`: `lang` on `<html>` plus the `lang-sync` clientside
  callback; `aria()` helper; `control_group` / `toggle_group`; focusable,
  named `info_icon`; `header` / `main` / `footer`; `role="status"` on the
  summary and download status; hidden headings; chart groups; localized
  date placeholders and modebar button name.
- `src/assets/style.css`: `--focus-ring` / `--focus-ring-on-ink` tokens and
  `:focus-visible` rules (with `!important` overrides for dcc and Plotly),
  `.visually-hidden`, tooltip on icon focus.
- `src/translations.py`: `a11y.*` keys (ES and EN).
- Tests: `tests/test_app.py` (structure and names), `tests/test_style.py`
  (focus ring contrast in both themes, override rules),
  `tests/test_translations.py`. The #44 tab-order guard now forbids only
  non-zero `tabIndex`.
- Not covered by automated tests: the `lang-sync` JavaScript (the project
  has no browser test tooling, see #42); checked by hand with Playwright.
