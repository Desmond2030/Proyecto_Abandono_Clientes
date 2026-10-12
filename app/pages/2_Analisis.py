# ESTADO_ARCHIVO: EN_MODIFICACION
import streamlit as st

from app.client import ErrorAPI
from app.datasets import editor_dataset
from app.results import tabla_predicciones, filas_graficos, graficos_modelos
from app.ui import asegurar_navegacion, cabecera, api_activa, dataset_activo, desde_respuesta

asegurar_navegacion("pages/2_Analisis.py")
cabecera("lotes", "02 / VISIÓN DE CARTERA", "Prioridades a escala.",
         "Carga y prepara el lote; clasifica a los clientes con el modelo 1 y estima su probabilidad de abandono con el modelo 2.")
predictor = api_activa()
editor_dataset(predictor)
st.divider()
st.subheader("Analizar el lote preparado")
options = {"subido": "Nuevo dataset preparado", "proyecto": "Dataset predispuesto del proyecto"}
default = st.session_state.get("lote_origen_activo", "subido" if st.session_state.get("dataset_preparado") else "proyecto")
source = st.selectbox("Dataset para este análisis", list(options), index=list(options).index(default),
                      format_func=options.get, key="_lote_selector")
st.session_state["lote_origen_activo"] = source
try:
    payload = dataset_activo(predictor, "prediccion", origen=source)
    frame, clients = desde_respuesta(payload)
except ErrorAPI as exc:
    st.error(str(exc))
    st.stop()
st.write(f"**{len(frame):,} clientes** · {payload['fuente']}")
if st.button("Analizar con ambos modelos", type="primary"):
    try:
        with st.spinner("Analizando clientes en la API…"):
            result = predictor.dataset_request(payload) if "entrada" in payload else predictor.predecir(clients)
        output = tabla_predicciones(payload, result)
        graficos_modelos(filas_graficos(payload, result))
        st.dataframe(output, hide_index=True, width="stretch")
        st.download_button("Descargar dataset con predicciones", output.to_csv(index=False).encode("utf-8-sig"),
                           "dataset_con_predicciones.csv", "text/csv", on_click="ignore")
        st.caption("Se conservan las filas y columnas del archivo tras las eliminaciones elegidas. Se agregan clase 0/1 del modelo 1 y probabilidad del modelo 2, sin sobrescribir columnas existentes.")
    except (ErrorAPI, ValueError) as exc:
        st.error(str(exc))
