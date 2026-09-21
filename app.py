import streamlit as st
import geopandas as gpd
from shapely.geometry import Polygon
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw
import requests
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="AgroPrecisión SIG", layout="wide")

st.title("🌾 AgroPrecisión - Gestión Agrícola & Riego")

# --- FUNCION PARA OBTENER CLIMA EN TIEMPO REAL ---
@st.cache_data(ttl=600)
def obtener_clima_real(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&daily=precipitation_sum,temperature_2m_max,temperature_2m_min,et0_fao_evapotranspiration&timezone=America/Argentina/Buenos_Aires"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception:
        return None
    return None

# Coordenadas centro de la chacra
centro_lat = -24.781077
centro_lon = -60.462864

datos_clima = obtener_clima_real(centro_lat, centro_lon)

# --- MENÚ LATERAL (SIDEBAR) ---
st.sidebar.header("🕹️ Configuración del Lote")
cultivo = st.sidebar.selectbox("Seleccionar Cultivo:", ["Sandía (Olimpia / Andina F1)", "Maíz", "Algodón", "Hortalizas"])
caudal_bomba = st.sidebar.number_input("Caudal de la bomba (Litros/Hora):", value=5000, step=500)

humedad_suelo = st.sidebar.slider("Humedad del Suelo - Sensor (%)", 0, 100, 38)

# --- DATOS GEOGRÁFICOS BASE ---
esquinas_chacra = [
    (-60.462643, -24.781825),
    (-60.461897, -24.780997),
    (-60.462948, -24.780359),
    (-60.463667, -24.781128),
    (-60.462643, -24.781825)
]

gdf_base = gpd.GeoDataFrame({
    'nombre': ['Chacra Principal'],
    'geometry': [Polygon(esquinas_chacra)]
}, crs="EPSG:4326")

gdf_proyectado = gdf_base.to_crs(epsg=32720)
superficie_ha = (gdf_proyectado.geometry.area / 10000).round(2).iloc[0]

# --- METEOROLOGÍA EN TIEMPO REAL ---
st.subheader("🌤️ Estación Meteorológica Local")

temp_actual = 30.0
lluvia_hoy = 0.0
evapo_fao = 5.0

if datos_clima and 'current_weather' in datos_clima:
    cw = datos_clima['current_weather']
    daily = datos_clima['daily']
    temp_actual = cw['temperature']
    lluvia_hoy = daily['precipitation_sum'][0]
    evapo_fao = daily.get('et0_fao_evapotranspiration', [5.0])[0]
    
    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
    col_c1.metric("Temperatura Actual", f"{temp_actual} °C")
    col_c2.metric("Viento", f"{cw['windspeed']} km/h")
    col_c3.metric("Temp. Máx Hoy", f"{daily['temperature_2m_max'][0]} °C")
    col_c4.metric("Lluvia Prevista Hoy", f"{lluvia_hoy} mm")

st.markdown("---")

# --- MODULO DE INTELIGENCIA DE RIEGO ---
st.subheader("💧 Balance Hídrico y Calculadora de Riego")

kc_dict = {
    "Sandía (Olimpia / Andina F1)": 0.85,
    "Maíz": 1.15,
    "Algodón": 1.00,
    "Hortalizas": 0.90
}

kc_actual = kc_dict[cultivo]
nec_mm_dia = max(0.0, (evapo_fao * kc_actual) - lluvia_hoy)
litros_totales = int(nec_mm_dia * superficie_ha * 10000)
horas_riego = round(litros_totales / caudal_bomba, 1) if caudal_bomba > 0 else 0

col_r1, col_r2, col_r3 = st.columns(3)
col_r1.metric("Necesidad Hídrica Neta", f"{nec_mm_dia:.1f} mm/día")
col_r2.metric("Volumen Requerido Total", f"{litros_totales:,} Litros".replace(",", "."))
col_r3.metric("Tiempo Estimado de Bombeo", f"{horas_riego} hs")

 recomendacion = ""
if humedad_suelo < 30:
    recomendacion = f"ALERTA: Suelo seco ({humedad_suelo}%). Programar riego por {horas_riego} hs ({litros_totales} Litros)."
    st.error(f"🚨 **RECOMENDACIÓN:** {recomendacion}")
elif humedad_suelo > 65 or lluvia_hoy > 10:
    recomendacion = "No se requiere riego hoy. Humedad o lluvias acumuladas suficientes."
    st.info(f"🌧️ **RECOMENDACIÓN:** {recomendacion}")
else:
    recomendacion = "Estado hídrico equilibrado. Monitorear durante la tarde."
    st.success(f"✅ **RECOMENDACIÓN:** {recomendacion}")

st.markdown("---")

# SECCIÓN VISOR Y DESCARGA
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📊 Resumen del Campo")
    st.write(f"**Lote:** Chacra Principal")
    st.write(f"**Cultivo:** {cultivo}")
    st.write(f"**Superficie:** {superficie_ha} Ha")
    st.write(f"**Humedad Actual:** {humedad_suelo}%")
    
    st.markdown("---")
    st.subheader("📄 Generar Ficha Técnica")
    
    # Generar texto del reporte
    fecha_hoy = datetime.now().strftime("%d/%m/%Y %H:%M")
    reporte_texto = f"""==================================================
        AGROPRECISIÓN SIG - FICHA TÉCNICA DE RIEGO
==================================================
Fecha y Hora de Emisión: {fecha_hoy}
Lote / Chacra: Chacra Principal
Ubicación: Formosa, Argentina (-24.781077, -60.462864)

--------------------------------------------------
1. DATOS DEL CULTIVO Y SUPERFICIE
--------------------------------------------------
Cultivo: {cultivo}
Superficie Calibrada: {superficie_ha} Hectáreas
Humedad Medida en Suelo: {humedad_suelo}%

--------------------------------------------------
2. CONDICIONES METEOROLÓGICAS (TIEMPO REAL)
--------------------------------------------------
Temperatura Actual: {temp_actual} °C
Lluvia Prevista: {lluvia_hoy} mm
Evapotranspiración Estimada: {evapo_fao} mm/día

--------------------------------------------------
3. BALANCE HÍDRICO Y RECOMENDACIÓN DE RIEGO
--------------------------------------------------
Necesidad Hídrica Neta: {nec_mm_dia:.1f} mm/día
Volumen Requerido Total: {litros_totales} Litros
Caudal de Bomba Configurado: {caudal_bomba} L/h
Tiempo Recomendado de Riego: {horas_riego} Horas

DIAGNÓSTICO:
{recomendacion}
==================================================
"""
    st.download_button(
        label="📥 Descargar Reporte (.TXT)",
        data=reporte_texto,
        file_name=f"Reporte_Riego_{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain"
    )

with col2:
    st.subheader("🗺️ Visor Geográfico Satelital")
    
    mapa = folium.Map(location=[centro_lat, centro_lon], zoom_start=17, tiles=None)
    
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google Maps',
        name='Google Satelital',
        overlay=False,
        control=True
    ).add_to(mapa)

    folium.GeoJson(
        gdf_base,
        name="Chacra Base",
        style_function=lambda feature: {
            'fillColor': '#00ff44',
            'color': '#ffffff',
            'weight': 3,
            'fillOpacity': 0.35
        }
    ).add_to(mapa)
    
    draw = Draw(export=True, filename='nuevo_lote.geojson', position='topleft')
    draw.add_to(mapa)
    
    folium.LayerControl(position='topright').add_to(mapa)
    st_folium(mapa, width=700, height=450)
