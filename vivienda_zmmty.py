import streamlit as st
import leafmap.foliumap as leafmap
import pandas as pd
import geopandas as gpd


# Cargar geometrías
zmmty = gpd.read_file("https://raw.githubusercontent.com/claudiodanielpc/vivi_zmmty/refs/heads/main/zmmty.geojson")

colonias = gpd.read_file("https://raw.githubusercontent.com/claudiodanielpc/vivi_zmmty/refs/heads/main/colonias_zmmty.geojson")

# Cargar datos de vivienda
data = pd.read_csv("https://github.com/claudiodanielpc/vivi_zmmty/raw/refs/heads/main/scripts/vivi_renta.csv", encoding="latin1")
data = data.dropna(subset=["lat"])

# 👉 Filtro por tipo de vivienda
tipo_viviendas = data["tipo_vivi"].dropna().unique()
tipo_vivi_seleccionado = st.selectbox("Selecciona el tipo de vivienda", sorted(tipo_viviendas))

# Filtrar datos según tipo seleccionado
data_filtrada = data[data["tipo_vivi"] == tipo_vivi_seleccionado].copy()

# Convertir a GeoDataFrame
gdf_puntos = gpd.GeoDataFrame(
    data_filtrada,
    geometry=gpd.points_from_xy(data_filtrada["lon"], data_filtrada["lat"]),
    crs="EPSG:4326"
)

# Spatial join
puntos_con_colonia = gpd.sjoin(gdf_puntos, colonias, how="inner", predicate="within")

# Precio promedio por colonia
precio_prom = puntos_con_colonia.groupby("nom_colonia", as_index=False)["precio"].mean()

# Unir con geometría
colonias_filtradas = colonias.merge(precio_prom, on="nom_colonia", how="left")
colonias_filtradas["precio"] = pd.to_numeric(colonias_filtradas["precio"], errors="coerce").round(2)
colonias_filtradas = colonias_filtradas.dropna(subset=["precio"])
colonias_filtradas["precio_str"] = colonias_filtradas["precio"].apply(lambda x: f"${x:,.2f}")

# Crear GeoDataFrame con solo columnas deseadas
gdf_coloreado = colonias_filtradas[["nom_colonia", "nom_mun", "precio", "precio_str", "geometry"]].copy()
colonias_popup = colonias[["nom_colonia", "geometry"]].copy()

st.markdown("<p style='font-family: Century Gothic; font-weight: bold;font-size: 35px; text-align: center'>Información sobre vivienda vertical y horizontal en la Zona Metropolitana de Monterrey</p>", unsafe_allow_html=True)

st.markdown("<p style='font-family: Century Gothic; font-weight: bold;font-size: 20px; text-align: center'>Algunos datos generales</p>", unsafe_allow_html=True)
st.markdown("<p style='font-family: Century Gothic;font-size: 15px; text-align: justified'>La información que se presenta corresponde a 3 municipios: Monterrey, San Pedro Garza García y Guadalupe. En esta muestra, que corresponde a datos recabados de Easyaviso y de Lamudi, se han encontrado <b>{}</b> registros de vivienda en renta.".format(len(data)), unsafe_allow_html=True)
st.markdown("---")
# Crear mapa con zoom válido
m = leafmap.Map(center=[25.67, -100.31], zoom=20)

# Capa 1: Municipios de la ZMMTY
m.add_gdf(
    gdf=zmmty,
    layer_name="Municipios de la ZMMTY",
    style_kwds={
        "color": "#feb24c",
        "fillColor": "#feb24c",
        "weight": 1,
        "fillOpacity": 0
    },
    info_mode="on_click",
    shown=True  #Capa apagada
)

# Capa 2: Coropletas
m.add_data(
    gdf_coloreado,
    column="precio",
    scheme="quantiles",
    cmap="YlOrRd",
    legend_title=f"Precio promedio - {tipo_vivi_seleccionado}",
    layer_name="Precio promedio",
    legend_kwds={"fmt": "{:,.2f}"},
    tooltip_fields=["nom_colonia", "nom_mun", "precio_str"]
)

# Capa 3: Colonias
m.add_gdf(
    gdf=colonias_popup,
    layer_name="Colonias completas",
    style_kwds={"color": "blue", "weight": 1, "fillOpacity": 0},
    info_mode="on_click"
)

# Mostrar el mapa
m.to_streamlit(1000, 600)
