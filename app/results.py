# ESTADO_ARCHIVO: EN_MODIFICACION
"""Resultados de ambos modelos: exportación alineada y gráficos interactivos."""
import io
import zipfile
import altair as alt
import pandas as pd
import streamlit as st


def tabla_predicciones(payload, results):
    source = payload.get("datos_exportacion", payload)
    output = pd.DataFrame(source["filas"], columns=source["columnas"]).copy()
    if any(len(values) != len(output) for values in results.values()):
        raise ValueError("Las predicciones no corresponden a las filas del dataset.")
    def agregar(name, values):
        candidate, suffix = name, 2
        while candidate in output.columns:
            candidate = f"{name}_{suffix}"
            suffix += 1
        output[candidate] = values
    agregar("Fila_origen", payload.get("filas_origen", list(range(1, len(output) + 1))))
    agregar("Prediccion_Abandono_Modelo_1", [int(p.abandono == "Yes") for p in results["modelo_1"]])
    agregar("Probabilidad_Abandono_Modelo_2", [p.probabilidad for p in results["modelo_2"]])
    for slot in ("modelo_1", "modelo_2"):
        agregar(f"Archivo_{slot}", [p.modelo for p in results[slot]])
    agregar("Umbral_Modelo_1", [p.umbral for p in results["modelo_1"]])
    return output


def filas_graficos(payload, results):
    indices = payload.get("filas_origen", list(range(1, len(payload["filas"]) + 1)))
    rows = []
    for i, first, second, record in zip(indices, results["modelo_1"], results["modelo_2"], payload["filas"]):
        row = {"fila": i, "modelo_1_clase": int(first.abandono == "Yes"),
               "modelo_2_probabilidad": second.probabilidad}
        if "Abandono" in record:
            row["Real"] = int(record["Abandono"])
        rows.append(row)
    return rows


def graficos_modelos(rows):
    frame = pd.DataFrame(rows)
    with st.container():
        st.subheader("Modelo 1 · clasificación")
        counts = []
        for field, serie in [("modelo_1_clase", "Predicha"), ("Real", "Real")]:
            if field in frame:
                for label in (0, 1):
                    counts.append({"Clase": "Permanece (0)" if label == 0 else "Abandona (1)",
                                   "Serie": serie, "Clientes": int(frame[field].eq(label).sum())})
        chart = alt.Chart(alt.Data(values=counts)).mark_bar().encode(
            x=alt.X("Clase:N", title="Clase de abandono", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Clientes:Q", axis=alt.Axis(tickMinStep=1)), xOffset="Serie:N",
            color=alt.Color("Serie:N", scale=alt.Scale(domain=["Predicha", "Real"], range=["#2563a6", "#b9753b"])),
            tooltip=["Clase:N", "Serie:N", "Clientes:Q"]).properties(height=300)
        st.altair_chart(chart, width="stretch")
    # Segunda fila a ancho completo: muchos clientes necesitan un eje navegable.
    st.subheader("Modelo 2 · probabilidad por cliente")
    values = frame.to_dict("records")
    tooltip = [alt.Tooltip("fila:Q", title="Fila original"),
               alt.Tooltip("modelo_2_probabilidad:Q", title="Probabilidad", format=".2%")]
    if "Real" in frame:
        tooltip.append(alt.Tooltip("Real:N", title="Clase real"))
    chart = alt.Chart(alt.Data(values=values)).mark_circle(size=65, opacity=.75).encode(
        x=alt.X("fila:Q", title="Cliente (posición original de la fila)", axis=alt.Axis(tickMinStep=1)),
        y=alt.Y("modelo_2_probabilidad:Q", title="Probabilidad de abandono", scale=alt.Scale(domain=[0, 1]),
                axis=alt.Axis(format=".0%")), tooltip=tooltip)
    if "Real" in frame:
        chart = chart.encode(color=alt.Color("Real:N", title="Clase real", scale=alt.Scale(range=["#0f766e", "#b9753b"])))
    else:
        chart = chart.encode(color=alt.value("#7863a7"))
    st.altair_chart(chart.properties(height=350).interactive(bind_y=False), width="stretch")
    st.caption("Cada punto corresponde a una fila; acerca o desplaza el eje horizontal y consulta el detalle al pasar el cursor. Sin etiquetas reales se muestran solo las predicciones.")


def matriz_interactiva(matrix):
    values = [{"Real": str(real), "Predicción": str(pred), "Clientes": matrix[real][pred]}
              for real in (0, 1) for pred in (0, 1)]
    base = alt.Chart(alt.Data(values=values)).encode(
        x=alt.X("Predicción:N", axis=alt.Axis(labelAngle=0)), y="Real:N",
        tooltip=["Real:N", "Predicción:N", "Clientes:Q"])
    cells = base.mark_rect().encode(color=alt.Color("Clientes:Q", scale=alt.Scale(scheme="blues")))
    text = base.mark_text(fontSize=22).encode(text="Clientes:Q", color=alt.value("#b45309"))
    st.altair_chart((cells + text).properties(height=240), width="stretch")


def archivo_metricas(result):
    """Solo evaluación: sin datos de clientes ni predicciones del lote."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("metricas.csv", pd.DataFrame(result["metricas"]).to_csv(index=False).encode("utf-8-sig"))
        for slot, matrix in result["matrices"].items():
            archive.writestr(f"{slot}_matriz.csv", pd.DataFrame(matrix, index=["Real 0", "Real 1"],
                columns=["Predicción 0", "Predicción 1"]).to_csv().encode("utf-8-sig"))
            report = {key: value for key, value in result["reportes"][slot].items() if isinstance(value, dict)}
            archive.writestr(f"{slot}_reporte.csv", pd.DataFrame(report).T.to_csv().encode("utf-8-sig"))
    return buffer.getvalue()
