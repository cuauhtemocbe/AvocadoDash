"""Regression tests for src/assets/style.css against the acceptance criteria
in GitHub issues #9 (tokens/typography), #11 (filter bar), and #14
(responsive fixes). CSS custom properties are resolved against :root where
an acceptance criterion describes the *effective* value (e.g. "font-family
is Inter"), and checked as raw `var(--x)` text where the criterion
describes the literal declaration (e.g. "background-color is var(--ink)")."""

import re
from pathlib import Path

import pytest

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
    # --heading-accent === var(--pit) in light mode (issue #45 introduced
    # this token so the divider can get a dark-mode-appropriate color too).
    pattern = r"border-(left|right)\s*:\s*1px\s+solid\s+var\(--heading-accent\)"
    assert re.search(pattern, menu_and_children)
    tokens = extract_root_tokens(css)
    assert resolve_token("--heading-accent", tokens) == tokens["--pit"]


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


# --- WCAG AA contrast regression (issues #44, #45, #51) -----------------
# Relative-luminance/contrast-ratio math per the WCAG 2.1 formula. These
# guard both the light-mode pairings the #44 audit found failing 4.5:1
# and the new dark-mode token values introduced for #45, so a future
# color edit can't silently regress either theme (see
# specs/accessibility-dark-mode.md's contrast audit table).

WCAG_AA_NORMAL_TEXT_RATIO = 4.5


def _linearize_channel(channel_8bit):
    fraction = channel_8bit / 255.0
    if fraction <= 0.03928:
        return fraction / 12.92
    return ((fraction + 0.055) / 1.055) ** 2.4


def _hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def _relative_luminance(rgb):
    r, g, b = (_linearize_channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _blend_over(fg_hex, alpha, bg_hex):
    fg, bg = _hex_to_rgb(fg_hex), _hex_to_rgb(bg_hex)
    return tuple(alpha * f + (1 - alpha) * b for f, b in zip(fg, bg))


def contrast_ratio(rgb_a, rgb_b):
    lum_a, lum_b = _relative_luminance(rgb_a), _relative_luminance(rgb_b)
    lighter, darker = max(lum_a, lum_b), min(lum_a, lum_b)
    return (lighter + 0.05) / (darker + 0.05)


def extract_dark_tokens(css_text):
    """Light tokens overridden by the explicit `:root[data-theme="dark"]`
    block (same values as the prefers-color-scheme-guarded block)."""
    match = re.search(r':root\[data-theme="dark"\]\s*\{([^}]*)\}', css_text)
    assert match, ':root[data-theme="dark"] block not found in style.css'
    overrides = {
        name: value.strip()
        for name, value in re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", match.group(1))
    }
    tokens = dict(extract_root_tokens(css_text))
    tokens.update(overrides)
    return tokens


def resolve_token(name, tokens):
    """Follow a chain of `var(--x)` token references down to a literal
    color value (hex or rgba)."""
    value = tokens[name].strip()
    seen = set()
    while value.startswith("var("):
        match = re.match(r"var\((--[\w-]+)\)$", value)
        assert match, f"unresolvable var() reference: {value!r}"
        ref = match.group(1)
        assert ref not in seen, f"circular var() reference at {ref!r}"
        seen.add(ref)
        value = tokens[ref].strip()
    return value


def effective_rgb(color_value, bg_hex):
    """RGB for a literal hex or rgba(...) color, alpha-blended over
    `bg_hex` if translucent."""
    if color_value.startswith("#"):
        return _hex_to_rgb(color_value)
    match = re.match(r"rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)", color_value)
    assert match, f"unsupported color value: {color_value!r}"
    r, g, b, alpha = match.groups()
    fg_hex = f"#{int(r):02X}{int(g):02X}{int(b):02X}"
    return _blend_over(fg_hex, float(alpha), bg_hex)


@pytest.mark.parametrize("tokens_fn", [extract_root_tokens, extract_dark_tokens])
def test_summary_stat_up_color_meets_aa_contrast_on_card(tokens_fn):
    tokens = tokens_fn(read_css())
    color = resolve_token("--summary-up-color", tokens)
    bg = resolve_token("--card-bg", tokens)
    ratio = contrast_ratio(effective_rgb(color, bg), _hex_to_rgb(bg))
    assert ratio >= WCAG_AA_NORMAL_TEXT_RATIO


@pytest.mark.parametrize("tokens_fn", [extract_root_tokens, extract_dark_tokens])
def test_summary_stat_down_color_meets_aa_contrast_on_card(tokens_fn):
    tokens = tokens_fn(read_css())
    color = resolve_token("--summary-down-color", tokens)
    bg = resolve_token("--card-bg", tokens)
    ratio = contrast_ratio(effective_rgb(color, bg), _hex_to_rgb(bg))
    assert ratio >= WCAG_AA_NORMAL_TEXT_RATIO


@pytest.mark.parametrize("tokens_fn", [extract_root_tokens, extract_dark_tokens])
def test_summary_stat_value_color_meets_aa_contrast_on_card(tokens_fn):
    tokens = tokens_fn(read_css())
    color = resolve_token("--text", tokens)
    bg = resolve_token("--card-bg", tokens)
    ratio = contrast_ratio(effective_rgb(color, bg), _hex_to_rgb(bg))
    assert ratio >= WCAG_AA_NORMAL_TEXT_RATIO


@pytest.mark.parametrize("tokens_fn", [extract_root_tokens, extract_dark_tokens])
def test_download_status_color_meets_aa_contrast_on_parchment(tokens_fn):
    tokens = tokens_fn(read_css())
    rule = extract_rule(read_css(), ".download-status")
    assert declared_value(rule, "color") == "var(--text-muted)"
    color = resolve_token("--text-muted", tokens)
    bg = resolve_token("--parchment", tokens)
    ratio = contrast_ratio(effective_rgb(color, bg), _hex_to_rgb(bg))
    assert ratio >= WCAG_AA_NORMAL_TEXT_RATIO


@pytest.mark.parametrize("tokens_fn", [extract_root_tokens, extract_dark_tokens])
def test_menu_title_heading_accent_meets_aa_contrast_on_parchment(tokens_fn):
    tokens = tokens_fn(read_css())
    color = resolve_token("--heading-accent", tokens)
    bg = resolve_token("--parchment", tokens)
    ratio = contrast_ratio(effective_rgb(color, bg), _hex_to_rgb(bg))
    assert ratio >= WCAG_AA_NORMAL_TEXT_RATIO


def test_header_link_hover_color_meets_aa_contrast_on_ink():
    tokens = extract_root_tokens(read_css())
    rule = extract_rule(read_css(), ".header-link:hover")
    color = declared_value(rule, "color")
    ratio = contrast_ratio(_hex_to_rgb(color), _hex_to_rgb(tokens["--ink"]))
    assert ratio >= WCAG_AA_NORMAL_TEXT_RATIO


def test_footer_link_hover_color_meets_aa_contrast_on_ink():
    tokens = extract_root_tokens(read_css())
    rule = extract_rule(read_css(), ".footer-link:hover")
    color = declared_value(rule, "color")
    ratio = contrast_ratio(_hex_to_rgb(color), _hex_to_rgb(tokens["--ink"]))
    assert ratio >= WCAG_AA_NORMAL_TEXT_RATIO


def test_dark_mode_card_bg_is_distinct_from_dark_mode_parchment():
    """Non-text UI-component contrast (WCAG 1.4.11, 3:1) between the two
    dark-mode surfaces, so cards visually separate from the page."""
    tokens = extract_dark_tokens(read_css())
    card_bg = resolve_token("--card-bg", tokens)
    parchment = resolve_token("--parchment", tokens)
    assert card_bg != parchment
