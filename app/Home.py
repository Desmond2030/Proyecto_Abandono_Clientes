# ESTADO_ARCHIVO: EN_MODIFICACION
"""Punto de entrada: ejecutar streamlit run app/Home.py desde la raíz."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import streamlit as st

st.set_page_config(page_title="Telco | Retención", page_icon="◈", layout="wide")
pages = [
    st.Page("pages/0_Inicio.py", title="Inicio y modelos", icon=":material/tune:", default=True),
    st.Page("pages/1_Prediccion.py", title="Predicción individual", icon=":material/person_search:"),
    st.Page("pages/2_Analisis.py", title="Análisis de lotes", icon=":material/table_chart:"),
    st.Page("pages/3_Metricas.py", title="Métricas", icon=":material/monitoring:"),
    st.Page("pages/4_Visualizaciones.py", title="Exploración de datos", icon=":material/bar_chart:"),
]
with st.sidebar:
    st.markdown("## ◈ TELCO\nInteligencia para la retención")
    st.caption("BD-151 · IA Aplicada · Proyecto académico")
page = st.navigation(pages)
st.session_state["_navegacion_iniciada"] = True
destination = st.session_state.pop("_destino_inicial", None)
if destination:
    st.switch_page(destination)
with st.sidebar:
    st.divider()
    from app.client import ApiClient, ErrorAPI
    try:
        health = ApiClient().salud()
        st.success("API conectada")
        if health["modelos_cargados"]:
            st.caption("Dos modelos cargados en el servidor")
        else:
            st.caption("Selecciona los modelos en Inicio")
    except ErrorAPI:
        st.error("API sin conexión")
    st.caption("Explora los datos, compara estimaciones y evalúa con un conjunto identificado.")
page.run()
