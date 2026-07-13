# translations.py
"""ES/EN string tables for the dashboard UI. Region names, the "Avocado
Analytics" brand name, and every `data.query()`/DataFrame column value stay
untranslated by design — only display text goes through this module."""

TRANSLATIONS = {
    "es": {
        "header.subtitle_by": "por ",
        "header.view_on_github": "Ver en GitHub",
        "header.description": (
            "Analiza el comportamiento de los precios del aguacate y la"
            " cantidad de aguacates vendidos en EE. UU. entre 2015 y 2018"
        ),
        "footer.created_by": "Creado por ",
        "sections.scatter_title": "Análisis de Dispersión",
        "sections.box_plot_title": "Análisis de Caja y Bigotes",
        "filters.region.label": "Región",
        "filters.region.placeholder": "Selecciona una región...",
        "filters.region.tooltip": (
            "Filtra todos los gráficos por una o más regiones de mercado de EE. UU."
        ),
        "filters.type.label": "Tipo",
        "filters.type.tooltip": (
            "Filtra por tipo de aguacate: convencional u orgánico."
        ),
        "filters.date_range.label": "Rango de Fechas",
        "filters.date_range.tooltip": (
            "Limita todos los gráficos a las ventas entre las fechas de"
            " inicio y fin seleccionadas."
        ),
        "filters.x_axis.label": "Columna del Eje X",
        "filters.x_axis.tooltip": (
            "Elige qué métrica graficar en el eje X del gráfico de dispersión."
        ),
        "filters.y_axis.label": "Columna del Eje Y",
        "filters.y_axis.tooltip": (
            "Elige qué métrica graficar en el eje Y del gráfico de dispersión."
        ),
        "filters.box_plot_column.label": "Columna a Analizar",
        "filters.box_plot_column.tooltip": (
            "Elige la distribución de qué métrica visualizar."
        ),
        "filters.box_plot_groupby.label": "Agrupar Por",
        "filters.box_plot_groupby.tooltip": (
            "Elige cómo agrupar el gráfico de caja: por tipo de aguacate, región o año."
        ),
        "download.button": "Descargar CSV",
        "download.no_data": "No hay datos para exportar.",
        "empty.select_region": "Selecciona al menos una región para ver los datos.",
        "empty.no_data_filters": (
            "No hay datos disponibles para los filtros seleccionados"
        ),
        "empty.try_adjusting": "Intenta ajustar tus filtros",
        "empty.no_data_summary": "No hay datos disponibles para esta selección.",
        "charts.price.title": "Precio Promedio de Aguacates",
        "charts.price.yaxis": "Precio (USD)",
        "charts.volume.title": "Aguacates Vendidos (Volumen)",
        "charts.scatter.vs": "vs",
        "charts.box_plot.distribution_by": "Distribución por",
        "common.date": "Fecha",
        "common.price": "Precio",
        "common.volume": "Volumen",
        "common.region": "Región",
        "common.error_prefix": "Error",
        "summary.price_change": "Cambio de Precio vs. Periodo Anterior",
        "summary.best_region": "Mejor Región (precio prom.)",
        "summary.worst_region": "Peor Región (precio prom.)",
    },
    "en": {
        "header.subtitle_by": "by ",
        "header.view_on_github": "View on GitHub",
        "header.description": (
            "Analyze the behavior of avocado prices and the number of"
            " avocados sold in the US between 2015 and 2018"
        ),
        "footer.created_by": "Created by ",
        "sections.scatter_title": "Scatter Plot Analysis",
        "sections.box_plot_title": "Box Plot Analysis",
        "filters.region.label": "Region",
        "filters.region.placeholder": "Select a region...",
        "filters.region.tooltip": (
            "Filter all charts to one or more US market regions."
        ),
        "filters.type.label": "Type",
        "filters.type.tooltip": "Filter by avocado type: conventional or organic.",
        "filters.date_range.label": "Date Range",
        "filters.date_range.tooltip": (
            "Limit all charts to sales between the selected start and end dates."
        ),
        "filters.x_axis.label": "X-Axis Column",
        "filters.x_axis.tooltip": (
            "Choose which metric to plot on the scatter chart's X axis."
        ),
        "filters.y_axis.label": "Y-Axis Column",
        "filters.y_axis.tooltip": (
            "Choose which metric to plot on the scatter chart's Y axis."
        ),
        "filters.box_plot_column.label": "Column to Analyze",
        "filters.box_plot_column.tooltip": (
            "Choose which metric's distribution to visualize."
        ),
        "filters.box_plot_groupby.label": "Group By",
        "filters.box_plot_groupby.tooltip": (
            "Choose how to group the box plot: by avocado type, region, or year."
        ),
        "download.button": "Download CSV",
        "download.no_data": "No data to export.",
        "empty.select_region": "Select at least one region to see data.",
        "empty.no_data_filters": "No data available for selected filters",
        "empty.try_adjusting": "Try adjusting your filters",
        "empty.no_data_summary": "No data available for this selection.",
        "charts.price.title": "Average Price of Avocados",
        "charts.price.yaxis": "Price (USD)",
        "charts.volume.title": "Avocados Sold (Volume)",
        "charts.scatter.vs": "vs",
        "charts.box_plot.distribution_by": "Distribution by",
        "common.date": "Date",
        "common.price": "Price",
        "common.volume": "Volume",
        "common.region": "Region",
        "common.error_prefix": "Error",
        "summary.price_change": "Price Change vs. Previous Period",
        "summary.best_region": "Best Region (avg. price)",
        "summary.worst_region": "Worst Region (avg. price)",
    },
}

# Numeric-column display names, replacing the old `col.replace("_", " ").title()`
# heuristic (which mis-rendered "AveragePrice" as "Averageprice") with an
# explicit label per column per language.
COLUMN_LABELS = {
    "es": {
        "AveragePrice": "Precio Promedio",
        "Total Volume": "Volumen Total",
        "Total Bags": "Bolsas Totales",
        "Small Bags": "Bolsas Pequeñas",
        "Large Bags": "Bolsas Grandes",
        "XLarge Bags": "Bolsas Extra Grandes",
        "year": "Año",
    },
    "en": {
        "AveragePrice": "Average Price",
        "Total Volume": "Total Volume",
        "Total Bags": "Total Bags",
        "Small Bags": "Small Bags",
        "Large Bags": "Large Bags",
        "XLarge Bags": "XLarge Bags",
        "year": "Year",
    },
}

COLUMN_TOOLTIPS = {
    "es": {
        "AveragePrice": "Precio promedio por aguacate individual (USD).",
        "Total Volume": "Número total de aguacates vendidos.",
        "Total Bags": "Total de bolsas vendidas, de todos los tamaños.",
        "Small Bags": "Bolsas vendidas en la categoría de tamaño pequeño.",
        "Large Bags": "Bolsas vendidas en la categoría de tamaño grande.",
        "XLarge Bags": ("Bolsas vendidas en la categoría de tamaño extra grande."),
        "year": "Año calendario de la venta.",
    },
    "en": {
        "AveragePrice": "Average price per single avocado (USD).",
        "Total Volume": "Total number of avocados sold.",
        "Total Bags": "Total bags sold, across all bag sizes.",
        "Small Bags": "Bags sold in the small size category.",
        "Large Bags": "Bags sold in the large size category.",
        "XLarge Bags": "Bags sold in the extra-large size category.",
        "year": "Calendar year of the sale.",
    },
}

GROUPBY_LABELS = {
    "es": {"type": "Tipo de Aguacate", "region": "Región", "year": "Año"},
    "en": {"type": "Avocado Type", "region": "Region", "year": "Year"},
}

GROUPBY_TOOLTIPS = {
    "es": {
        "type": "Una caja por tipo de aguacate (convencional vs orgánico).",
        "region": "Una caja por región de EE. UU.",
        "year": "Una caja por año calendario.",
    },
    "en": {
        "type": "One box per avocado type (conventional vs organic).",
        "region": "One box per US region.",
        "year": "One box per calendar year.",
    },
}

TYPE_LABELS = {
    "es": {"conventional": "Convencional", "organic": "Orgánico"},
    "en": {"conventional": "Conventional", "organic": "Organic"},
}


def t(key: str, lang: str) -> str:
    """Look up a translated string. Raises KeyError for an unknown key/lang."""
    return TRANSLATIONS[lang][key]


def column_label(column: str, lang: str) -> str:
    return COLUMN_LABELS[lang][column]


def column_tooltip(column: str, lang: str) -> str:
    return COLUMN_TOOLTIPS[lang][column]


def groupby_label(value: str, lang: str) -> str:
    return GROUPBY_LABELS[lang][value]


def groupby_tooltip(value: str, lang: str) -> str:
    return GROUPBY_TOOLTIPS[lang][value]


def type_label(avocado_type: str, lang: str) -> str:
    return TYPE_LABELS[lang][avocado_type]
