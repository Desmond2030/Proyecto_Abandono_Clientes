# ESTADO_ARCHIVO: EN_MODIFICACION
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

from app.client import ErrorAPI
from app.ui import asegurar_navegacion, api_activa, cabecera, desde_respuesta, dataset_activo

asegurar_navegacion("pages/4_Visualizaciones.py")

cabecera("exploracion", "04 / EXPLORACIÓN DEL DATASET", "Los patrones detrás del abandono.",
         "Explora el dataset procesado del EDA: permanencia, cargos mensuales, segmentos y asociaciones. No se requieren modelos cargados.")
api = api_activa(False)
try:
    payload = dataset_activo(api, "exploracion")
    data, _ = desde_respuesta(payload)
except ErrorAPI as exc:
    st.error(str(exc))
    st.stop()
has_target = "Abandono" in data.columns
st.caption(f"Fuente: {payload['fuente']} · datos preparados y validados por la API, en unidades originales.")
contracts = st.multiselect("Filtrar por contrato", [0, 1, 2], default=[0, 1, 2],
                           format_func=lambda n: ["Mes a mes", "Un año", "Dos años"][n])
view = data.loc[data.Contrato.isin(contracts)].copy()
if view.empty:
    st.info("Selecciona al menos un contrato con registros.")
    st.stop()
for col, label, value in zip(st.columns(3), ["Clientes en la vista", "Abandono observado", "Antigüedad media"],
                            [f"{len(view):,}", f"{view.Abandono.mean():.1%}" if has_target else "Sin objetivo", f"{view['Antiguedad(Meses)'].mean():.1f} meses"]):
    col.metric(label, value)
distribution, segments, associations, quality = st.tabs(["Distribuciones", "Segmentos", "Asociaciones", "Calidad y contexto"])
with distribution:
    variable = st.selectbox("Variable continua", ["Antiguedad(Meses)", "Cargos_Mensuales"])
    fig, axes = plt.subplots(2, 1, figsize=(9, 5), sharex=True, gridspec_kw={"height_ratios": [1, 4]}, layout="constrained")
    axes[0].boxplot(view[variable], orientation="horizontal", patch_artist=True,
                    boxprops={"facecolor": "#e9b98b"})
    axes[0].set_yticks([])
    if has_target:
        for value, color, label in [(0, "#0f766e", "Permanece"), (1, "#b96736", "Abandona")]:
            axes[1].hist(view.loc[view.Abandono == value, variable], bins=20, alpha=.65, color=color, label=label)
    else:
        axes[1].hist(view[variable], bins=20, color="#a86336", label="Clientes")
    axes[1].set(xlabel=variable, ylabel="Clientes")
    axes[1].legend()
    st.pyplot(fig, width="stretch")
    plt.close(fig)
with segments:
    field = st.selectbox("Segmentar por", ["Contrato", "Adulto_Mayor", "Pareja", "Dependientes", "Internet_DSL", "Internet_Fiber optic", "Facturacion_Electronica"])
    grouped = (view.groupby(field).Abandono.agg(Clientes="size", Abandonos="sum", Tasa="mean")
               if has_target else view.groupby(field).size().to_frame("Clientes"))
    if field == "Contrato":
        grouped.index = grouped.index.map({0: "Mes a mes", 1: "Un año", 2: "Dos años"})
    else:
        grouped.index = grouped.index.map({0: "No", 1: "Sí"})
    st.bar_chart(grouped["Tasa" if has_target else "Clientes"], color="#a86336",
                 y_label="Proporción de abandono" if has_target else "Clientes")
    st.dataframe(grouped.style.format({"Tasa": "{:.1%}"}), width="stretch")
    st.caption("Las tasas describen asociaciones en estos datos; no prueban causas de abandono.")
with associations:
    st.write("Asociaciones mixtas con dython entre todas las variables disponibles, incluido el objetivo cuando existe.")
    all_variables = st.checkbox("Incluir todas las variables", value=True)
    chosen = list(view.columns) if all_variables else st.multiselect("Variables", list(view.columns), default=list(view.columns))
    if st.button("Calcular asociaciones"):
        if len(chosen) < 2:
            st.error("Selecciona al menos 2 variables.")
        else:
            try:
                import io
                import textwrap
                from dython.nominal import associations as mixed_associations
                constant = [c for c in chosen if view[c].nunique() < 2]
                if constant:
                    st.warning(f"Variables constantes en la vista: {constant}; interpreta sus asociaciones con cautela.")
                nominal = [c for c in chosen if c not in ["Antiguedad(Meses)", "Cargos_Mensuales"]]
                matrix = mixed_associations(view[chosen], nominal_columns=nominal, compute_only=True)["corr"]
                fig, ax = plt.subplots(figsize=(max(12, len(chosen) * .95), max(10, len(chosen) * .85)), layout="constrained")
                sns.heatmap(matrix, ax=ax, cmap="BrBG", annot=True, annot_kws={"size": 10},
                            fmt=".2f", vmin=-1, vmax=1, square=True)
                labels = [textwrap.fill(c, 24, break_long_words=True) for c in chosen]
                ax.set_xticklabels(labels, rotation=55, ha="right", fontsize=11)
                ax.set_yticklabels(labels, rotation=0, fontsize=11)
                ax.set_title("Asociaciones entre variables", pad=20)
                st.caption("Pantalla completa: usa el icono de expansión en la esquina superior derecha del gráfico. La descarga SVG conserva los nombres completos y permite ampliar sin perder detalle.")
                st.pyplot(fig, width="stretch")
                svg = io.StringIO()
                fig.savefig(svg, format="svg", bbox_inches="tight")
                st.download_button("Descargar matriz SVG", svg.getvalue(), "asociaciones.svg", "image/svg+xml", on_click="ignore")
                plt.close(fig)
                with st.expander("Consultar todos los valores de la matriz"):
                    st.dataframe(matrix, width="stretch", height=500)
                    st.download_button("Descargar valores CSV", matrix.to_csv().encode("utf-8-sig"),
                                       "asociaciones.csv", "text/csv", on_click="ignore")
                st.caption("Las medidas mixtas dependen del tipo de variable; no todas tienen signo o interpretación equivalente a Pearson.")
            except ImportError:
                st.info("La matriz mixta requiere dython, declarado en requirements.txt.")
with quality:
    st.write("Referencia del dataset original del proyecto: el preprocesamiento traduce variables, agrupa la ausencia de servicios en 0, codifica contrato como 0/1/2 y genera dummies de internet y pago.")
    st.write("Las categorías de referencia son sin internet y tarjeta automática: todas sus dummies valen 0. El EDA excluye género y cargos totales; el ID nunca entra al modelo.")
    st.write("Los 11 espacios en TotalCharges del CSV original se sustituyen por 0 en el notebook; esta columna queda fuera de la inferencia. Antigüedad 0 no demuestra que un cliente haya abandonado.")
    st.dataframe(pd.DataFrame({"Nulos": view.isna().sum(), "Valores distintos": view.nunique(),
                               "Espacios vacíos": view.astype(str).apply(lambda c: c.str.strip().eq("").sum())}), width="stretch")
    st.caption(f"Filas idénticas en la vista: {view.duplicated().sum()}. Sin identificador, coincidencias de atributos no prueban clientes duplicados.")
