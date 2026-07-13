import pytest

from translations import (
    COLUMN_LABELS,
    COLUMN_TOOLTIPS,
    GROUPBY_LABELS,
    GROUPBY_TOOLTIPS,
    TRANSLATIONS,
    TYPE_LABELS,
    column_label,
    column_tooltip,
    groupby_label,
    groupby_tooltip,
    t,
    type_label,
)

NESTED_DICTS = {
    "TRANSLATIONS": TRANSLATIONS,
    "COLUMN_LABELS": COLUMN_LABELS,
    "COLUMN_TOOLTIPS": COLUMN_TOOLTIPS,
    "GROUPBY_LABELS": GROUPBY_LABELS,
    "GROUPBY_TOOLTIPS": GROUPBY_TOOLTIPS,
    "TYPE_LABELS": TYPE_LABELS,
}


@pytest.mark.parametrize("name,mapping", NESTED_DICTS.items())
def test_es_and_en_have_identical_key_sets(name, mapping):
    assert set(mapping["es"].keys()) == set(mapping["en"].keys()), name


@pytest.mark.parametrize("name,mapping", NESTED_DICTS.items())
def test_no_empty_translation_values(name, mapping):
    for lang, entries in mapping.items():
        for key, value in entries.items():
            assert isinstance(value, str) and value.strip(), (name, lang, key)


def test_t_looks_up_correct_language():
    assert t("download.button", "es") == "Descargar CSV"
    assert t("download.button", "en") == "Download CSV"


def test_t_raises_for_unknown_key():
    with pytest.raises(KeyError):
        t("not.a.real.key", "en")


def test_t_raises_for_unknown_language():
    with pytest.raises(KeyError):
        t("download.button", "fr")


def test_column_label_fixes_averageprice_display_quirk():
    # Historically `.title()` on "AveragePrice" rendered as "Averageprice".
    assert column_label("AveragePrice", "en") == "Average Price"
    assert column_label("AveragePrice", "es") == "Precio Promedio"


def test_column_tooltip_returns_nonempty_strings():
    assert column_tooltip("Total Volume", "en")
    assert column_tooltip("Total Volume", "es")


def test_groupby_label_and_tooltip():
    assert groupby_label("type", "en") == "Avocado Type"
    assert groupby_label("type", "es") == "Tipo de Aguacate"
    assert groupby_tooltip("region", "en")
    assert groupby_tooltip("region", "es")


def test_type_label_matches_existing_title_case_convention_for_english():
    assert type_label("conventional", "en") == "Conventional"
    assert type_label("organic", "en") == "Organic"
    assert type_label("conventional", "es") == "Convencional"
    assert type_label("organic", "es") == "Orgánico"
