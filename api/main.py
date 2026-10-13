# ESTADO_ARCHIVO: EN_MODIFICACION
"""Backend HTTP del dashboard. Ejecutar con un solo worker."""
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException, Request
from starlette.concurrency import run_in_threadpool
from api.evaluation import metricas

from api.loaders import EXTENSIONES, cargar_archivo
from api.predict import ErrorPrediccion, MODELS, ROOT, Predictor, inventario, validar_tabla
from api.schemas import Preparacion, DatasetInferencia, COLUMNAS, Configuracion, Evaluacion, Lote, Peticion, Prediccion, RespuestaLote

CONFIG_FILE = MODELS / "configuracion_inferencia.json"
configuration_lock = Lock()


@asynccontextmanager
async def lifespan(application):
    application.state.predictor = None
    application.state.error_carga = None
    if CONFIG_FILE.exists():
        try:
            config = Configuracion.model_validate_json(CONFIG_FILE.read_text(encoding="utf-8"))
            candidate = await run_in_threadpool(Predictor, config)
            candidate.revision = uuid4().hex
            application.state.predictor = candidate
        except (ValueError, OSError) as exc:
            application.state.error_carga = f"No se restauró la configuración guardada: {exc}"
    yield


app = FastAPI(title="Telco · Abandono de clientes", version="0.4.0", lifespan=lifespan)
app.state.predictor = None
app.state.error_carga = None
Revision = Annotated[str | None, Header(alias="X-Configuration-Id")]


def activo(revision=None):
    predictor = app.state.predictor
    if predictor is None:
        raise HTTPException(409, "Primero cargue los artefactos en Inicio o mediante PUT /configuracion.")
    if revision is not None and revision != getattr(predictor, "revision", None):
        raise HTTPException(409, "La configuración cambió. Actualice la página antes de volver a predecir.")
    return predictor


def estado(predictor):
    return {**predictor.config.model_dump(), "revision": predictor.revision}


@app.get("/health")
def health():
    return {"servicio": "telco-churn", "version": app.version, "estado": "ok",
            "modelos_cargados": app.state.predictor is not None,
            "error_carga": app.state.error_carga}


@app.get("/artefactos")
def artefactos():
    return inventario()


@app.get("/configuracion")
def configuracion():
    return estado(activo())


@app.put("/configuracion")
def configurar(config: Configuracion):
    with configuration_lock:
        try:
            candidate = Predictor(config)
            candidate.revision = uuid4().hex
            temporary = CONFIG_FILE.with_suffix(".tmp")
            temporary.write_text(config.model_dump_json(indent=2) + "\n", encoding="utf-8")
            temporary.replace(CONFIG_FILE)
        except (ErrorPrediccion, OSError) as exc:
            raise HTTPException(422, str(exc)) from exc
        app.state.predictor = candidate
        app.state.error_carga = None
    return estado(candidate)


def ejecutar(request, revision):
    try:
        return activo(revision).predecir([request.cliente], (request.modelo,))[request.modelo][0]
    except ErrorPrediccion as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/predict/churn", response_model=Prediccion)
def churn(request: Peticion, revision: Revision = None):
    return ejecutar(request, revision)


@app.post("/predict/risk_score", response_model=Prediccion)
def risk_score(request: Peticion, revision: Revision = None):
    return ejecutar(request, revision)


@app.post("/predict/batch", response_model=RespuestaLote)
def batch(request: Lote, revision: Revision = None):
    try:
        return activo(revision).predecir(request.clientes)
    except ErrorPrediccion as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/evaluate")
def evaluate(request: Evaluacion, revision: Revision = None):
    predictor = activo(revision)
    try:
        results = predictor.predecir(request.clientes)
    except ErrorPrediccion as exc:
        raise HTTPException(422, str(exc)) from exc
    return metricas(results, request.etiquetas, request.conjunto, predictor)


def tabla_respuesta(frame, fuente, objetivo):
    validar_tabla(frame, objetivo=objetivo)
    return {"fuente": fuente, "columnas": list(frame.columns), "filas": frame.to_dict("records")}


@app.get("/data/{conjunto}")
def datos(conjunto: Literal["validation", "exploration"]):
    path = ROOT / ("data/partitions/validation_set.parquet" if conjunto == "validation"
                   else "data/processed/Proyecto_B_Clientes_Limpio.parquet")
    try:
        processor = cargar_archivo(path, "datos")
        return tabla_respuesta(processor.data, path.name, True)
    except FileNotFoundError as exc:
        raise HTTPException(404, f"No existe el dataset {path.name} en el servidor.") from exc
    except (ValueError, OSError) as exc:
        raise HTTPException(422, f"Dataset no válido: {exc}") from exc


def validar_artefacto(obj, tipo):
    if tipo == "scaler":
        import numpy as np
        from sklearn.preprocessing import MinMaxScaler
        from sklearn.utils.validation import check_is_fitted
        scaler = obj.scaler
        if not isinstance(scaler, MinMaxScaler):
            raise ValueError("Se requiere un MinMaxScaler entrenado.")
        check_is_fitted(scaler)
        if list(getattr(scaler, "feature_names_in_", [])) != COLUMNAS or scaler.n_features_in_ != 20:
            raise ValueError("El scaler no coincide con las 20 columnas y su orden.")
        if not np.isfinite(scaler.scale_).all():
            raise ValueError("El scaler tiene parámetros inválidos.")
    else:
        model = obj.model
        if model.input_shape != (None, 20) or model.output_shape != (None, 1):
            raise ValueError("El modelo debe recibir 20 variables y devolver una probabilidad.")
        if getattr(getattr(model.layers[-1], "activation", None), "__name__", "") != "sigmoid":
            raise ValueError("La salida debe usar sigmoid.")


@app.post("/files/{tipo}", status_code=201)
async def subir(tipo: Literal["modelo", "scaler", "datos"], nombre: str, request: Request,
                uso: Literal["prediccion", "evaluacion", "exploracion", "preparacion"] = "prediccion"):
    # Cuerpo binario: evita depender de multipart. Los datos se leen en temporales.
    if (not nombre or Path(nombre).name != nombre or "/" in nombre or "\\" in nombre
            or ":" in nombre or Path(nombre).suffix not in EXTENSIONES[tipo]
            or nombre in {"columnas.pkl"}):
        raise HTTPException(422, "Nombre o formato incompatible con el tipo de carga.")
    limit = 20 * 1024 * 1024 if tipo == "datos" else 100 * 1024 * 1024
    with TemporaryDirectory(prefix="telco-carga-") as directory:
        temporary = Path(directory) / nombre
        size = 0
        with temporary.open("wb") as stream:
            async for chunk in request.stream():
                size += len(chunk)
                if size > limit:
                    raise HTTPException(413, "El archivo supera el límite de carga.")
                stream.write(chunk)
        if not size:
            raise HTTPException(422, "El archivo está vacío.")
        try:
            obj = await run_in_threadpool(cargar_archivo, temporary, tipo)
            if tipo == "datos":
                if uso == "preparacion":
                    from api.datasets import vista_previa
                    return vista_previa(obj.data, nombre)
                return tabla_respuesta(obj.data, nombre, uso != "prediccion")
            await run_in_threadpool(validar_artefacto, obj, tipo)
            # Nunca sobrescribir un artefacto del usuario o que esté activo.
            target = MODELS / nombre
            try:
                with target.open("xb") as output, temporary.open("rb") as source:
                    import shutil
                    shutil.copyfileobj(source, output)
            except FileExistsError as exc:
                raise HTTPException(409, "Ya existe un archivo con ese nombre. Selecciónelo o use otro nombre.") from exc
            return {"archivo": nombre, "tipo": tipo, "cargado": True}
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(422, f"No se pudo cargar {tipo}: {type(exc).__name__}: {exc}") from exc



@app.post("/datasets/prepare")
def preparar_dataset(request: Preparacion, revision: Revision = None):
    from api.datasets import preparar
    try:
        return preparar(request, activo(revision))
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, str(exc)) from exc


def inferir_dataset(request, revision):
    import pandas as pd
    from api.datasets import matriz_entrada
    predictor = activo(revision)
    if request.revision_preparacion != predictor.revision:
        raise HTTPException(409, "Cambió la configuración. Prepara de nuevo el dataset en Análisis de lotes.")
    try:
        _, scaled = matriz_entrada(pd.DataFrame(request.entrada), predictor, request.aplicar_scaler)
        return predictor, predictor.predecir_matriz(scaled)
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, str(exc)) from exc


@app.post("/datasets/predict", response_model=RespuestaLote)
def predecir_dataset(request: DatasetInferencia, revision: Revision = None):
    _, results = inferir_dataset(request, revision)
    return results


@app.post("/datasets/evaluate")
def evaluar_dataset(request: DatasetInferencia, revision: Revision = None):
    if request.etiquetas is None:
        raise HTTPException(422, "El dataset no tiene objetivo. Mapéalo en Análisis de lotes para evaluar.")
    predictor, results = inferir_dataset(request, revision)
    return metricas(results, request.etiquetas, request.conjunto, predictor)
