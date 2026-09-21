import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw
import pandas as pd
import geopandas as gpd
import json

st.set_page_config(page_title="AgroPrecision SIG & IoT Pro", layout="wide")

st.title("🌱 AgroPrecision SIG & IoT 4.0")
st.subheader("Plataforma de Operaciones Agrícolas • Las Lomitas, Formosa")

# Estado de sesión
if "valvula_abierta" not in st.session_state:
    st.session_state["valvula_abierta"] = False

# Métricas operativas superiores
col1, col2, col3, col4 = st.columns(4)
col1.metric("HUMEDAD SUELO", "29.8%", "-1.2%")
col2.metric("TEMP. AMBIENTE", "28.5 °C", "+0.5°C")
col3.metric("LLUVIA HOY", "15 mm")
estado_valvula = "ABIERTA 💧" if st.session_state["valvula_abierta"] else "CERRADA 🔒"
col4.metric("VALVULA RIEGO", estado_valvula)

st.divider()

# Pestañas Principales
tab1, tab2, tab3, tab4 = st.tabs([
    "🗺️ SIG & Carga de Datos", 
    "💧 Calculadora de Riego", 
    "🛸 Analítica Dron / NDVI",
    "📊 Importar Datos de Campo (CSV/GPX)"
])

with tab1:
    st.markdown("### Módulo 1: Visor SIG y Delimitación de Campo")
    
    esquina1 = [-24.781825, -60.462643]
    esquina2 = [-24.780997, -60.461897]
    esquina3 = [-24.780359, -60.462948]
    esquina4 = [-24.781128, -60.463667]
    poligono_chacra = [esquina1, esquina2, esquina3, esquina4]
    
    lat_center = sum([p[0] for p in poligono_chacra]) / 4
    lon_center = sum([p[1] for p in poligono_chacra]) / 4
    
    m = folium.Map(location=[lat_center, lon_center], zoom_start=17)
    
    # Capa satelital
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri World Imagery',
        name='Satélite Esri HD',
        overlay=False
    ).add_to(m)
    
    folium.TileLayer('openstreetmap', name='Mapa de Calles').add_to(m)
    
    # Polígono base
    folium.Polygon(
        locations=poligono_chacra,
        color="#10b981",
        weight=3,
        fill=True,
        fill_color="#10b981",
        fill_opacity=0.3,
        popup="Chacra Principal"
    ).add_to(m)
    
    # Marcador Cabezal
    folium.Marker(
        esquina1,
        popup="Cabezal de Riego Principal",
        icon=folium.Icon(color="blue", icon="tint", prefix="fa")
    ).add_to(m)
    
    # Herramienta de Dibujo
    Draw(
        export=True,
        filename='lote_agroprecision.geojson',
        position='topleft'
    ).add_to(m)
    
    folium.LayerControl(position='topright').add_to(m)
    
    st_folium(m, width=950, height=500)

with tab2:
    st.markdown("### Módulo 2: Balance Hídrico y Tiempo de Riego")
    
    c1, c2 = st.columns(2)
    with c1:
        cultivo = st.selectbox("Variedad de Cultivo", ["Sandía (Olimpia / Andina F1)", "Maíz", "Algodón"])
        sup_ha = st.number_input("Superficie Efectiva Riego (Ha)", value=1.2, step=0.1)
        caudal = st.number_input("Caudal de Bomba (Litros / Hora)", value=6000, step=500)
        kc = st.slider("Coeficiente de Cultivo (Kc)", 0.3, 1.2, 0.85)
        
    with c2:
        eto = st.number_input("Evapotranspiración Base ETo (mm/día)", value=5.5, step=0.1)
        eficiencia = st.slider("Eficiencia del Sistema (%)", 70, 95, 85)
        
        # Cálculos de Demanda Hídrica
        etc = eto * kc # Necesidad de agua en mm/día
        volumen_m3 = (sup_ha * 10) * etc / (eficiencia / 100) # m3 requeridos
        horas_riego = (volumen_m3 * 1000) / caudal
        
        st.info(f"💧 **Necesidad Hídrica Diaria:** `{etc:.2f} mm/día`")
        st.success(f"⏱️ **Tiempo de Riego Sugerido:** `{horas_riego:.2f} Horas` (`{horas_riego*60:.0f} minutos`)")
        st.warning(f"📊 **Volumen Total Requerido:** `{volumen_m3:.1f} m³ de agua`")

with tab3:
    st.markdown("### Módulo 3: Analítica de Salud Foliar (NDVI)")
    
    col_n1, col_n2 = st.columns([1, 1])
    with col_n1:
        st.markdown("#### Registro Temporal de Vigor Foliar")
        dias = pd.date_range(end=pd.Timestamp.today(), periods=6, freq='W')
        df_ndvi = pd.DataFrame({
            "Fecha": dias,
            "Lote Sandia": [0.25, 0.40, 0.58, 0.72, 0.78, 0.81]
        }).set_index("Fecha")
        
        st.line_chart(df_ndvi)
        
    with col_n2:
        st.markdown("#### Diagnóstico Operativo")
        st.write("• **Estado Vegetativo:** Crecimiento acelerado.")
        st.write("• **Anomalías:** Sin detección de estrés hídrico generalizado.")
        st.write("• **Próxima Inspección recomendada:** 7 días.")

with tab4:
    st.markdown("### Módulo 4: Importador de Archivos de Campo")
    st.write("Subí archivos de trazabilidad exportados desde **SW Maps, QField o GPS (.csv / .geojson)**")
    
    uploaded_file = st.file_uploader("Cargar archivo de puntos o lotes", type=["csv", "geojson"])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_field = pd.read_csv(uploaded_file)
                st.write("📋 **Vista previa de registros importados:**")
                st.dataframe(df_field.head())
            else:
                data_geo = json.load(uploaded_file)
                st.success("✅ Archivo GeoJSON procesado correctamente.")
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")
