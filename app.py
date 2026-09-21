import streamlit as st
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="AgroPrecision SIG & IoT", layout="wide")

st.title("🌱 AgroPrecision SIG & IoT 4.0")
st.subheader("Control Centralizado Sandia, Maíz y Soja • Optimización de Riego & NDVI")

# Estado de sesión para la electroválvula
if "valvula_abierta" not in st_state:
    st.session_state["valvula_abierta"] = False

# Métricas superiores en tiempo real / simuladas
col1, col2, col3, col4 = st.columns(4)
col1.metric("HUMEDAD SUELO", "29.8%", "-1.2%")
col2.metric("TEMP. AMBIENTE", "28.5 °C", "+0.5°C")
col3.metric("LLUVIA HOY", "15 mm")

estado_valvula = "ABIERTA 💧" if st.session_state["valvula_abierta"] else "CERRADA 🔒"
col4.metric("VALVULA RIEGO", estado_valvula)

st.divider()

# Navegación por Pestañas
tab1, tab2, tab3 = st.tabs([
    "📍 1. Mapeo y SIG (Folium)", 
    "💧 2. Clima y Decisión de Riego", 
    "🛸 3. Monitoreo Aéreo / Dron (NDVI)"
])

with tab1:
    st.markdown("### Módulo 1: Mapeo y SIG Agrícola")
    st.write("Georreferenciación parcelaria de alta resolución con infraestructura del lote.")
    
    # Coordenadas aproximadas Chacra Principal - Las Lomitas
    m = folium.Map(location=[-24.7061, -60.5931], zoom_start=15)
    
    # Polígono delimitado del lote
    folium.Polygon(
        locations=[
            [-24.7040, -60.5950],
            [-24.7040, -60.5910],
            [-24.7080, -60.5910],
            [-24.7080, -60.5950]
        ],
        color="#10b981",
        fill=True,
        fill_color="#10b981",
        fill_opacity=0.4,
        popup="Lote 1: Sandia (18.5 Ha)"
    ).add_to(m)
    
    st_folium(m, width=900, height=500)

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
                    st.experimental_rerun()
            else:
                if st.button("🔒 Cerrar Electroválvula"):
                    st.session_state["valvula_abierta"] = False
                    st.experimental_rerun()
        else:
            st.success("✅ Humedad óptima del suelo para el cultivo.")

with tab3:
    st.markdown("### Módulo 3: Monitoreo Aéreo (NDVI)")
    st.info("Inspección espectral de vigor foliar mediante análisis de imágenes por dron.")
    st.write("Análisis del lote con mapa de calor de índice vegetativo normalizado.")
