# ESTADO_ARCHIVO: EN_MODIFICACION
"""Inferencia del servidor FastAPI consumida por Streamlit mediante HTTP."""
from pathlib import Path
from threading import RLock

import joblib
import numpy as np
import pandas as pd
from pydantic import ValidationError
from sklearn.preprocessing import MinMaxScaler
from sklearn.utils.validation import check_is_fitted

from api.schemas import COLUMNAS, Cliente, Configuracion, Prediccion
from api.loaders import cargar_archivo

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"


class ErrorPrediccion(ValueError):
    pass


def inventario(directory=MODELS):
    directory = Path(directory)
    return {
        "modelos": sorted(p.name for p in directory.glob("*.keras") if p.is_file()),
        "scalers": sorted(p.name for p in directory.iterdir()
                          if p.is_file() and p.suffix in {".pkl", ".joblib"}
                          and p.name != "columnas.pkl") if directory.exists() else [],
    }


def archivo_local(directory, name, suffixes):
    root = Path(directory).resolve()
    path = (root / name).resolve()
    if path.parent != root or path.name != name or path.suffix not in suffixes:
        raise ErrorPrediccion("Seleccione un archivo directamente dentro de models/.")
    if not path.is_file():
        raise ErrorPrediccion(f"No existe el artefacto: {name}.")
    return path


def validar_tabla(frame, objetivo=False):
    """No elimina columnas inesperadas ni rellena variables ausentes con cero."""
    if frame.empty or len(frame) > 10000:
        raise ErrorPrediccion("Se admiten entre 1 y 10.000 filas.")
    if frame.columns.duplicated().any():
        raise ErrorPrediccion("Hay nombres de columna duplicados.")
    expected = set(COLUMNAS) | ({"Abandono"} if objetivo else set())
    missing, extra = expected - set(frame.columns), set(frame.columns) - expected
    if missing or extra:
        raise ErrorPrediccion(f"Columnas faltantes: {sorted(missing)}. No admitidas: {sorted(extra)}.")
    if objetivo and (frame.Abandono.isna().any() or not frame.Abandono.isin([0, 1]).all()):
        raise ErrorPrediccion("Abandono debe contener exclusivamente 0 o 1.")
    clients = []
    for number, row in enumerate(frame[COLUMNAS].to_dict("records"), start=1):
        try:
            clients.append(Cliente.model_validate(row))
        except ValidationError as exc:
            # No exponer la fila o sus valores en errores de lotes.
            issues = "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}"
                               for e in exc.errors(include_input=False, include_url=False))
            raise ErrorPrediccion(f"Fila {number}: {issues}") from exc
    return clients


class Predictor:
    def __init__(self, config: Configuracion, directory=MODELS):
        # Carga local exclusivamente: pickle/joblib requieren artefactos de confianza.
        self.config = config.model_copy(deep=True)
        self.lock = RLock()
        try:
            path = archivo_local(directory, config.scaler, {".pkl", ".joblib"})
            self.processor = cargar_archivo(path, "scaler")
            self.scaler = self.processor.scaler
            if not isinstance(self.scaler, MinMaxScaler):
                raise ErrorPrediccion("El artefacto debe ser un MinMaxScaler entrenado.")
            check_is_fitted(self.scaler)
            names = list(getattr(self.scaler, "feature_names_in_", []))
            if names != COLUMNAS or self.scaler.n_features_in_ != len(COLUMNAS):
                raise ErrorPrediccion("El scaler no coincide con las 20 columnas y su orden del notebook.")
            if not np.isfinite(self.scaler.scale_).all():
                raise ErrorPrediccion("El scaler contiene parámetros no finitos.")
            columns_file = Path(directory) / "columnas.pkl"
            if columns_file.exists() and list(joblib.load(columns_file)) != names:
                raise ErrorPrediccion("columnas.pkl y feature_names_in_ no coinciden.")
            self.models = {}
            for slot in ("modelo_1", "modelo_2"):
                model_path = archivo_local(directory, getattr(config, slot), {".keras"})
                adapter = cargar_archivo(model_path, "modelo")
                model = adapter.model
                if (isinstance(model.input_shape, list) or len(model.input_shape) != 2
                        or model.input_shape[-1] != len(names)
                        or model.output_shape != (None, 1)):
                    raise ErrorPrediccion(f"{model_path.name}: se requiere entrada de 20 variables y una salida.")
                activation = getattr(getattr(model.layers[-1], "activation", None), "__name__", "")
                if activation != "sigmoid":
                    raise ErrorPrediccion(f"{model_path.name}: la salida debe utilizar sigmoid para P(Abandono=1).")
                adapter.scaler = self.scaler
                self.models[slot] = adapter
        except ErrorPrediccion:
            raise
        except Exception as exc:
            raise ErrorPrediccion(f"No se pudieron cargar los artefactos ({type(exc).__name__}). Verifique versiones y archivos.") from exc

    def transformar(self, clients):
        if not 1 <= len(clients) <= 10000:
            raise ErrorPrediccion("Se admiten entre 1 y 10.000 clientes.")
        frame = pd.DataFrame([c.model_dump(by_alias=True) for c in clients], columns=COLUMNAS)
        # Revalidar incluso clientes construidos fuera de Pydantic.
        validar_tabla(frame)
        values = frame.to_numpy(dtype=float)
        outside = (values < self.scaler.data_min_) | (values > self.scaler.data_max_)
        if outside.any():
            cols = frame.columns[outside.any(axis=0)].tolist()
            raise ErrorPrediccion(f"Valores fuera del rango de entrenamiento en {cols}. No se recortan automáticamente.")
        # Instancia por solicitud: el DataProcessor no se comparte entre hilos.
        from src.Data_Processor import DataProcessor
        processor = DataProcessor()
        processor.data = frame
        processor.set_types({column: "float64" for column in COLUMNAS})
        processor.scaler = self.scaler
        scaled = processor.scaler.transform(processor.data)  # Nunca fit en inferencia.
        if scaled.shape != (len(clients), len(COLUMNAS)) or not np.isfinite(scaled).all():
            raise ErrorPrediccion("La transformación produjo dimensiones o valores inválidos.")
        return scaled.astype("float32")

    def predecir(self, clients, slots=("modelo_1", "modelo_2")):
        scaled = self.transformar(clients)
        return self.predecir_matriz(scaled, slots)

    def predecir_matriz(self, scaled, slots=("modelo_1", "modelo_2")):
        if (scaled.ndim != 2 or scaled.shape[1] != len(COLUMNAS)
                or not 1 <= len(scaled) <= 10000 or not np.isfinite(scaled).all()):
            raise ErrorPrediccion("Matriz de inferencia inválida.")
        results = {}
        with self.lock:
            for slot in slots:
                if slot not in self.models:
                    raise ErrorPrediccion("Modelo no disponible.")
                try:
                    # Lotes pequeños evitan consumir memoria con una carga grande.
                    outputs = [np.asarray(self.models[slot](scaled[i:i+256], training=False))
                               for i in range(0, len(scaled), 256)]
                    probabilities = np.concatenate(outputs, axis=0)
                except Exception as exc:
                    raise ErrorPrediccion("El modelo no pudo procesar las entradas.") from exc
                if (probabilities.shape != (len(scaled), 1) or not np.isfinite(probabilities).all()
                        or (probabilities < 0).any() or (probabilities > 1).any()):
                    raise ErrorPrediccion("El modelo devolvió probabilidades inválidas.")
                results[slot] = [self.resultado(slot, float(p)) for p in probabilities[:, 0]]
        return results

    def resultado(self, slot, probability):
        cfg = self.config
        return Prediccion(
            modelo=getattr(cfg, slot), probabilidad=probability,
            abandono="Yes" if probability >= cfg.umbral else "No",
            riesgo="Alto" if probability >= cfg.riesgo_alto else "Medio" if probability >= cfg.riesgo_medio else "Bajo",
            umbral=cfg.umbral,
        )
