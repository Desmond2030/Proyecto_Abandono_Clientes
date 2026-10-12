# ESTADO_ARCHIVO: EN_MODIFICACION
import pandas as pd
import streamlit as st

from app.client import ErrorAPI
from app.results import graficos_modelos, matriz_interactiva, archivo_metricas
from app.ui import asegurar_navegacion, api_activa, cabecera, desde_respuesta, dataset_activo, plantilla

asegurar_navegacion("pages/3_Metricas.py")
cabecera("metricas", "03 / EVIDENCIA DEL MODELO", "El rendimiento necesita contexto.",
         "Evalúa la clasificación del modelo 1 y las probabilidades del modelo 2 con las medidas utilizadas en las clases del proyecto.")
predictor = api_activa()
st.download_button("Descargar plantilla de cliente individual", plantilla(), "plantilla_cliente.csv", "text/csv", on_click="ignore")
options = {"proyecto": "Ejemplos reservados del notebook", "subido": "Dataset nuevo cargado en Lotes"}
default = st.session_state.get("metricas_origen_activo", st.session_state.get("origen_datos_activo", "proyecto"))
source = st.radio("Conjunto de evaluación", list(options), index=list(options).index(default),
                  format_func=options.get, key="_metricas_origen", horizontal=True)
st.session_state["metricas_origen_activo"] = source
try:
    payload = dataset_activo(predictor, "evaluacion", origen=source)
    frame, clients = desde_respuesta(payload)
except ErrorAPI as exc:
    st.error(str(exc))
    st.stop()
name = payload["fuente"]
if source == "proyecto":
    st.warning("El entrenamiento actual utiliza X_test como validación. Sus resultados no constituyen una evaluación final independiente. El subconjunto de 23 ejemplos sirve para demostración.")
    name += " · demostración, no prueba final"
st.caption(f"{name} · {len(frame)} registros · umbral {predictor.config.umbral:.2%}")
if st.button("Calcular métricas", type="primary"):
    try:
        with st.spinner("Calculando métricas en la API…"):
            result = (predictor.dataset_request(payload, evaluar=True) if "entrada" in payload
                      else predictor.evaluar(clients, frame.Abandono.astype(int).tolist(), name))
        summary = pd.DataFrame(result["metricas"])
        summary["Umbral"] = summary["Umbral"].map(lambda value: f"{value:.2%}")
        st.dataframe(summary, hide_index=True, width="stretch")
        st.caption("MAE y RMSE: clase 0/1 para el modelo 1; probabilidad para el modelo 2, comparada con la etiqueta observada. MAE/media y MAE/mediana son razones; si el denominador es cero se muestran vacías. No son porcentajes de accuracy.")
        for col, slot in zip(st.columns(2), ("modelo_1", "modelo_2")):
            with col:
                st.subheader("Modelo 1 · clasificación" if slot == "modelo_1" else "Modelo 2 · clasificación auxiliar")
                if slot == "modelo_2":
                    st.caption(f"Solo para reporte y matriz: probabilidad ≥ {predictor.config.umbral:.2%}. La salida principal sigue siendo la probabilidad.")
                matriz_interactiva(result["matrices"][slot])
                report = {key: value for key, value in result["reportes"][slot].items() if isinstance(value, dict)}
                st.dataframe(pd.DataFrame(report).T, width="stretch")
        rows = result["clientes"]
        for row, position in zip(rows, payload.get("filas_origen", range(1, len(rows) + 1))):
            row["fila"] = position
        graficos_modelos(rows)
        st.caption("Las métricas de clasificación usan el umbral activo. Precision, recall y F1 sin denominador se muestran como 0; ROC AUC y average precision requieren ambas clases.")
        st.download_button("Descargar resultados de evaluación", archivo_metricas(result),
                           "resultados_metricas.zip", "application/zip", on_click="ignore")
    except ErrorAPI as exc:
        st.error(str(exc))
