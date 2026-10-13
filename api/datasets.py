# ESTADO_ARCHIVO: EN_MODIFICACION
"""Preparación explícita de datasets, sin modificar archivos originales."""
import json
import numpy as np
import pandas as pd

from api.schemas import COLUMNAS
from api.predict import ErrorPrediccion, validar_tabla
from src.Data_Processor import DataProcessor


def vista_previa(frame, fuente):
    if frame.empty or len(frame) > 10000 or len(frame.columns) > 200:
        raise ErrorPrediccion("Se admiten 1–10.000 filas y hasta 200 columnas de origen.")
    if frame.columns.duplicated().any() or any(not isinstance(c, str) or not c.strip() for c in frame.columns):
        raise ErrorPrediccion("Los encabezados deben ser textos únicos y no vacíos.")
    return {"fuente": fuente, "columnas": list(frame.columns),
            "filas": json.loads(frame.to_json(orient="records", date_format="iso"))}


def clave(value):
    if isinstance(value, (float, int)) and float(value).is_integer():
        return str(int(value))
    return str(value).strip()


def convertir(series, mapping, nombre):
    if mapping:
        keys = series.map(clave)
        if not keys.isin(mapping).all():
            raise ErrorPrediccion(f"El mapa de {nombre} no cubre todos sus valores. Revisa la vista previa.")
        series = keys.map(mapping)
    try:
        return pd.to_numeric(series, errors="raise")
    except (ValueError, TypeError) as exc:
        raise ErrorPrediccion(f"{nombre} contiene texto: configura su mapa de valores.") from exc


def matriz_entrada(frame, predictor, aplicar_scaler):
    if set(frame.columns) != set(COLUMNAS) or frame.columns.duplicated().any():
        raise ErrorPrediccion("Se requieren exactamente las 20 variables, sin objetivo ni identificadores.")
    processor = DataProcessor()
    processor.data = frame[COLUMNAS].copy()
    try:
        processor.set_types({c: "float64" for c in COLUMNAS})
    except (ValueError, TypeError) as exc:
        raise ErrorPrediccion("Todas las entradas deben ser numéricas.") from exc
    processor.scaler = predictor.scaler
    if aplicar_scaler:
        clients = validar_tabla(processor.data)
        scaled = predictor.transformar(clients)
        return processor.data, scaled
    scaled = processor.data.to_numpy(dtype=float)
    low, high = processor.scaler.feature_range
    if not np.isfinite(scaled).all() or (scaled < low - 1e-6).any() or (scaled > high + 1e-6).any():
        raise ErrorPrediccion("Sin aplicar scaler se requieren entradas ya escaladas dentro de su rango.")
    raw = pd.DataFrame(processor.scaler.inverse_transform(scaled), columns=COLUMNAS)
    # Solo redondeo del error numérico de inversión, nunca una categoría arbitraria.
    for c in set(COLUMNAS) - {"Antiguedad(Meses)", "Cargos_Mensuales"}:
        rounded = raw[c].round()
        if not np.allclose(raw[c], rounded, atol=1e-5, rtol=0):
            raise ErrorPrediccion(f"{c} no corresponde a una categoría válida con este scaler.")
        raw[c] = rounded
    validar_tabla(raw)
    values = raw.to_numpy()
    if (values < predictor.scaler.data_min_ - 1e-5).any() or (values > predictor.scaler.data_max_ + 1e-5).any():
        raise ErrorPrediccion("Los datos escalados no corresponden al rango de entrenamiento.")
    return raw, scaled.astype("float32")  # No transform: ya estaba escalado.


def preparar(request, predictor):
    frame = pd.DataFrame(request.filas)
    vista_previa(frame, request.fuente)
    if set(request.entradas) != set(COLUMNAS):
        raise ErrorPrediccion("Mapea cada una de las 20 variables de entrada.")
    if set(request.valores) - set(COLUMNAS):
        raise ErrorPrediccion("Hay mapas de valores para variables no admitidas.")
    if set(request.eliminar_columnas) - set(frame.columns):
        raise ErrorPrediccion("Se intenta eliminar una columna inexistente.")
    if any(i > len(frame) for i in request.eliminar_filas):
        raise ErrorPrediccion("Hay posiciones de fila fuera del archivo.")
    frame.index = np.arange(1, len(frame) + 1)
    frame = frame.drop(columns=request.eliminar_columnas, index=list(set(request.eliminar_filas)))
    used = set(request.entradas.values()) | ({request.objetivo} if request.objetivo else set())
    if used - set(frame.columns):
        raise ErrorPrediccion("Alguna columna mapeada falta o fue eliminada.")
    if request.objetivo and request.objetivo in request.entradas.values():
        raise ErrorPrediccion("La columna objetivo no puede usarse como entrada del modelo.")
    if request.eliminar_nulos:
        frame = frame.replace(r"^\s*$", np.nan, regex=True).dropna(subset=list(used))
    if frame.empty:
        raise ErrorPrediccion("La preparación eliminó todas las filas.")
    mapped = pd.DataFrame({c: convertir(frame[source], request.valores.get(c, {}), c)
                           for c, source in request.entradas.items()}, index=frame.index)[COLUMNAS]
    raw, _ = matriz_entrada(mapped, predictor, request.aplicar_scaler)
    if request.objetivo:
        labels = convertir(frame[request.objetivo], request.valores_objetivo, "Abandono")
        if labels.isna().any() or not labels.isin([0, 1]).all():
            raise ErrorPrediccion("Mapea la columna objetivo a 0 (permanece) y 1 (abandona).")
        raw["Abandono"] = labels.to_numpy(dtype=int)
    return {"fuente": request.fuente, "columnas": list(raw.columns), "filas": raw.to_dict("records"),
            "datos_exportacion": vista_previa(frame, request.fuente),
            "entrada": mapped.to_dict("records"), "aplicar_scaler": request.aplicar_scaler,
            "revision_preparacion": predictor.revision, "filas_origen": frame.index.tolist(),
            "eliminadas": len(request.filas) - len(frame),
            "columnas_omitidas": [c for c in frame.columns if c not in used]}
