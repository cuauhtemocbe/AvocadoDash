"""Regression tests for src/assets/style.css against the acceptance criteria
in GitHub issues #9 (tokens/typography), #11 (filter bar), and #14
(responsive fixes). CSS custom properties are resolved against :root where
an acceptance criterion describes the *effective* value (e.g. "font-family
is Inter"), and checked as raw `var(--x)` text where the criterion
describes the literal declaration (e.g. "background-color is var(--ink)")."""

import re
from pathlib import Path

STYLE_PATH = Path(__file__).resolve().parent.parent / "src" / "assets" / "style.css"


def read_css():
    return STYLE_PATH.read_text()


def extract_root_tokens(css_text):
    """Map every `--token: value;` declared inside the first :root block."""
    root_match = re.search(r":root\s*\{([^}]*)\}", css_text)
    assert root_match, ":root block not found in style.css"
    return {
        name: value.strip()
        for name, value in re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", root_match.group(1))
    }


def extract_rule(css_text, selector):
    """First `selector { ... }` block's body (assumes no nested braces)."""
    pattern = re.escape(selector) + r"\s*\{([^}]*)\}"
    match = re.search(pattern, css_text)
    assert match, f"{selector!r} rule not found in style.css"
    return match.group(1)


def declared_value(rule_body, property_name):
    match = re.search(rf"{re.escape(property_name)}\s*:\s*([^;]+);", rule_body)
    assert match, f"{property_name!r} not declared in rule"
    return match.group(1).strip()


def resolve(value, tokens):
    """Resolve a single top-level var(--x) reference against `tokens`."""
    match = re.match(r"var\((--[\w-]+)\)$", value.strip())
    if match:
        return tokens[match.group(1)]
    return value


def test_root_color_tokens_defined():
    tokens = extract_root_tokens(read_css())
    assert tokens["--ink"] == "#1F1710"
    assert tokens["--parchment"] == "#F6F1E4"
    assert tokens["--flesh"] == "#7C8F3E"
    assert tokens["--pit"] == "#8B5A2B"
    assert tokens["--bruise"] == "#B4432E"
    assert tokens["--cream-text"] == "#EDE6D6"


def test_body_font_family_uses_inter_with_sans_serif_fallback():
    css = read_css()
    tokens = extract_root_tokens(css)
    body_rule = extract_rule(css, "body")
    resolved = resolve(declared_value(body_rule, "font-family"), tokens)
    assert "Inter" in resolved
    assert "sans-serif" in resolved


def test_header_title_uses_the_display_typeface():
    css = read_css()
    tokens = extract_root_tokens(css)
    header_title_rule = extract_rule(css, ".header-title")
    resolved = resolve(declared_value(header_title_rule, "font-family"), tokens)
    assert "Fraunces" in resolved


def test_header_uses_ink_background_token():
    header_rule = extract_rule(read_css(), ".header")
    assert declared_value(header_rule, "background-color") == "var(--ink)"


def test_menu_uses_parchment_background_token():
    menu_rule = extract_rule(read_css(), ".menu")
    assert declared_value(menu_rule, "background-color") == "var(--parchment)"


def test_menu_has_no_box_shadow():
    menu_rule = extract_rule(read_css(), ".menu")
    assert "box-shadow" not in menu_rule


def test_menu_filter_groups_have_a_pit_hairline_divider():
    css = read_css()
    menu_block_start = css.index(".menu")
    # Search the .menu rule and its immediately-following child selectors.
    menu_and_children = css[menu_block_start : menu_block_start + 600]
    pattern = r"border-(left|right)\s*:\s*1px\s+solid\s+var\(--pit\)"
    assert re.search(pattern, menu_and_children)


def test_menu_width_is_fluid_not_fixed():
    menu_rule = extract_rule(read_css(), ".menu")
    width = declared_value(menu_rule, "width")
    assert width == "100%"
    assert "px" not in width


def test_select_control_width_is_not_fixed():
    select_rule = extract_rule(read_css(), ".Select-control")
    width = declared_value(select_rule, "width")
    assert "px" not in width


def test_menu_stacks_vertically_below_768px():
    css = read_css()
    media_match = re.search(
        r"@media\s*\(max-width:\s*768px\)\s*\{(.*)\}\s*\}", css, re.DOTALL
    )
    assert media_match, "no @media (max-width: 768px) rule found"
    media_body = media_match.group(1)
    menu_rule_in_media = extract_rule(".menu" + media_body, ".menu")
    assert declared_value(menu_rule_in_media, "flex-direction") == "column"


def test_summary_stat_value_uses_mono_font_with_fallback():
    css = read_css()
    tokens = extract_root_tokens(css)
    rule = extract_rule(css, ".summary-stat-value")
    resolved = resolve(declared_value(rule, "font-family"), tokens)
    assert "IBM Plex Mono" in resolved
    assert "monospace" in resolved
