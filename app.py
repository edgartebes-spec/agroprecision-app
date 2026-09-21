import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw
import pandas as pd

st.set_page_config(page_title="AgroPrecision SIG & IoT", layout="wide")

st.title("🌱 AgroPrecision SIG & IoT 4.0")
st.subheader("Control Centralizado Sandia, Maíz y Soja • Optimización de Riego & NDVI")

# Estado de sesión para la electroválvula
if "valvula_abierta" not in st.session_state:
    st.session_state["valvula_abierta"] = False

# Métricas superiores en tiempo real
col1, col2, col3, col4 = st.columns(4)
col1.metric("HUMEDAD SUELO", "29.8%", "-1.2%")
col2.metric("TEMP. AMBIENTE", "28.5 °C", "+0.5°C")
col3.metric("LLUVIA HOY", "15 mm")

estado_valvula = "ABIERTA 💧" if st.session_state["valvula_abierta"] else "CERRADA 🔒"
col4.metric("VALVULA RIEGO", estado_valvula)

st.divider()

# Navegación por Pestañas
tab1, tab2, tab3 = st.tabs([
    "📍 1. Mapeo y SIG (Satelital + Dibujo)", 
    "💧 2. Clima y Decisión de Riego", 
    "🛸 3. Monitoreo Aéreo / Dron (NDVI)"
])

with tab1:
    st.markdown("### Módulo 1: Mapeo y SIG Agrícola Interactivo")
    st.write("Utilizá el panel de herramientas a la izquierda del mapa para **dibujar nuevos lotes, medir distancias o editar polígonos**.")
    
    # Coordenadas base (Las Lomitas, Formosa)
    lat_center, lon_center = -24.7061, -60.5931
    
    # Crear mapa base
    m = folium.Map(location=[lat_center, lon_center], zoom_start=15)
    
    # Capa 1: Esri Satellite
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri World Imagery',
        name='Satélite Esri HD',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Capa 2: OpenStreetMap (Mapa estándar)
    folium.TileLayer('openstreetmap', name='Mapa de Calles / Caminos').add_to(m)
    
    # Polígono Lote 1 - Sandia
    lote_sandia = [
        [-24.7045, -60.5960],
        [-24.7045, -60.5915],
        [-24.7075, -60.5915],
        [-24.7075, -60.5960]
    ]
    
    folium.Polygon(
        locations=lote_sandia,
        color="#10b981",
        weight=3,
        fill=True,
        fill_color="#10b981",
        fill_opacity=0.3,
        popup="Lote 1: Sandia Olimpia / Andina F1 (18.5 Ha)"
    ).add_to(m)
    
    # Marcador de Bomba / Electroválvula
    folium.Marker(
        [-24.7045, -60.5960],
        popup="Cabezal de Riego & Electroválvula #1",
        icon=folium.Icon(color="blue", icon="tint", prefix="fa")
    ).add_to(m)
    
    # Herramienta de Dibujo y Edición (Draw)
    draw = Draw(
        export=True,
        filename='lote_dibujado.geojson',
        position='topleft',
        draw_options={
            'polyline': True,
            'polygon': True,
            'circle': False,
            'rectangle': True,
            'marker': True,
            'circlemarker': False
        }
    )
    draw.add_to(m)
    
    # Selector de Capas (Esquina superior derecha)
    folium.LayerControl(position='topright').add_to(m)
    
    st_folium(m, width=950, height=530)

with tab2:
    st.markdown("### Módulo 2: Clima y Decisión de Riego")
    
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        cultivo = st.selectbox("Seleccionar Cultivo", ["Sandia (Olimpia / Andina F1)", "Maíz", "Algodón"])
        superficie = st.number_input("Superficie del Lote (Ha)", value=1.5, step=0.1)
        caudal_bomba = st.number_input("Caudal Bomba de Riego (L/h)", value=5000, step=500)
    
    with col_c2:
        humedad_simulada = st.slider("Humedad Medida (%)", 0, 100, 29)
        
        if humedad_simulada < 35:
            st.error("⚠️ Alerta de Riego: Humedad crítica por debajo del umbral óptimo.")
            
            if not st.session_state["valvula_abierta"]:
                if st.button("🔓 Abrir Electroválvula de Riego"):
                    st.session_state["valvula_abierta"] = True
                    st.rerun()
            else:
                if st.button("🔒 Cerrar Electroválvula"):
                    st.session_state["valvula_abierta"] = False
                    st.rerun()
        else:
            st.success("✅ Humedad óptima del suelo para el cultivo.")

with tab3:
    st.markdown("### Módulo 3: Monitoreo Aéreo (NDVI)")
    st.info("Inspección espectral de vigor foliar mediante análisis de imágenes tomadas por dron.")
    
    col_n1, col_n2 = st.columns([1, 1])
    
    with col_n1:
        st.markdown("#### Índice Vigor Foliar (NDVI)")
        st.write("**Promedio del Lote:** `0.74` (Saludable)")
        st.write("**Área bajo estrés:** `12%` (Sector Noreste)")
        
        # Historial de NDVI en el tiempo
        dias = pd.date_range(end=pd.Timestamp.today(), periods=8, freq='W')
        data_ndvi = pd.DataFrame({
            "Fecha": dias,
            "Índice NDVI": [0.35, 0.42, 0.55, 0.61, 0.68, 0.72, 0.71, 0.74]
        }).set_index("Fecha")
        
        st.line_chart(data_ndvi)
        
    with col_n2:
        st.markdown("#### Escala de Interpretación NDVI")
        st.markdown("""
        * 🟩 **0.60 a 0.90:** Vegetación densa y saludable.
        * 🟨 **0.30 a 0.59:** Vegetación moderada / Posible estrés hídrico.
        * 🟥 **0.00 a 0.29:** Suelo desnudo, anomalía o maleza.
        """)
        st.success("💡 **Recomendación Dron:** Aplicar refuerzo de fertirriego en las parcelas del sector este.")
