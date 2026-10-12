# ESTADO_ARCHIVO: EN_MODIFICACION
"""Extiende Binary_Model para inferencia con escalado y umbral controlados por la API."""
from tensorflow.keras.models import load_model
from src.Modelo_ANN import Binary_Model


class ModeloInferencia(Binary_Model):
    def __init__(self):
        super().__init__(None, None, None, None, None, [])

    def cargar_modelo(self, path):
        # Usa la propiedad model heredada. No requiere recrear la arquitectura.
        self.model = load_model(path, compile=False, safe_mode=True)
        return self

    def __call__(self, data, training=False):
        # Predictor ya validó y escaló. El make_prediction original volvería a
        # escalar y aplicaría un umbral fijo; aquí se conserva P(Abandono=1).
        return self.model(data, training=training)
