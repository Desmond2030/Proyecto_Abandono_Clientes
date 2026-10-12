# ESTADO_ARCHIVO: EN_MODIFICACION
import io
import unittest
import zipfile
import numpy as np
from api.datasets import preparar
from api.evaluation import metricas
from api.schemas import Cliente, COLUMNAS, Preparacion
from api.test_predict import ejemplo, predictor_falso
from app.results import tabla_predicciones, archivo_metricas


class EvaluacionExportacionTests(unittest.TestCase):
    def setUp(self):
        self.p = predictor_falso()
        self.clients = [Cliente.model_validate(ejemplo())] * 2
        self.results = self.p.predecir(self.clients)

    def test_errors_follow_class_for_model1_and_probability_for_model2(self):
        result = metricas(self.results, [0, 1], "Prueba", self.p)
        first, second = result["metricas"]
        self.assertAlmostEqual(first["MAE"], .5)
        self.assertAlmostEqual(first["RMSE"], np.sqrt(.5))
        self.assertAlmostEqual(second["MAE"], .5)
        self.assertAlmostEqual(second["RMSE"], np.sqrt(.34))
        self.assertEqual(second["MAE / media"], 1)
        self.assertEqual(result["clientes"][0]["modelo_1_clase"], 1)
        self.assertEqual(result["clientes"][0]["modelo_2_probabilidad"], .2)
        self.assertEqual(result["reportes"]["modelo_1"]["Abandona (1)"]["support"], 1)

    def test_zero_denominators_and_missing_class_are_explicit(self):
        result = metricas(self.results, [0, 0], "Prueba", self.p)
        for row in result["metricas"]:
            self.assertIsNone(row["MAE / media"])
            self.assertIsNone(row["MAE / mediana"])
            self.assertIsNone(row["ROC AUC"])
        self.assertEqual(result["matrices"]["modelo_1"], [[0, 2], [0, 0]])

    def test_export_retains_source_columns_alignment_and_collisions(self):
        rows = [{**ejemplo(), "Cliente": f"ficticio-{i}", "Nota": "conservar",
                 "Eliminar": 999, "Prediccion_Abandono_Modelo_1": -1} for i in range(3)]
        recipe = Preparacion(fuente="Prueba", filas=rows, entradas={c: c for c in COLUMNAS},
                             eliminar_filas=[2], eliminar_columnas=["Eliminar"], aplicar_scaler=True)
        payload = preparar(recipe, self.p)
        output = tabla_predicciones(payload, self.results)
        self.assertEqual(output.Cliente.tolist(), ["ficticio-0", "ficticio-2"])
        self.assertEqual(output.Fila_origen.tolist(), [1, 3])
        self.assertNotIn("Eliminar", output)
        self.assertEqual(output.Nota.tolist(), ["conservar"] * 2)
        self.assertEqual(output.Prediccion_Abandono_Modelo_1.tolist(), [-1, -1])
        self.assertEqual(output.Prediccion_Abandono_Modelo_1_2.tolist(), [1, 1])
        self.assertEqual(output.Probabilidad_Abandono_Modelo_2.tolist(), [.2, .2])

    def test_metrics_download_contains_only_evaluation_results(self):
        result = metricas(self.results, [0, 1], "Prueba", self.p)
        with zipfile.ZipFile(io.BytesIO(archivo_metricas(result))) as archive:
            self.assertEqual(len(archive.namelist()), 5)
            self.assertIn("modelo_1_reporte.csv", archive.namelist())
            self.assertTrue(all("clientes" not in name and "predicciones" not in name for name in archive.namelist()))


if __name__ == "__main__":
    unittest.main()
