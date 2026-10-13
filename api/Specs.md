<!-- ESTADO_ARCHIVO: EN_MODIFICACION -->
# API preliminar de abandono de clientes

## Propósito

Exponer inferencia con FastAPI y mantener una única implementación de validación,
escalado y predicción consumida por Streamlit mediante HTTP. Código preparado en Windows
para revisión y posterior traslado manual junto con app/ al proyecto WSL.

## Archivos integrados

| Archivo | Responsabilidad |
| --- | --- |
| `main.py` | Endpoints, carga de archivos, evaluación, restauración y cambio de configuración. |
| `loaders.py` | Despacho explícito por tipo y extensión a las clases de src. |
| `model_adapter.py` | Adaptador de Binary_Model para cargar .keras e inferir sin invertir etiquetas. |
| `datasets.py` | Vista previa flexible, recetas de preparación y validación de entradas ya escaladas. |
| `evaluation.py` | Métricas según la salida de cada modelo y reportes serializables. |
| `test_evaluation.py` | Fórmulas de evaluación, alineación de exportación y contenido del ZIP. |
| `test_datasets.py` | Pruebas de mapeo, filas, objetivo, revisiones y ausencia de doble escalado. |
| `schemas.py` | Contratos Pydantic de clientes, configuración, solicitudes y respuestas. |
| `predict.py` | Inventario local, carga de artefactos, validación, escalado e inferencia. |
| `test_predict.py` | Pruebas unittest con entradas sintéticas, incluyendo peticiones ASGI. |
| `__init__.py` | Paquete importable. |

Todos los archivos nuevos están en estado EN_MODIFICACION.

## Contrato verificado contra los notebooks y el scaler

Se consultaron los cuatro notebooks actuales de WSL y las clases de src. El flujo
real difiere del ejemplo genérico del README: contrato ordinal, categorías de
servicio agrupadas y 20 predictores, todos escalados por MinMaxScaler. El modelo
recibe datos procesados en español, todavía **sin escalar**. No recibe el CSV
original directamente.

Orden obligatorio, tomado de `feature_names_in_` del scaler existente:

```text
Adulto_Mayor
Pareja
Dependientes
Antiguedad(Meses)
Servicio_Telefono
Lineas_Multiples
Internet_DSL
Internet_Fiber optic
Seguridad_Online
Copia_Seguridad_Online
Proteccion_Dispositivos
Soporte_Tecnico
Streaming_TV
Streaming_Peliculas
Contrato
Facturacion_Electronica
MP_Electronic check
MP_Mailed check
MP_Bank transfer (automatic)
Cargos_Mensuales
```

- Variables binarias: 0/1; contrato: 0 = mes a mes, 1 = un año, 2 = dos años.
- Antigüedad y cargos mensuales: números finitos, no negativos y en rango entrenado.
- Sin internet: ambas dummies de internet en 0. Tarjeta automática: las tres
  dummies de pago en 0. Son las referencias observadas en el dataset procesado.
- El formulario convierte categorías humanas a este contrato; no infiere categorías
  nuevas ni ejecuta get_dummies sobre un único cliente.
- No se admiten ID_Cliente, Genero, Cargos_Totales ni Abandono como predictores.
  `Churn` corresponde a `Abandono`; `TotalCharges` a `Cargos_Totales` (excluida).
- Se rechazan variables extra, faltantes, duplicadas, nulos, infinitos, categorías
  inválidas y servicios contradictorios. Nunca se agregan columnas con cero para
  ocultar una incompatibilidad. En evaluación se valida y separa Abandono explícitamente.

## Flujo de inferencia

1. Validar cliente o lote (1 a 10.000 filas).
2. Construir DataFrame con las 20 columnas, en el orden documentado.
3. Comprobar rangos mínimos/máximos aprendidos: rechazar extrapolación; no recortar.
4. Aplicar `scaler.transform` una sola vez a todas las variables, incluidas dummies
   y contrato. Nunca ajustar el scaler en producción ni escalar dos veces.
5. Usar esa matriz para uno o ambos modelos, en bloques de hasta 256 filas.
6. Comprobar salida finita de forma N×1 y dentro de [0,1].
7. Abandono = Yes si P(Abandono=1) >= umbral. Riesgo según los límites configurados.

Las clases actuales Binary_Model y Regression_Model de WSL aplican escalado y
un umbral fijo > 0.8 en sus métodos de predicción/evaluación. La copia antigua de
src en Windows usa otra regla. La API reutiliza la propiedad model heredada para
inferir sobre la matriz ya escalada; mantiene P(Abandono=1) y aplica >= umbral con
el valor elegido en Inicio. No llama make_prediction, no escala dos veces y no
modifica las clases originales. evaluation.py reproduce las fórmulas de evaluación
sin depender de sus impresiones o ventanas Matplotlib.

## Artefactos y configuración

Ambos modelos se escogen entre archivos `.keras` directamente en models/; scaler
entre `.pkl` y `.joblib`. Debe ser un MinMaxScaler ya entrenado y conservar los
nombres y orden exactos anteriores. Si existe columnas.pkl, también se contrasta.
Si faltan nombres no se deduce el orden a partir del tamaño de entrada.

Se exige entrada N×20, salida N×1 y activación final sigmoid. Se carga con
`compile=False`, `safe_mode=True`. Solo se aceptan archivos locales, sin traversal
ni enlaces que salgan del directorio. Pickle/joblib solo son apropiados para
artefactos locales de confianza.

La comprobación estructural NO demuestra que un modelo arbitrario fue entrenado
con ese scaler, esas columnas en ese orden ni esa clase positiva. El propietario
debe conservar la correspondencia del entrenamiento. Los `.keras` actuales no
incluyen ese contrato completo. No se inventa esa garantía ni se convierten logits.
Los dos archivos deben ser distintos; eso no garantiza arquitecturas distintas.

Los modelos quedan en memoria por proceso. PUT /configuracion valida todos los
artefactos antes de sustituir la configuración y guarda su selección mediante
reemplazo atómico en models/configuracion_inferencia.json. El inicio de la API
restaura esa selección; si falla, /health muestra el error y se puede cargar otra.
Una petición toma una referencia estable; si otra carga falla, conserva los
modelos anteriores. Usar un único worker en esta implementación local.

La respuesta de configuración incluye una revisión única. Streamlit envía
X-Configuration-Id al predecir o evaluar: una revisión obsoleta devuelve 409 y
requiere actualizar la página, evitando mezclar resultados de configuraciones.

Los modelos, scaler y tres umbrales son obligatorios. No se asignan archivos ni
umbrales automáticamente cuando falta configuración. La intervención de
2026-10-12 conservó intacta la configuración que el usuario tenía guardada;
las pruebas no cambiaron sus modelos ni umbrales.
Se copiaron los tres .keras reales desde WSL a models/ de Windows y se comprobó
su integridad SHA-256. Los originales y el scaler no se modificaron.

## Reutilización de src y métodos de carga

| Tipo seleccionado | Extensión | Método utilizado |
| --- | --- | --- |
| Datos | .csv, .xlsx, .parquet | DataProcessor.load_data, heredado de DataLoader; este despacha a pandas según extensión. |
| Scaler | .pkl | DataProcessor.save_load_scaler(load=True), heredado de DataLoader, usa pickle. |
| Scaler | .joblib | joblib.load; asignación a la propiedad scaler de DataProcessor. |
| Modelo | .keras | ModeloInferencia hereda Binary_Model y usa la propiedad model de Modelo_ANN; carga Keras con compile=False y safe_mode=True. |

Para transformar datos se crea un DataProcessor por solicitud, se asigna data,
se llama set_types y se utiliza su scaler con transform. El adaptador ejecuta
la red sobre esa matriz ya escalada. El método legado make_prediction no se
invoca porque vuelve a escalar y aplica un umbral fijo ajeno a la configuración activa.
No se usa get_dummies sobre nuevas filas porque depende de las categorías que
aparezcan y podría cambiar el esquema; el contrato reproduce los códigos
observados del notebook. No se alteraron las clases de src.

La extensión es un contrato: .pkl se lee como pickle y .joblib como joblib.
Un joblib comprimido renombrado .pkl no se interpreta por ensayo y error.

## Subida de archivos

POST /files/{tipo} recibe el archivo como cuerpo binario y los parámetros
nombre y uso. Tipo: modelo, scaler o datos. Uso: prediccion, evaluacion, exploracion o preparacion. No requiere multipart ni otra dependencia. Streamlit envía el
contenido seleccionado y muestra los errores de la API.

Datos admite 20 MB y 1–10.000 filas; artefactos, 100 MB. Se rechazan nombres con
rutas y formatos que no correspondan al tipo. Datos se leen en un temporal,
se validan completos y se devuelven sin modificar datasets. CSV y Excel
comprueban encabezados duplicados antes de que pandas pueda renombrarlos.
Los modos originales evaluación y exploración exigen Abandono; predicción lo
rechaza. El nuevo modo preparacion admite columnas distintas y nulos para
configurar su tratamiento antes de exigir el contrato del modelo. Un modelo o
scaler se comprueba antes de guardarse en models/, sin sobrescribir nombres
existentes (409). La carga de un archivo no cambia los modelos activos:
se deben seleccionar y aplicar desde la configuración.

## Ejecución

Desde la raíz de Windows, con el entorno existente:

```powershell
.\.IA_Abonado\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000
.\.IA_Abonado\Scripts\python.exe -m unittest api.test_predict api.test_datasets api.test_evaluation -v
```

Tras copiar app/ y api/ a WSL, usar el Python del entorno de ese proyecto:

```bash
.IA_Abandono_wsl/bin/python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

OpenAPI: http://127.0.0.1:8000/docs. No incluye autenticación ni despliegue público;
el alcance actual es ejecución local académica.

| Método | Ruta | Uso |
| --- | --- | --- |
| GET | `/health` | Salud y presencia de configuración. |
| GET | `/artefactos` | Listas de modelos y posibles scalers locales. |
| GET | `/configuracion` | Configuración activa; 409 si falta. |
| PUT | `/configuracion` | Cargar ambos modelos y scaler una vez. |
| POST | `/predict/churn` | Un cliente y slot de modelo; etiqueta y probabilidad. |
| POST | `/predict/risk_score` | Un cliente y slot; probabilidad y riesgo. |
| POST | `/predict/batch` | Todos los clientes evaluados con ambos modelos. |
| POST | `/evaluate` | Clientes, etiquetas y nombre de conjunto; métricas y matrices de ambos modelos. |
| GET | `/data/validation` | Subconjunto de 23 filas del notebook validado por DataProcessor. |
| GET | `/data/exploration` | Dataset procesado local, validado y sin escalar. |
| POST | `/files/{tipo}` | Subir un modelo, scaler o dataset con el cargador elegido. |
| POST | `/datasets/prepare` | Aplicar una receta a un borrador y devolver datos/entradas validados. |
| POST | `/datasets/predict` | Inferencia del dataset preparado, con o sin nuevo escalado. |
| POST | `/datasets/evaluate` | Métricas del dataset preparado y sus etiquetas alineadas. |

Ejemplo de configuración (sustituir por nombres del inventario):

```json
{
  "modelo_1": "mejor_modelo_PR-AUC.keras",
  "modelo_2": "mejor_modelo_precision.keras",
  "scaler": "scaler.pkl",
  "umbral": 0.5,
  "riesgo_medio": 0.35,
  "riesgo_alto": 0.65
}
```

Ejemplo de predicción individual, también utilizable en `/predict/risk_score`:

```json
{
  "modelo": "modelo_1",
  "cliente": {
    "Adulto_Mayor": 0, "Pareja": 0, "Dependientes": 0,
    "Antiguedad(Meses)": 12, "Servicio_Telefono": 1, "Lineas_Multiples": 0,
    "Internet_DSL": 1, "Internet_Fiber optic": 0, "Seguridad_Online": 0,
    "Copia_Seguridad_Online": 0, "Proteccion_Dispositivos": 0, "Soporte_Tecnico": 0,
    "Streaming_TV": 0, "Streaming_Peliculas": 0, "Contrato": 0,
    "Facturacion_Electronica": 0, "MP_Electronic check": 0,
    "MP_Mailed check": 0, "MP_Bank transfer (automatic)": 0, "Cargos_Mensuales": 50
  }
}
```

Lotes: `{"clientes": [cliente1, cliente2]}` con los objetos anteriores. No se
envían nombres de archivos en cada predicción. Errores de entrada/artefactos: 422;
ausencia de configuración: 409.

## Validación y límites

Se verificó inferencia real por HTTP con dos modelos copiados de WSL y sus 23 ejemplos reservados,
sin entrenarlos ni modificar los originales; sus copias locales se verificaron por SHA-256. Las 29 pruebas verifican
orden, escalado, rechazo de datos inválidos, umbrales, contratos HTTP, revisión
obsoleta, persistencia, carga CSV/Excel/Parquet y subida de scalers sin sobrescritura.
Se comprobó además por HTTP la subida de un .keras real a un nombre temporal,
su detección en el inventario y su posterior limpieza; los modelos originales
se conservaron. Lotes y métricas se ejecutaron con ambas redes reales. Se comprobó también la
carga e inferencia del tercer modelo seleccionable y se restauró la selección
anterior. Tras reiniciar los servicios se recuperó la configuración guardada y
se generaron 23 predicciones por modelo; con la API detenida el cliente mostró
el error de conexión esperado. No son
una evaluación de calidad predictiva ni una prueba de instalación desde cero.

Fuentes de implementación: [MinMaxScaler](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.MinMaxScaler.html),
[modelos Pydantic](https://docs.pydantic.dev/latest/concepts/models/).


## Preparación configurable de datasets (versión 0.4.0)

La interfaz solo sube y prepara datasets desde Análisis de lotes. Métricas elige
entre los ejemplos reservados y el lote nuevo. Inicio conserva artefactos y el
origen general de Exploración; las selecciones de Lotes y Métricas son explícitas.
Los endpoints anteriores mantienen compatibilidad, pero la nueva interfaz usa
POST /files/datos?uso=preparacion para recibir el borrador sin exigir de antemano
las 20 columnas. Se limitan 10.000 filas, 200 columnas y 20 MB; no se permiten
encabezados duplicados o vacíos. Los nulos se conservan como null en la vista
previa, para poder eliminarlos mediante una acción explícita.

Preparacion es un contrato Pydantic con extra=forbid. Recibe fuente, filas,
eliminar_columnas, eliminar_filas (posiciones desde 1), eliminar_nulos,
entradas (destino -> columna de origen), valores (mapa por entrada), objetivo
opcional, valores_objetivo y aplicar_scaler. Se eliminan primero las columnas y
filas indicadas; luego, si se solicitó, las filas nulas en columnas utilizadas.
Las etiquetas se seleccionan con el mismo índice que los predictores.

Cada una de las 20 entradas debe tener origen. Una columna puede alimentar
varias dummies mediante mapas explícitos. Una categoría desconocida produce
error; no se rellena con cero. Columnas sobrantes se omiten del contrato y se
reportan. Se impide utilizar la columna objetivo como entrada. Abandono se
mapea a 0/1 y queda separado. La preparación no realiza fit, entrenamiento,
selección automática de variables ni imputación.

El resultado contiene filas en unidades originales para visualización,
entrada para inferencia, aplicar_scaler, revision_preparacion, filas_origen,
conteo de eliminadas, columnas omitidas y datos_exportacion. Este último conserva
las columnas y valores de origen después de eliminar filas/columnas, para añadir
las predicciones sin perder información ni enviar columnas extra a la red. No se persiste en disco ni en un
repositorio compartido: Streamlit conserva el borrador, receta y resultado
por sesión. Un fallo no sustituye el último resultado válido.

DatasetInferencia valida exactamente las 20 claves, números finitos, límites
de filas y correspondencia de etiquetas. La API vuelve a comprobar los datos
antes de predecir; no confía en que hayan pasado previamente por preparación.
Rechaza una revisión de preparación diferente de la configuración activa con
409. Esto también exige revalidar después de reiniciar la API.

- aplicar_scaler=true: validar Cliente, rango de entrenamiento y transform
  mediante DataProcessor; inferir sobre el resultado, sin ajustar el scaler.
- aplicar_scaler=false: las entradas deben estar YA escaladas. Comprobar rango
  feature_range, invertir solo para validar categorías, coherencia y rangos
  originales; inferir sobre los valores escalados recibidos sin nuevo transform.
  La inversión admite únicamente tolerancia de redondeo numérico, no categorías
  arbitrarias. Los gráficos usan las unidades originales reconstruidas.

La validación estructural no demuestra la procedencia de un dataset escalado;
el usuario debe saber que corresponde al scaler seleccionado. No se infiere
esa decisión por el rango aparente de números.

Las métricas exigen objetivo; lotes y exploración pueden trabajar sin él.
En el formulario individual la API conserva sus respuestas de probabilidad,
etiqueta y riesgo: la tarjeta del modelo 1 presenta 0/1 a partir de su umbral,
y la del modelo 2 presenta la probabilidad. No se modificaron las redes.

Verificación adicional 2026-10-12: los 29 tests pasaron. Por HTTP con las redes
reales se preparó un dataset con nombre de entrada distinto, columna extra,
filas eliminadas y objetivo textual. Lotes y métricas conservaron la alineación;
el mismo dataset ya escalado produjo probabilidades equivalentes (tolerancia
1e-6) sin aplicar transform otra vez. Streamlit AppTest verificó la preparación,
la elección central entre páginas y las dos presentaciones de resultado.


## Evaluación y exportación por modelo (0.4.0)

POST /evaluate y /datasets/evaluate comparten evaluation.metricas. Devuelven
metricas, matrices, reportes, clientes y revision. Modelo 1: MAE/RMSE sobre clase
0/1; modelo 2: MAE/RMSE sobre probabilidad. Ambos incluyen las razones MAE/media
y MAE/mediana de la etiqueta real (null si denominador cero), classification_report
y confusion_matrix como las clases actuales de src en WSL. Para el modelo 2,
reporte/matriz y accuracy/precision/recall/F1 son auxiliares, tras aplicar el
umbral configurado. ROC AUC y average precision usan probabilidades. clientes
incluye etiquetas reales y salidas para gráficos; no se incorpora al ZIP de métricas.

Lotes exporta datos_exportacion con clase del modelo 1 y probabilidad del modelo 2,
archivos de los modelos, umbral y posición original. Los nombres ya presentes
reciben sufijos en las columnas nuevas. Métricas descarga solo resumen, reportes
y matrices en ZIP; la plantilla individual también se ofrece allí.

Verificación actual: 33 pruebas satisfactorias en Windows y WSL (incluyen las
29 anteriores y cuatro de evaluación/exportación). En WSL se ejecutó el código
Windows montado bajo /mnt/c usando el src, modelos y scaler originales, con
inferencia y evaluación reales de 23 registros. Streamlit AppTest conectado al
HTTP local verificó preparación en Lotes, exportación tras eliminar filas/columnas,
gráficos interactivos y los dos orígenes de Métricas. Configuración conservada
por SHA-256. No se copió código al proyecto WSL ni se modificaron sus archivos.

Copiar app/ y api/ juntas después de revisar. Consultar app/Specs.md para el
arranque con .IA_Abandono_wsl/bin/python. El entorno WSL comprobado es Python
3.12.3 y el Windows 3.11.9. No trasladar la configuración Windows sin revisar los
nombres: modelo_74_accur.keras no figura con ese nombre en models/ de WSL.
Seleccionar los artefactos presentes desde Inicio; no hay elección implícita.

Revisión visual actual: navegación, selector de evaluación, matrices y gráficos
verificados en el navegador. Subida nativa de CSV ficticio con columna adicional,
preparación y análisis en Lotes; descarga real comprobada: 3 filas, 22 columnas
de origen más 6 de resultados. No se observaron superposiciones en estas vistas.


## Porcentajes y umbrales (revisión 2026-10-12)

Modelos de referencia indicados por el usuario: modelo_74_accur.keras y
regression_model.keras, con el scaler seleccionado. Se conserva la configuración
activa: clasificación 30 %, riesgo medio desde 50 % y alto desde 80 %.
Cada modelo aplica esos cortes a su propia probabilidad, sin redondear antes de
comparar. Clasificación y nivel de riesgo son decisiones distintas: 32,28 %
supera el 30 % de abandono, pero es riesgo bajo al estar por debajo del 50 %.

Inicio permite introducir los umbrales en porcentajes y los convierte dividiendo
entre 100 para la API. La configuración persistida, los endpoints y los CSV
mantienen valores numéricos de 0 a 1. Las tarjetas individuales muestran la
probabilidad de cada modelo, el umbral en porcentaje y los tres intervalos de
riesgo; Métricas también presenta su umbral en porcentaje. No se cambiaron los
cortes elegidos ni las reglas de clasificación para hacer coincidir etiquetas.

Verificación: 34 pruebas satisfactorias, incluyendo probabilidades propias por
modelo y límites justo debajo/en 30/50/80 %. AppTest con la API real comprobó
la conversión 30/50/80 a 0.3/0.5/0.8 sin persistir cambios, y las tarjetas con
43,98 % y 32,28 % para el perfil ficticio usado. Artefactos y configuración
conservados por SHA-256. Los porcentajes visuales se redondean a dos decimales;
las decisiones conservan toda la precisión recibida del modelo.
