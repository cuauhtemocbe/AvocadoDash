# Screen-reader walkthrough: filter-to-chart flow

A manual, repeatable procedure for checking what a screen reader announces
as a user filters the data and reads the charts. It complements the
automated checks (contrast ratios in `tests/test_style.py`, no positive
`tabIndex` and `alt=""` on the header mark in `tests/test_app.py`), which
cannot judge what is actually spoken. Tracking issue: #50.

**Status: procedure written; walkthrough not yet run.** Every "Result"
cell below is empty until a person runs it with a screen reader. The
"Code check" column was verified by reading `src/app.py` and
`src/assets/style.css` at commit `7d3c719` (2026-10-02) and is a
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

| # | Suspected finding | Code check (7d3c719) | Verdict | Fixed / issue |
|---|-------------------|----------------------|---------|---------------|
| 1 | No page `lang`; Spanish UI with a bare `<html>` may get the wrong voice | No `lang` or `index_string` customization in `src/app.py` | Pending | |
| 2 | Controls have no accessible names; labels are `div.menu-title`, not `<label for>` | No `aria-*`, `htmlFor` or `html.Label` anywhere in `src/app.py` | Pending | |
| 3 | Tooltips are hover-only and unreachable by keyboard / screen reader | `info_icon` is `html.Span("i", title=...)`; not focusable. Dropdown option `title`s likewise | Pending | |
| 4 | Dynamic updates are silent | `summary-panel`, `download-status` and the charts are not `aria-live` regions; charts sit in `dcc.Loading` | Pending | |
| 5 | Charts have no text alternative | `dcc.Graph` figures are SVG; the CSV button and the modebar PNG button are the only alternatives | Pending | |
| 6 | Toggles have no group label; emoji may be read verbosely | `theme-toggle` and `language-toggle` are bare `dcc.RadioItems` | Pending | |
| 7 | Sparse heading structure | One `H1`, two `H2` (scatter, box plot); no heading for the summary or the price/volume charts | Pending | |
| 8 | Trend glyphs read oddly or carry meaning only by symbol | `TREND_GLYPHS` prefixes `▲ ` / `▼ ` to summary values | Pending | |
| 9 | Focus not visible, especially in dark mode | 0 `:focus` / `outline` rules in `style.css` | Pending | |
| 10 | Page `H1` stays English when the UI is Spanish | Extra, found while writing this: `html.H1(children="Avocado Analytics")` is static and `update_ui_language` has no output for it | Pending | |

## 4. After the walkthrough

1. Fill in section 1 (versions) and every "Result" cell.
2. Set each verdict in section 3; for each confirmed one, fix it or open
   an issue and link it in the last column.
3. Comment on #50 with the table of verdicts and links.
4. Re-run this walkthrough when the filter or chart layout changes
   substantially, and update the "Code check" column.
