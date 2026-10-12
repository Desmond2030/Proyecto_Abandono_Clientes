# ESTADO_ARCHIVO: EN_MODIFICACION
"""Cliente HTTP: Streamlit no carga redes ni ejecuta inferencia local."""
import os
import requests
from api.schemas import Configuracion, Prediccion


class ErrorAPI(ValueError):
    pass


class ApiClient:
    def __init__(self, url=None):
        self.url = (url or os.environ.get("TELCO_API_URL", "http://127.0.0.1:8000")).rstrip("/")
        self.config = None
        self.revision = None

    def request(self, method, path, payload=None, *, timeout=30, revision=False, binary=None, params=None):
        headers = {"X-Configuration-Id": self.revision} if revision and self.revision else {}
        if binary is not None:
            headers["Content-Type"] = "application/octet-stream"
        try:
            with requests.Session() as session:
                session.trust_env = False
                response = session.request(method, self.url + path, json=payload, data=binary,
                                           params=params, headers=headers, timeout=(5, timeout))
        except requests.Timeout as exc:
            raise ErrorAPI("La API no respondió a tiempo. Actualiza su estado antes de reintentar la carga.") from exc
        except requests.RequestException as exc:
            raise ErrorAPI(f"No hay conexión con la API en {self.url}. Inicia ambos servicios con python app/run.py.") from exc
        try:
            data = response.json()
        except ValueError as exc:
            raise ErrorAPI("El servidor no devolvió una respuesta JSON válida de Telco.") from exc
        if not response.ok:
            detail = data.get("detail", "Error del servidor")
            if isinstance(detail, list):
                detail = "; ".join(f"{'.'.join(map(str, e.get('loc', [])))}: {e.get('msg', '')}" for e in detail)
            raise ErrorAPI(f"API {response.status_code}: {detail}")
        return data

    def salud(self):
        data = self.request("GET", "/health", timeout=10)
        if data.get("servicio") != "telco-churn" or data.get("version") != "0.4.0":
            raise ErrorAPI("El puerto responde, pero no corresponde a esta versión de la API Telco.")
        return data

    def inventario(self):
        return self.request("GET", "/artefactos")

    def cargar_estado(self):
        data = self.request("GET", "/configuracion")
        self.revision = data.pop("revision")
        self.config = Configuracion.model_validate(data)
        return self

    def configurar(self, config):
        data = self.request("PUT", "/configuracion", config.model_dump(), timeout=180)
        self.revision = data.pop("revision")
        self.config = Configuracion.model_validate(data)

    def predecir(self, clients, *, individual=False):
        rows = [client.model_dump(by_alias=True) for client in clients]
        if individual:
            result = {}
            for slot, endpoint in [("modelo_1", "churn"), ("modelo_2", "risk_score")]:
                data = self.request("POST", f"/predict/{endpoint}",
                                    {"cliente": rows[0], "modelo": slot}, revision=True)
                result[slot] = [Prediccion.model_validate(data)]
            return result
        data = self.request("POST", "/predict/batch", {"clientes": rows}, timeout=180, revision=True)
        return {slot: [Prediccion.model_validate(p) for p in predictions] for slot, predictions in data.items()}

    def evaluar(self, clients, labels, name):
        return self.request("POST", "/evaluate", {"clientes": [c.model_dump(by_alias=True) for c in clients],
                            "etiquetas": labels, "conjunto": name}, timeout=180, revision=True)

    def datos(self, kind):
        return self.request("GET", f"/data/{kind}")

    def subir(self, file, tipo, uso="prediccion"):
        return self.request("POST", f"/files/{tipo}", binary=file.getvalue(),
                            params={"nombre": file.name, "uso": uso}, timeout=180)


    def preparar(self, recipe):
        return self.request("POST", "/datasets/prepare", recipe, timeout=180, revision=True)

    def dataset_request(self, dataset, *, evaluar=False):
        payload = {key: dataset[key] for key in ("entrada", "aplicar_scaler", "revision_preparacion")}
        payload["conjunto"] = dataset["fuente"]
        if "Abandono" in dataset["columnas"]:
            payload["etiquetas"] = [row["Abandono"] for row in dataset["filas"]]
        result = self.request("POST", "/datasets/evaluate" if evaluar else "/datasets/predict",
                              payload, timeout=180, revision=True)
        if evaluar:
            return result
        return {slot: [Prediccion.model_validate(p) for p in values] for slot, values in result.items()}
