# ESTADO_ARCHIVO: EN_MODIFICACION
import streamlit as st
from pydantic import ValidationError

from api.schemas import Configuracion
from app.client import ErrorAPI
from app.ui import asegurar_navegacion, api_activa, cabecera

asegurar_navegacion("pages/0_Inicio.py")

cabecera("inicio", "TELCO / CENTRO DE CONTROL", "Comprender. Comparar. Retener.",
         "Carga tus artefactos, explora los datos y compara dos redes neuronales conectadas a la misma API.")
api = api_activa(False)
try:
    files = api.inventario()
    health = api.salud()
    if health["modelos_cargados"]:
        api.cargar_estado()
except ErrorAPI as exc:
    st.error(str(exc))
    st.stop()
cfg = api.config
for col, value, label in zip(st.columns(3), [str(len(files["modelos"])), str(len(files["scalers"])), "Conectada"],
                             ["Modelos disponibles", "Scalers disponibles", "API"]):
    col.metric(label, value)

st.subheader("Origen de los datos")
origins = {"proyecto": "Datos predispuestos del proyecto", "subido": "Dataset subido y preparado"}
selected = st.selectbox("Origen general de datos", list(origins),
                        index=list(origins).index(st.session_state.get("origen_datos_activo", "proyecto")),
                        format_func=origins.get, key="_origen_datos_selector")
st.session_state["origen_datos_activo"] = selected
if selected == "subido":
    saved = st.session_state.get("dataset_preparado")
    if saved:
        st.caption(f"{saved['fuente']} · {len(saved['filas'])} filas preparadas en esta sesión.")
    else:
        st.info("Todavía no hay un dataset preparado en esta sesión.")
    st.page_link("pages/2_Analisis.py", label="Subir y preparar datos en Análisis de lotes")
else:
    st.caption("Exploración usa este origen. Métricas permite elegir su conjunto; Lotes prioriza el nuevo dataset preparado.")

with st.expander("Subir modelo o scaler", expanded=not bool(files["modelos"])):
    kind = st.selectbox("¿Qué deseas subir?", ["Modelo Keras", "Scaler entrenado"], index=None)
    if kind is not None:
        kind_id = {"Modelo Keras": "modelo", "Scaler entrenado": "scaler"}[kind]
        types = ["keras"] if kind_id == "modelo" else ["pkl", "joblib"]
        uploaded = st.file_uploader("Archivo que deseas cargar", type=types, key=f"subir_{kind_id}", max_upload_size=100)
        if kind_id == "scaler":
            st.caption("Utiliza únicamente scalers de confianza: pickle/joblib carga objetos Python.")
        if st.button("Subir y validar archivo", disabled=uploaded is None):
            try:
                with st.spinner("La API está validando el archivo…"):
                    result = api.subir(uploaded, kind_id)
                st.session_state["aviso_carga"] = f"Archivo disponible: {result['archivo']}. Selecciónalo abajo para activarlo."
                st.rerun()
            except ErrorAPI as exc:
                st.error(str(exc))
if st.session_state.get("aviso_carga"):
    st.success(st.session_state.pop("aviso_carga"))

st.subheader("Modelos activos")
st.write("La API conserva los modelos hasta que apliques otra configuración. La selección también se recupera al reiniciar el servidor.")
if cfg:
    st.success(f"En uso: {cfg.modelo_1} + {cfg.modelo_2} · {cfg.scaler}")
    st.caption(f"Clasificación ≥ {cfg.umbral:.2%} · riesgo medio ≥ {cfg.riesgo_medio:.2%} · alto ≥ {cfg.riesgo_alto:.2%}")
if len(files["modelos"]) < 2 or not files["scalers"]:
    st.warning("Sube al menos dos modelos .keras y un scaler compatible para habilitar la carga.")
else:
    def indice(items, value):
        return items.index(value) if value in items else None
    with st.form("cargar_modelos"):
        left, right = st.columns(2)
        m1 = left.selectbox("Modelo 1 · clasificación", files["modelos"], index=indice(files["modelos"], cfg.modelo_1 if cfg else None))
        m2 = right.selectbox("Modelo 2 · riesgo", files["modelos"], index=indice(files["modelos"], cfg.modelo_2 if cfg else None))
        scaler = st.selectbox("Scaler entrenado compartido", files["scalers"], index=indice(files["scalers"], cfg.scaler if cfg else None))
        st.caption("Selecciona modelos entrenados con este scaler y las mismas 20 variables. Se verifican nombres, orden, dimensiones y activación de salida.")
        st.markdown("**Umbrales de decisión**")
        threshold = st.number_input("Clasificación: probabilidad mínima para abandono (%)", .01, 99.99, value=cfg.umbral * 100 if cfg else None, step=1.0, format="%.2f")
        medium = st.number_input("Riesgo medio desde (%)", .01, 99.99, value=cfg.riesgo_medio * 100 if cfg else None, step=1.0, format="%.2f")
        high = st.number_input("Riesgo alto desde (%)", .01, 99.99, value=cfg.riesgo_alto * 100 if cfg else None, step=1.0, format="%.2f")
        st.caption("Introduce porcentajes: 30 significa 30 %. Cada modelo compara su propia probabilidad con estos cortes compartidos. Clasificación y riesgo son decisiones distintas; los umbrales deben justificarse con validación.")
        submitted = st.form_submit_button("Cargar configuración en API", type="primary")
    if submitted:
        if any(value is None for value in [m1, m2, scaler, threshold, medium, high]):
            st.error("Selecciona ambos modelos, el scaler y los tres umbrales.")
        else:
            try:
                config = Configuracion(modelo_1=m1, modelo_2=m2, scaler=scaler,
                                       umbral=threshold / 100, riesgo_medio=medium / 100, riesgo_alto=high / 100)
                with st.spinner("Cargando modelos y scaler en la API…"):
                    api.configurar(config)
                st.rerun()
            except (ErrorAPI, ValidationError) as exc:
                st.error(str(exc))
                st.caption("La configuración anterior se conserva si la carga falla.")
st.divider()
left, right = st.columns(2)
with left, st.container(border=True):
    st.subheader("Conoce a tus clientes")
    st.write("Distribuciones, tasas de abandono por segmento y asociaciones entre variables.")
    st.page_link("pages/4_Visualizaciones.py", label="Abrir exploración")
with right, st.container(border=True):
    st.subheader("Compara ambos modelos")
    st.write("Predicciones individuales, archivos de clientes y métricas calculadas por la API.")
    st.page_link("pages/1_Prediccion.py", label="Predecir un cliente")
    st.page_link("pages/2_Analisis.py", label="Analizar un lote")
