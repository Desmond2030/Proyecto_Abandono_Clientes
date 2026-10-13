# Proyecto B: Sistema de Predicción de Abandono de Clientes (Churn)

**Curso:** BD-151 Inteligencia Artificial Aplicada – Colegio Universitario de Cartago
**Profesor:** Osvaldo González Chaves
**Año:** 2026

## Integrantes

| Nombre | Carné | Correo |
|---|---|---|
|Desmond Akin Bermúdez Rodríguez |305270891 |305270891@cuc.cr |

## Descripción del problema

Sistema que predice qué clientes tienen mayor probabilidad de abandonar un servicio de telecomunicaciones. Identifica clientes en riesgo y los clasifica por nivel de urgencia para implementar estrategias de retención.

## Dataset

- **Nombre:** Telco Customer Churn (Kaggle)
- **URL:** https://www.kaggle.com/datasets/blastchar/telco-customer-churn
- **Registros:** 7,043 clientes
- **Variables:** 21 (demográficas, servicios contratados, información de cuenta)

Colocar los archivos originales en `data/raw/` sin modificarlos.

## Modelos

- **Modelo 1 – Clasificación Binaria:** Predecir si el cliente abandonará o no (Churn Yes/No)
- **Modelo 2 – Scoring de Riesgo:** Estimar la probabilidad de churn (0.0 a 1.0) con una arquitectura distinta a la del Modelo 1 y clasificar por nivel de riesgo según umbrales justificados por el grupo

Lineamientos de entrenamiento:

- Normalización con `MinMaxScaler` ajustado solo sobre el conjunto de entrenamiento.
- Variables categóricas con `pd.get_dummies`; guardar la lista de columnas resultante en `models/columnas.pkl`.
- Entrenamiento con `validation_split` y `EarlyStopping`; el conjunto de prueba se usa solo para la evaluación final.
- Comparar al menos dos configuraciones por modelo (por ejemplo, con y sin `Dropout`).

## API REST

| Método | Endpoint | Respuesta |
|---|---|---|
| POST | `/predict/churn` | Churn Yes/No |
| POST | `/predict/risk_score` | Probabilidad de churn y nivel de riesgo |

La documentación automática queda disponible en `http://localhost:8000/docs`.

## Estructura del proyecto

```
Proyecto_B_Abandono_Clientes/
│
├── README.md                      ← Guía completa de instalación y uso del proyecto
├── requirements.txt               ← Dependencias Python
├── .gitignore                     ← Archivos excluidos del control de versiones
├── .vscode                        ← Para archivo de configuracion de VSCode
├── USO_DE_IA.md                   ← Para documentar el uso de herramientas de AI generativa en el proyecto
│
├── data/
│   ├── raw/                       ← Datos originales sin procesar
|   | └── docs/                    ← Carpeta para albergar documentacion sobre los datos originales
|   |
│   ├── processed/                 ← Datos originales sin procesar
|   | └── Proyecto_B_Clientes_Limpio.parquet     ← Datos limpios y preprocesados para EDA
|   |
│   └── partitions/                 ← Datos limpios, preprocesados y particionados
│       ├── train.csv              ← Conjunto de entrenamiento
│       └── test.csv               ← Conjunto de prueba
│
├── notebooks/
│   ├── 01_EDA.ipynb               ← Análisis Exploratorio de Datos
│   ├── 02_Preprocesamiento.ipynb  ← Limpieza, variables dummy, normalización
│   ├── 03_ANN_Modelo1.ipynb       ← Entrenamiento del Modelo 1
│   ├── 04_ANN_Modelo2.ipynb       ← Entrenamiento del Modelo 2
│   └── 05_Comparacion_Modelos.ipynb ← Evaluación y selección del mejor modelo
│
├── src/
│   ├── __init__.py
│   ├── config.py                  ← Configuraciones globales (rutas, parámetros)
│   ├── data_prep.py               ← Funciones de preprocesamiento
│   └── train/
│       ├── __init__.py
│       ├── model1.py              ← Entrenamiento del Modelo 1
│       ├── model2.py              ← Entrenamiento del Modelo 2
│       └── utils.py               ← Utilidades compartidas (métricas, gráficas)
│
├── Proyect_Context/
│   ├── About_Folder.md            ← Indicaciones de la carpeta para Agentes  
│   └── General_Context_File.md    ← Historial compartido sobre la evolucion del proyecto
│
│
├── models/
│   ├── model1.keras               ← Modelo 1 guardado (formato Keras)
│   ├── model2.keras               ← Modelo 2 guardado (formato Keras)
│   ├── scaler.pkl                 ← MinMaxScaler entrenado
│   └── columnas.pkl               ← Columnas finales tras get_dummies
│
├── api/
│   ├── main.py                    ← Aplicación FastAPI con endpoints
│   ├── schemas.py                 ← Modelos Pydantic para validación
│   └── predict.py                 ← Lógica de predicción e inferencia
│
└── app/
    ├── Home.py                    ← Página principal del dashboard con streamlit
    └── pages/
        ├── 1_Prediccion.py        ← Predicciones individuales
        ├── 2_Analisis.py          ← Análisis de lotes
        └── 3_Metricas.py          ← Métricas y rendimiento
```

## Instalación

Requisitos: Python 3.11 y Git.

```bash
git clone <url-del-repositorio>
cd Proyecto_B_Abandono_Clientes
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
pip install -r requirements.txt
```

## Ejecución

1. Ejecutar los notebooks en orden (`01` a `05`) desde `notebooks/`:
   ```bash
   jupyter notebook
   ```
2. Levantar la API (desde la raíz del proyecto):
   ```bash
   uvicorn api.main:app --reload
   ```
3. Levantar el frontend en otra terminal:
   ```bash
   streamlit run app/Home.py
   ```

## Entregables

- [ ] Notebook de EDA con análisis de tasas de churn por segmento
- [ ] Notebook con manejo de datos desbalanceados (class_weight)
- [ ] Dos modelos ANN: clasificación binaria y scoring de riesgo
- [ ] API REST con endpoints /predict/churn y /predict/risk_score
- [ ] Dashboard Streamlit con segmentación de clientes por nivel de riesgo
- [ ] Análisis de ROI potencial de estrategias de retención

## Resultados

| Modelo | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|
| Modelo 1 | 0.74 | | | |
| Modelo 2 | 0.61 | | | |

**Modelo seleccionado y justificación:**

Modelo 1 de clasificacion tiene el mejor ratio de acierto

## Conclusiones y recomendaciones

Las metricas de ambos modelos no supera el umbral del 80%, el desbalanceo de cargas es un factor bastante compejo de entrenar incliso al implementar class_weight, aplicar dropouts no siempre mejoro el modelo y el planeamiento de la arquitectura el bastante capricoso ya que con cambios minimos el accurracy bajaba bastane, por lo que considero que sobre una buena planificacion de la arquitectura de la red neuronal, la iteracion sobre distintos los distintos hiperparametros puede marcar los cambios fundamentales en la precicion.
