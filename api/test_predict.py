# ESTADO_ARCHIVO: EN_MODIFICACION
"""Comprobaciones con datos sintéticos: python -m unittest api.test_predict -v."""
import asyncio
import json
import tempfile
import pickle
import unittest
from pathlib import Path
from threading import RLock
from unittest.mock import patch

import numpy as np
import pandas as pd
import joblib
from pydantic import ValidationError
from sklearn.preprocessing import MinMaxScaler

from api.main import app
from api.predict import ErrorPrediccion, Predictor, archivo_local, validar_tabla
from api.schemas import COLUMNAS, Cliente, Configuracion


def ejemplo():
    row = dict.fromkeys(COLUMNAS, 0)
    row.update({"Antiguedad(Meses)": 12, "Servicio_Telefono": 1,
                "Internet_DSL": 1, "Cargos_Mensuales": 50})
    return row


class ModeloFalso:
    def __init__(self, probability):
        self.probability = probability
        self.received = None

    def __call__(self, values, training=False):
        self.received = values.copy()
        return np.full((len(values), 1), self.probability)


def predictor_falso():
    p = Predictor.__new__(Predictor)
    low, high = dict.fromkeys(COLUMNAS, 0), dict.fromkeys(COLUMNAS, 1)
    low["Cargos_Mensuales"] = 10
    high.update({"Antiguedad(Meses)": 100, "Cargos_Mensuales": 110, "Contrato": 2})
    p.scaler = MinMaxScaler().fit(pd.DataFrame([low, high], columns=COLUMNAS))
    p.config = Configuracion(modelo_1="a.keras", modelo_2="b.keras", scaler="scaler.pkl", umbral=.5, riesgo_medio=.35, riesgo_alto=.65)
    p.models = {"modelo_1": ModeloFalso(.8), "modelo_2": ModeloFalso(.2)}
    p.revision = "test-revision"
    p.lock = RLock()
    return p


async def request(method, path, body=None, headers=None, query=b"", binary=None):
    messages = []
    payload = binary if binary is not None else json.dumps(body).encode() if body is not None else b""
    async def receive():
        return {"type": "http.request", "body": payload, "more_body": False}
    async def send(message):
        messages.append(message)
    await app({"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
               "method": method, "scheme": "http", "path": path, "raw_path": path.encode(),
               "query_string": query, "root_path": "", "headers": headers or [(b"content-type", b"application/json")],
               "client": ("127.0.0.1", 1), "server": ("127.0.0.1", 8000)}, receive, send)
    status = next(m["status"] for m in messages if m["type"] == "http.response.start")
    data = json.loads(b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body"))
    return status, data


class InferenciaTests(unittest.TestCase):
    def setUp(self):
        self.p = predictor_falso()
        self.row = ejemplo()
        app.state.predictor = self.p

    def tearDown(self):
        app.state.predictor = None

    def test_escala_y_orden_antes_de_ambos_modelos(self):
        frame = pd.DataFrame([self.row])[list(reversed(COLUMNAS))]
        result = self.p.predecir(validar_tabla(frame))
        received = self.p.models["modelo_1"].received
        self.assertEqual(received.shape, (1, 20))
        self.assertAlmostEqual(float(received[0, 3]), .12, places=6)
        self.assertAlmostEqual(float(received[0, -1]), .4, places=6)
        np.testing.assert_array_equal(received, self.p.models["modelo_2"].received)
        self.assertEqual(result["modelo_1"][0].abandono, "Yes")
        self.assertEqual(result["modelo_2"][0].abandono, "No")
        self.assertEqual(result["modelo_1"][0].riesgo, "Alto")

    def test_no_fit_durante_inferencia(self):
        with patch.object(self.p.scaler, "fit", side_effect=AssertionError("No ajustar")):
            self.p.predecir([Cliente.model_validate(self.row)])

    def test_rechaza_columnas_extra_faltantes_duplicadas(self):
        frames = [pd.DataFrame([{**self.row, "Abandono": 1}]),
                  pd.DataFrame([self.row]).drop(columns="Pareja")]
        duplicate = pd.DataFrame([self.row])
        duplicate.columns = ["Pareja"] + list(duplicate.columns[1:])
        frames.append(duplicate)
        for frame in frames:
            with self.subTest(columns=list(frame.columns)), self.assertRaises(ErrorPrediccion):
                validar_tabla(frame)

    def test_rechaza_nan_infinito_y_fuera_de_rango(self):
        for value in [float("nan"), float("inf"), -1]:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                Cliente.model_validate({**self.row, "Cargos_Mensuales": value})
        with self.assertRaises(ErrorPrediccion):
            self.p.predecir([Cliente.model_validate({**self.row, "Cargos_Mensuales": 1000})])

    def test_rechaza_servicios_imposibles(self):
        for change in [{"Internet_Fiber optic": 1}, {"Servicio_Telefono": 0, "Lineas_Multiples": 1},
                       {"Internet_DSL": 0, "Streaming_TV": 1},
                       {"MP_Mailed check": 1, "MP_Electronic check": 1}]:
            with self.subTest(change=change), self.assertRaises(ValidationError):
                Cliente.model_validate({**self.row, **change})

    def test_rechaza_probabilidades_invalidas(self):
        for value in [float("nan"), -0.1, 1.1]:
            self.p.models["modelo_1"] = ModeloFalso(value)
            with self.assertRaises(ErrorPrediccion):
                self.p.predecir([Cliente.model_validate(self.row)])

    def test_limites_inclusivos(self):
        self.assertEqual(self.p.resultado("modelo_1", .5).abandono, "Yes")
        self.assertEqual(self.p.resultado("modelo_1", .35).riesgo, "Medio")
        self.assertEqual(self.p.resultado("modelo_1", .65).riesgo, "Alto")

    def test_porcentaje_y_riesgo_usando_probabilidad_propia(self):
        self.p.config.umbral = .3
        self.p.config.riesgo_medio = .5
        self.p.config.riesgo_alto = .8
        self.p.models["modelo_1"] = ModeloFalso(.29)
        self.p.models["modelo_2"] = ModeloFalso(.323)
        code, result = asyncio.run(request("POST", "/predict/batch", {"clientes": [self.row]}))
        self.assertEqual(code, 200)
        self.assertEqual(result["modelo_1"][0]["abandono"], "No")
        self.assertEqual(result["modelo_2"][0]["abandono"], "Yes")
        self.assertEqual(result["modelo_2"][0]["riesgo"], "Bajo")
        self.assertAlmostEqual(result["modelo_2"][0]["probabilidad"] * 100, 32.3)
        for slot in ("modelo_1", "modelo_2"):
            for p, clase, riesgo in [(0, "No", "Bajo"), (.299999, "No", "Bajo"),
                    (.3, "Yes", "Bajo"), (.499999, "Yes", "Bajo"), (.5, "Yes", "Medio"),
                    (.799999, "Yes", "Medio"), (.8, "Yes", "Alto"), (1, "Yes", "Alto")]:
                with self.subTest(modelo=slot, probabilidad=p):
                    prediction = self.p.resultado(slot, p)
                    self.assertEqual(prediction.abandono, clase)
                    self.assertEqual(prediction.riesgo, riesgo)

    def test_rutas_fuera_de_models(self):
        with tempfile.TemporaryDirectory() as folder:
            for name in ["../a.keras", "sub/a.keras", "/a.keras"]:
                with self.subTest(name=name), self.assertRaises(ErrorPrediccion):
                    archivo_local(Path(folder), name, {".keras"})

    def test_scaler_sin_nombres_o_con_orden_incorrecto(self):
        variants = [MinMaxScaler().fit(np.zeros((2, 20))),
                    MinMaxScaler().fit(pd.DataFrame(np.zeros((2, 20)), columns=list(reversed(COLUMNAS)))),
                    MinMaxScaler().fit(pd.DataFrame(np.zeros((2, 19)), columns=COLUMNAS[:-1]))]
        with tempfile.TemporaryDirectory() as folder:
            for scaler in variants:
                (Path(folder) / "scaler.pkl").write_bytes(pickle.dumps(scaler))
                with self.assertRaisesRegex(ErrorPrediccion, "20 columnas"):
                    Predictor(self.p.config, folder)

    def test_columnas_guardadas_incompatibles(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "scaler.pkl").write_bytes(pickle.dumps(self.p.scaler))
            joblib.dump(list(reversed(COLUMNAS)), Path(folder) / "columnas.pkl")
            with self.assertRaisesRegex(ErrorPrediccion, "columnas.pkl"):
                Predictor(self.p.config, folder)

    def test_api_predicciones_lotes_y_validacion(self):
        for endpoint in ["churn", "risk_score"]:
            code, data = asyncio.run(request("POST", f"/predict/{endpoint}", {"cliente": self.row, "modelo": "modelo_2"}))
            self.assertEqual(code, 200)
            self.assertEqual(data["abandono"], "No")
        code, data = asyncio.run(request("POST", "/predict/batch", {"clientes": [self.row, self.row]}))
        self.assertEqual(code, 200)
        self.assertEqual(len(data["modelo_1"]), 2)
        code, _ = asyncio.run(request("POST", "/predict/churn", {"cliente": {**self.row, "ID_Cliente": "ficticio"}}))
        self.assertEqual(code, 422)
        code, _ = asyncio.run(request("POST", "/predict/batch", {"clientes": []}))
        self.assertEqual(code, 422)

    def test_api_sin_configuracion(self):
        app.state.predictor = None
        code, _ = asyncio.run(request("POST", "/predict/churn", {"cliente": self.row}))
        self.assertEqual(code, 409)

    def test_carga_fallida_conserva_modelos(self):
        with patch("api.main.Predictor", side_effect=ErrorPrediccion("Incompatible")):
            code, _ = asyncio.run(request("PUT", "/configuracion", self.p.config.model_dump()))
        self.assertEqual(code, 422)
        self.assertIs(app.state.predictor, self.p)

    def test_revision_antigua_no_predice_con_otro_modelo(self):
        code, _ = asyncio.run(request("POST", "/predict/batch", {"clientes": [self.row]},
                                      headers=[(b"content-type", b"application/json"),
                                               (b"x-configuration-id", b"revision-antigua")]))
        self.assertEqual(code, 409)

    def test_evaluacion_valida_y_desalineada(self):
        code, data = asyncio.run(request("POST", "/evaluate", {"clientes": [self.row, self.row],
                                       "etiquetas": [0, 1], "conjunto": "Prueba sintética"}))
        self.assertEqual(code, 200)
        self.assertEqual(len(data["metricas"]), 2)
        self.assertEqual(data["matrices"]["modelo_1"], [[0, 1], [0, 1]])
        code, _ = asyncio.run(request("POST", "/evaluate", {"clientes": [self.row],
                                    "etiquetas": [0, 1], "conjunto": "Prueba sintética"}))
        self.assertEqual(code, 422)

    def test_configuracion_no_inventa_umbrales(self):
        config = self.p.config.model_dump()
        del config["riesgo_medio"]
        code, _ = asyncio.run(request("PUT", "/configuracion", config))
        self.assertEqual(code, 422)

    def test_carga_datos_csv_xlsx_parquet_y_metodo_src(self):
        from api.loaders import cargar_archivo
        from src.Data_Processor import DataProcessor
        frame = pd.DataFrame([self.row])
        with tempfile.TemporaryDirectory() as folder:
            for suffix in ["csv", "xlsx", "parquet"]:
                path = Path(folder) / f"clientes.{suffix}"
                processor = DataProcessor()
                processor.data = frame
                processor.save_data(str(path), index=False)
                loaded = cargar_archivo(path, "datos")
                self.assertIsInstance(loaded, DataProcessor)
                self.assertEqual(len(validar_tabla(loaded.data)), 1)
                code, data = asyncio.run(request("POST", "/files/datos", binary=path.read_bytes(),
                                         query=f"nombre=clientes.{suffix}&uso=prediccion".encode()))
                self.assertEqual(code, 201, data)
                self.assertEqual(len(data["filas"]), 1)

    def test_cargas_rechazan_tipo_duplicados_y_rutas(self):
        for name, body in [("../clientes.csv", b"a\n1"), ("clientes.keras", b"x"),
                           ("clientes.csv", b"Pareja,Pareja\n0,0")]:
            code, _ = asyncio.run(request("POST", "/files/datos", binary=body,
                                          query=f"nombre={name}&uso=prediccion".encode()))
            self.assertEqual(code, 422)

    def test_subida_scaler_no_sobrescribe(self):
        with tempfile.TemporaryDirectory() as folder, patch("api.main.MODELS", Path(folder)):
            blob = pickle.dumps(self.p.scaler)
            code, _ = asyncio.run(request("POST", "/files/scaler", binary=blob, query=b"nombre=scaler.pkl"))
            self.assertEqual(code, 201)
            code, _ = asyncio.run(request("POST", "/files/scaler", binary=blob, query=b"nombre=scaler.pkl"))
            self.assertEqual(code, 409)
            self.assertEqual((Path(folder) / "scaler.pkl").read_bytes(), blob)

    def test_persistencia_configuracion(self):
        with tempfile.TemporaryDirectory() as folder, patch("api.main.CONFIG_FILE", Path(folder) / "config.json"), \
                patch("api.main.Predictor", return_value=self.p):
            code, data = asyncio.run(request("PUT", "/configuracion", self.p.config.model_dump()))
            self.assertEqual(code, 200)
            saved = Configuracion.model_validate_json((Path(folder) / "config.json").read_text())
            self.assertEqual(saved, self.p.config)
            self.assertIn("revision", data)


if __name__ == "__main__":
    unittest.main()
