import pandas as pd
import geopandas as gpd

DF_SIDPOL = pd.read_csv("data/SIDPOL_DATASET.csv", encoding="utf-8")
GDF_GEO = gpd.read_file("data/peru_distrital_simple.geojson")

ANCHO = 1400
ALTO = 820

COLOR_FONDO = "#0A1628"
COLOR_UNMASK = "#ffffff"
COLOR_DORADO = "#FFD700"

FUENTE_LABEL = ("Segoe UI", 17)

ULTIMO_FILTRO_ALGORITMOS = {
    "departamento": None,
    "tipo_label": None,
    "tipo_value": "TODO",
}
