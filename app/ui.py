# ESTADO_ARCHIVO: EN_MODIFICACION
import html

import pandas as pd
import streamlit as st

from api.schemas import COLUMNAS, Cliente
from app.client import ApiClient, ErrorAPI

PALETA = {"inicio": ("#164e63", "#0f766e"), "prediccion": ("#115e59", "#0f766e"),
          "lotes": ("#1e3a5f", "#2563a6"), "metricas": ("#4c356b", "#7863a7"),
          "exploracion": ("#794a29", "#a86336")}


def asegurar_navegacion(pagina):
    # Un enlace directo tras arrancar puede activar el descubrimiento pages/.
    # Primero inicializar Home y después recuperar la página solicitada.
    if not st.session_state.get("_navegacion_iniciada", False):
        st.session_state["_destino_inicial"] = pagina
        st.switch_page("Home.py")


def cabecera(key, eyebrow, title, description):
    a, b = PALETA[key]
    corners = {"inicio": "20px", "prediccion": "28px 28px 8px 28px",
               "lotes": "8px", "metricas": "8px 32px", "exploracion": "3px 24px 24px 3px"}[key]
    st.html(f"""<style>
    .block-container {{max-width:1200px; padding-top:5rem; padding-bottom:3rem;}}
    .telco-hero {{background:linear-gradient(120deg,{a},{b});color:#fff;
      border-radius:{corners};padding:clamp(1.2rem,3vw,2.4rem);margin:0 0 1.6rem;
      overflow-wrap:anywhere;}}
    .telco-hero h1 {{font-size:clamp(1.7rem,3.5vw,2.8rem);line-height:1.15;color:#fff;
      margin:.5rem 0 .8rem;padding:0;font-weight:750;}}
    .telco-hero p {{max-width:760px;line-height:1.6;margin:0;color:#e8f4f3;}}
    .telco-hero small {{letter-spacing:.13em;font-weight:650;}}
    [data-testid="stMetric"] {{border:1px solid color-mix(in srgb,{b} 25%,transparent);
      border-top:3px solid {b};border-radius:12px;padding:1rem;}}
    [data-testid="stMetricLabel"] {{white-space:normal;}}
    [data-testid="stMetricValue"] {{font-size:clamp(1.4rem,3vw,2rem);}}
    @media(max-width:640px) {{.block-container {{padding:4.5rem 1rem 2.5rem;}}}}
    </style><section class="telco-hero"><small>{html.escape(eyebrow)}</small>
    <h1>{html.escape(title)}</h1><p>{html.escape(description)}</p></section>""")


def api_activa(requiere_modelos=True):
    api = ApiClient()
    try:
        health = api.salud()
        if health.get("error_carga"):
            st.warning(health["error_carga"])
        if requiere_modelos:
            if not health["modelos_cargados"]:
                st.info("Selecciona y carga los modelos en Inicio.")
                st.page_link("pages/0_Inicio.py", label="Ir a configuración")
                st.stop()
            api.cargar_estado()
            st.caption(f"Activos en API: {api.config.modelo_1} · {api.config.modelo_2} · {api.config.scaler}")
        return api
    except ErrorAPI as exc:
        st.error(str(exc))
        st.code("python app/run.py", language="bash")
        st.stop()


def desde_respuesta(data):
    frame = pd.DataFrame(data["filas"], columns=data["columnas"])
    clients = [Cliente.model_validate(row) for row in frame[COLUMNAS].to_dict("records")]
    return frame, clients


def dataset_activo(api, uso, origen=None):
    """Inicio elige el origen general; Lotes y Métricas pueden elegir su conjunto."""
    if (origen or st.session_state.get("origen_datos_activo", "proyecto")) == "subido":
        payload = st.session_state.get("dataset_preparado")
        if payload is None:
            st.info("Seleccionaste datos subidos. Carga y prepara el archivo en Análisis de lotes.")
            st.page_link("pages/2_Analisis.py", label="Preparar dataset")
            st.stop()
        if api.config is None:
            api.cargar_estado()
        if payload["revision_preparacion"] != api.revision:
            st.warning("Cambió la configuración de modelos o scaler. Vuelve a preparar el dataset en Análisis de lotes.")
            st.page_link("pages/2_Analisis.py", label="Revisar preparación")
            st.stop()
        st.caption(f"Origen de datos: dataset subido · {payload['fuente']}")
    else:
        payload = api.datos("validation" if uso == "evaluacion" else "exploration")
        st.caption(f"Origen de datos: proyecto · {payload['fuente']}")
    if uso == "evaluacion" and "Abandono" not in payload["columnas"]:
        st.info("El dataset no tiene objetivo. Puedes usarlo para lotes y exploración; para métricas, mapea su objetivo en Análisis de lotes.")
        st.stop()
    return payload


def plantilla():
    # Fila ficticia en el contrato del notebook; no contiene identificadores.
    row = dict.fromkeys(COLUMNAS, 0)
    row.update({"Antiguedad(Meses)": 12, "Servicio_Telefono": 1,
                "Internet_DSL": 1, "Cargos_Mensuales": 50})
    return pd.DataFrame([row]).to_csv(index=False).encode("utf-8-sig")


def mostrar_resultados(results, config):
    for col, slot in zip(st.columns(2), ("modelo_1", "modelo_2")):
        result = results[slot][0]
        with col, st.container(border=True):
            st.subheader("Modelo 1" if slot == "modelo_1" else "Modelo 2")
            st.caption(result.modelo)
            if slot == "modelo_1":
                st.metric("Clasificación de abandono (0/1)", int(result.abandono == "Yes"))
            else:
                st.metric("Probabilidad estimada de abandono", f"{result.probabilidad:.2%}")
            st.progress(result.probabilidad, text=f"Probabilidad de este modelo: {result.probabilidad:.2%}")
            st.write(f"**Predicción:** {'Abandona' if result.abandono == 'Yes' else 'Permanece'}")
            st.write(f"**Nivel de riesgo:** {result.riesgo}")
            st.caption(f"Umbral de clasificación: {result.umbral:.2%}. "
                       f"Abandona si la probabilidad es ≥ {result.umbral:.2%}; permanece si es menor.")
            st.caption(f"Riesgo bajo: < {config.riesgo_medio:.2%} · "
                       f"medio: ≥ {config.riesgo_medio:.2%} y < {config.riesgo_alto:.2%} · "
                       f"alto: ≥ {config.riesgo_alto:.2%}.")
    st.caption("Clasificación y nivel de riesgo usan cortes distintos, aplicados a la probabilidad de cada modelo sin redondear. Superar el umbral de abandono no implica riesgo alto. Son estimaciones, no certezas.")
