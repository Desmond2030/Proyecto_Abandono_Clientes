# ESTADO_ARCHIVO: EN_MODIFICACION
"""Único formulario de carga y preparación de datasets de clientes."""
import hashlib
import json
import pandas as pd
import streamlit as st

from api.schemas import COLUMNAS
from app.client import ErrorAPI


def filas_a_eliminar(texto, total):
    rows = set()
    for piece in texto.split(","):
        piece = piece.strip()
        if not piece:
            continue
        limits = piece.split("-")
        if len(limits) > 2:
            raise ValueError("Usa posiciones como 1, 4-8, 12.")
        start, end = int(limits[0]), int(limits[-1])
        if not 1 <= start <= end <= total:
            raise ValueError(f"Las posiciones deben estar entre 1 y {total}.")
        rows.update(range(start, end + 1))
    return sorted(rows)


def mapa_json(texto):
    value = json.loads((texto or "").strip() or "{}")
    if not isinstance(value, dict):
        raise ValueError("Cada mapa de valores debe ser un objeto JSON, por ejemplo {\"Yes\": 1, \"No\": 0}.")
    return value


def editor_dataset(api):
    st.subheader("Cargar y preparar dataset")
    st.write("Sube aquí los datos para métricas, lotes y exploración. Se admiten otras columnas y nombres; después se construyen las 20 entradas del modelo.")
    file = st.file_uploader("Dataset de clientes", type=["csv", "xlsx", "parquet"], max_upload_size=20, key="dataset_archivo")
    if file is not None:
        digest = hashlib.sha256(file.getvalue() + file.name.encode()).hexdigest()
        if st.session_state.get("dataset_borrador_hash") != digest:
            try:
                preview = api.subir(file, "datos", "preparacion")
            except ErrorAPI as exc:
                st.error(str(exc))
                return
            st.session_state["dataset_borrador"] = preview
            st.session_state["dataset_borrador_hash"] = digest
    if "dataset_borrador" not in st.session_state:
        return
    digest = st.session_state["dataset_borrador_hash"]
    previous = st.session_state.get("dataset_receta", {}) if st.session_state.get("dataset_receta_hash") == digest else {}
    preview = st.session_state["dataset_borrador"]
    frame = pd.DataFrame(preview["filas"], columns=preview["columnas"])
    frame.index = range(1, len(frame) + 1)
    st.caption(f"Archivo de origen: {len(frame)} filas · {len(frame.columns)} columnas. Numeración desde 1, sin contar el encabezado.")
    st.dataframe(frame.head(100), width="stretch", height=280)
    st.caption("Vista previa: primeras 100 filas. La preparación se aplica a todas las filas del archivo.")
    drop = st.multiselect("Eliminar columnas", list(frame.columns), default=previous.get("eliminar_columnas", []), key=f"drop_{digest}")
    available = [c for c in frame.columns if c not in drop]
    if not available:
        st.warning("Conserva al menos las columnas que deseas mapear.")
        return
    editor_key = digest + hashlib.sha256(str(drop).encode()).hexdigest()[:8]
    with st.form(f"preparacion_{editor_key}"):
        source_name = st.text_input("Nombre y procedencia del dataset", value=previous.get("fuente", preview["fuente"]), max_chars=200)
        rows_text = st.text_input("Eliminar filas por posición", value=", ".join(map(str, previous.get("eliminar_filas", []))), placeholder="Ejemplo: 1, 4-8, 12")
        remove_nulls = st.checkbox("Eliminar filas con nulos o espacios vacíos en las columnas utilizadas", value=previous.get("eliminar_nulos", False))
        st.markdown("**Mapear columnas de entrada**")
        st.caption("Cada fila es una entrada del modelo. Elige la columna de origen; las no mapeadas quedan fuera. Puedes usar una misma columna con distintos mapas para crear las dummies de internet o pago.")
        mapping = pd.DataFrame({"Entrada del modelo": COLUMNAS,
                                "Columna de origen": [previous.get("entradas", {}).get(c, c if c in available else None) for c in COLUMNAS],
                                "Mapa de valores (JSON)": [json.dumps(previous.get("valores", {}).get(c, {}), ensure_ascii=False) for c in COLUMNAS]})
        edited = st.data_editor(mapping, hide_index=True, width="stretch", height=530,
            disabled=["Entrada del modelo"], num_rows="fixed", key=f"map_{editor_key}",
            column_config={"Columna de origen": st.column_config.SelectboxColumn(options=available, required=True),
                           "Mapa de valores (JSON)": st.column_config.TextColumn(width="large")})
        st.caption('Mapas opcionales: {"Yes": 1, "No": 0}; Contrato: {"Month-to-month": 0, "One year": 1, "Two year": 2}. Para DSL: {"DSL": 1, "Fiber optic": 0, "No": 0}. Sin mapa, se exige un número.')
        target_default = previous.get("objetivo", "Abandono" if "Abandono" in available else None)
        target = st.selectbox("Columna objetivo", [None] + available,
                             index=([None] + available).index(target_default) if target_default in available else 0,
                             format_func=lambda x: "Sin objetivo (lotes y exploración)" if x is None else x)
        target_map = st.text_input("Mapa de valores del objetivo (JSON)", value=json.dumps(previous.get("valores_objetivo", {}), ensure_ascii=False),
                                   help='Ejemplo: {"Yes": 1, "No": 0}. Si ya contiene 0/1, deja {}.')
        apply_scaler = st.checkbox("Aplicar scaler antes de predecir", value=previous.get("aplicar_scaler", True))
        st.caption("Activado: entradas sin escalar. Desactivado: el archivo YA está escalado con el scaler activo; se validará y no se escalará otra vez. Para explorar se reconstruyen las unidades originales.")
        submitted = st.form_submit_button("Validar y guardar dataset preparado", type="primary")
    if submitted:
        try:
            entries = dict(zip(edited["Entrada del modelo"], edited["Columna de origen"]))
            if any(not isinstance(v, str) or not v for v in entries.values()):
                raise ValueError("Selecciona la columna de origen para cada una de las 20 entradas.")
            recipe = {"fuente": source_name.strip(), "filas": preview["filas"], "eliminar_columnas": drop,
                      "eliminar_filas": filas_a_eliminar(rows_text, len(frame)), "eliminar_nulos": remove_nulls,
                      "entradas": entries, "valores": {row["Entrada del modelo"]: mapa_json(row["Mapa de valores (JSON)"])
                                                       for row in edited.to_dict("records")},
                      "objetivo": target, "valores_objetivo": mapa_json(target_map), "aplicar_scaler": apply_scaler}
            with st.spinner("Preparando y validando en la API…"):
                result = api.preparar(recipe)
            st.session_state["dataset_preparado"] = result
            st.session_state["dataset_receta"] = recipe
            st.session_state["dataset_receta_hash"] = digest
            st.success(f"Dataset preparado: {len(result['filas'])} filas, {result['eliminadas']} eliminadas. Solo las 20 entradas mapeadas llegan a los modelos.")
            if result["columnas_omitidas"]:
                st.caption("Columnas no utilizadas: " + ", ".join(result["columnas_omitidas"]))
            st.session_state["lote_origen_activo"] = "subido"
            st.session_state["_lote_selector"] = "subido"
            st.success("El nuevo lote está listo para analizarse abajo. También está disponible en el selector de Métricas.")
        except (ValueError, TypeError, ErrorAPI) as exc:
            st.error(str(exc))
            st.caption("El último dataset preparado se conserva; este borrador todavía no está activo.")
