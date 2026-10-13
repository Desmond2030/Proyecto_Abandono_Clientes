# ESTADO_ARCHIVO: EN_MODIFICACION
"""Pruebas de preparación, correspondencia y prevención del doble escalado."""
import asyncio
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from pydantic import ValidationError

from api.datasets import preparar, matriz_entrada
from api.main import app
from api.schemas import COLUMNAS, Preparacion, DatasetInferencia
from api.test_predict import ejemplo, predictor_falso, request


class DatasetTests(unittest.TestCase):
    def setUp(self):
        self.predictor = predictor_falso()
        app.state.predictor = self.predictor
        self.row = ejemplo()

    def tearDown(self):
        app.state.predictor = None

    def recipe(self, **changes):
        base = dict(fuente="Datos sintéticos", filas=[self.row], entradas={c: c for c in COLUMNAS}, aplicar_scaler=True)
        base.update(changes)
        return Preparacion.model_validate(base)

    def test_preview_accepts_extra_columns_and_missing_values(self):
        blob = b"otro_nombre,extra,objetivo\n12,abc,Yes\n,def,No\n"
        code, data = asyncio.run(request("POST", "/files/datos", binary=blob,
                                        query=b"nombre=origen.csv&uso=preparacion"))
        self.assertEqual(code, 201, data)
        self.assertEqual(data["columnas"], ["otro_nombre", "extra", "objetivo"])
        self.assertIsNone(data["filas"][1]["otro_nombre"])

    def test_drop_rename_map_target_and_keep_row_identity(self):
        rows = [{**self.row, "Cargos": 40 + i, "Clase": label, "ID": "ficticio"}
                for i, label in enumerate(["Yes", "No", "Yes"])]
        for row in rows:
            del row["Cargos_Mensuales"]
        mapping = {c: c for c in COLUMNAS}; mapping["Cargos_Mensuales"] = "Cargos"
        data = preparar(self.recipe(filas=rows, entradas=mapping, eliminar_columnas=["ID"],
                                    eliminar_filas=[2], objetivo="Clase", valores_objetivo={"Yes": 1, "No": 0}), self.predictor)
        self.assertEqual(data["filas_origen"], [1, 3])
        self.assertEqual([r["Abandono"] for r in data["filas"]], [1, 1])
        self.assertEqual(set(data["entrada"][0]), set(COLUMNAS))
        self.assertNotIn("ID", data["filas"][0])

    def test_null_rows_only_removed_when_requested(self):
        rows = [self.row, {**self.row, "Cargos_Mensuales": None}]
        with self.assertRaises(ValueError):
            preparar(self.recipe(filas=rows), self.predictor)
        data = preparar(self.recipe(filas=rows, eliminar_nulos=True), self.predictor)
        self.assertEqual(data["filas_origen"], [1])
        self.assertEqual(data["eliminadas"], 1)

    def test_category_mapping_and_unknown_values(self):
        recipe = self.recipe(filas=[{**self.row, "Pareja": "Yes"}], valores={"Pareja": {"Yes": 1, "No": 0}})
        self.assertEqual(preparar(recipe, self.predictor)["entrada"][0]["Pareja"], 1)
        recipe.valores["Pareja"] = {"No": 0}
        with self.assertRaisesRegex(ValueError, "no cubre"):
            preparar(recipe, self.predictor)

    def test_target_leakage_missing_mapping_and_removed_input_rejected(self):
        for recipe in [self.recipe(objetivo="Pareja"), self.recipe(eliminar_columnas=["Pareja"]),
                       self.recipe(entradas={c: c for c in COLUMNAS if c != "Pareja"})]:
            with self.subTest(recipe=recipe.entradas), self.assertRaises(ValueError):
                preparar(recipe, self.predictor)

    def test_skip_scaler_preserves_exact_model_input(self):
        row = {**self.row, "Contrato": 1}
        original = pd.DataFrame([row], columns=COLUMNAS)
        scaled = self.predictor.scaler.transform(original).astype("float32")
        request_data = self.recipe(filas=pd.DataFrame(scaled, columns=COLUMNAS).to_dict("records"), aplicar_scaler=False)
        with patch.object(self.predictor.scaler, "transform", side_effect=AssertionError("Doble escalado")):
            data = preparar(request_data, self.predictor)
            _, actual = matriz_entrada(pd.DataFrame(data["entrada"]), self.predictor, False)
            self.predictor.predecir_matriz(actual)
        np.testing.assert_allclose(self.predictor.models["modelo_1"].received, scaled)
        self.assertEqual(data["filas"][0]["Contrato"], 1)
        self.assertAlmostEqual(data["filas"][0]["Cargos_Mensuales"], row["Cargos_Mensuales"], places=4)

    def test_unscaled_and_invalid_categories_cannot_skip_scaler(self):
        with self.assertRaisesRegex(ValueError, "ya escaladas"):
            preparar(self.recipe(aplicar_scaler=False), self.predictor)
        scaled = self.predictor.scaler.transform(pd.DataFrame([self.row], columns=COLUMNAS))
        scaled[0, COLUMNAS.index("Contrato")] = .3
        with self.assertRaisesRegex(ValueError, "categoría"):
            preparar(self.recipe(filas=pd.DataFrame(scaled, columns=COLUMNAS).to_dict("records"), aplicar_scaler=False), self.predictor)

    def test_dataset_api_predict_evaluate_and_revision(self):
        code, data = asyncio.run(request("POST", "/datasets/prepare", self.recipe(
            filas=[{**self.row, "Clase": "Yes"}], objetivo="Clase", valores_objetivo={"Yes": 1}).model_dump()))
        self.assertEqual(code, 200, data)
        payload = {key: data[key] for key in ["entrada", "aplicar_scaler", "revision_preparacion"]}
        payload.update(conjunto="Prueba", etiquetas=[1])
        for endpoint in ["predict", "evaluate"]:
            code, result = asyncio.run(request("POST", "/datasets/" + endpoint, payload))
            self.assertEqual(code, 200, result)
        payload["revision_preparacion"] = "anterior"
        code, _ = asyncio.run(request("POST", "/datasets/predict", payload))
        self.assertEqual(code, 409)

    def test_no_target_evaluation_and_extra_predictors_rejected(self):
        payload = dict(entrada=[self.row], aplicar_scaler=True, revision_preparacion=self.predictor.revision, conjunto="Prueba")
        code, _ = asyncio.run(request("POST", "/datasets/evaluate", payload))
        self.assertEqual(code, 422)
        payload["entrada"][0] = {**self.row, "Abandono": 1}
        with self.assertRaises(ValidationError):
            DatasetInferencia.model_validate(payload)


if __name__ == "__main__":
    unittest.main()
