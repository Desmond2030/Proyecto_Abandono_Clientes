<!-- ESTADO_ARCHIVO: EN_MODIFICACION -->
# Dashboard de retención

## Objetivo y ejecución

Aplicación Streamlit para seleccionar dos redes, predecir clientes, preparar
archivos, analizar lotes, evaluar métricas y explorar el dataset. Se mantiene
en la copia Windows para revisión y traslado posterior por el desarrollador.

Desde la raíz y con el entorno existente:

```powershell
.\.IA_Abonado\Scripts\python.exe app/run.py
```

App: http://127.0.0.1:8501 · API: http://127.0.0.1:8000/docs.
El lanzador inicia FastAPI y Streamlit, comprueba puertos y cierra sus procesos
con Ctrl+C. Para iniciarlos por separado, ejecutar uvicorn api.main:app en 8000
y streamlit run app/Home.py en 8501, con el Python del mismo entorno.
TELCO_API_URL indica otra URL de backend al iniciar Streamlit por separado.

## Archivos

| Archivo | Responsabilidad |
| --- | --- |
| Home.py | Navegación común y estado real de conexión. |
| run.py | Arranque y cierre de servicios. |
| client.py | Cliente HTTP de FastAPI; no ejecuta inferencia local. |
| ui.py | Diseño común, origen activo y tarjetas de resultados. |
| datasets.py | Formulario único de subida, limpieza y mapeo de datasets. |
| pages/0_Inicio.py | Modelos, scaler, umbrales y selector global de origen. |
| pages/1_Prediccion.py | Formulario individual; modelo 1 clase 0/1, modelo 2 probabilidad. |
| pages/2_Analisis.py | Carga, preparación, inferencia y descarga del dataset con predicciones. |
| pages/3_Metricas.py | Selector de conjunto, evaluación etiquetada y descarga de resultados. |
| results.py | Gráficos interactivos, unión de predicciones y ZIP de evaluación. |
| pages/4_Visualizaciones.py | Distribuciones, segmentos, asociaciones y calidad. |

## Inicio y selección de datos

Inicio conserva selección y subida de modelos .keras y scalers .pkl/.joblib.
Los inventarios proceden de models/. Dos redes distintas y el scaler compartido
se cargan una vez al aplicar la configuración, que la API guarda en
models/configuracion_inferencia.json y restaura al reiniciar. No se cambian
por cliente. Los umbrales se eligen explícitamente; no se recalibran aquí.

El selector «Origen general de datos» de Inicio elige proyecto o dataset preparado
para Exploración y el valor inicial de Métricas. Métricas tiene su propio selector
entre los 23 ejemplos reservados y el dataset nuevo cargado en Lotes. Lotes
selecciona automáticamente el nuevo dataset tras prepararlo; también permite
analizar el dataset procesado predispuesto. Una fuente subida ausente no se
sustituye silenciosamente por datos del proyecto.

El origen, borrador, receta y resultado preparado se conservan entre páginas
en la sesión de Streamlit. Los datasets no se guardan sobre archivos del proyecto
ni se comparten entre usuarios. Una sesión nueva requiere subirlos otra vez.
Si cambia la configuración de modelos/scaler o se reinicia la API, se exige
preparar de nuevo el archivo para confirmar su correspondencia.

## Cargar y preparar datos: exclusivamente en Análisis de lotes

Inicio y Métricas no tienen controles de subida de datasets. Lotes admite
CSV UTF-8, Excel .xlsx y Parquet, hasta 20 MB, 10.000 filas y 200 columnas de
origen. La primera lectura admite nombres distintos, columnas extra, categorías
y nulos. La API utiliza DataProcessor.load_data, heredado de DataLoader.
La vista previa muestra las primeras 100 filas; las reglas se aplican a todas.

Acciones disponibles:

1. Eliminar columnas seleccionadas.
2. Eliminar posiciones de fila, desde 1 sin encabezado: `1, 4-8, 12`.
3. Opcionalmente eliminar filas con nulos o espacios vacíos en columnas usadas.
4. Mapear cada una de las 20 entradas del modelo a una columna conservada.
5. Definir mapas de valores JSON por entrada cuando contenga categorías:
   `{"Yes": 1, "No": 0}`. Sin mapa se exige contenido numérico.
6. Seleccionar una columna objetivo opcional y mapearla a 0 = permanece,
   1 = abandona. La columna objetivo no puede ser una entrada.
7. Elegir si aplicar scaler antes de predecir.

Una columna de origen puede alimentar varias dummies con mapas diferentes;
por ejemplo InternetService a Internet_DSL e Internet_Fiber optic. Cada mapa
debe cubrir todos los valores presentes. No se inventan ceros para categorías
no reconocidas. Las columnas no mapeadas se omiten y se identifican en el resumen.
Solo las 20 entradas finales llegan al modelo, siempre en su orden entrenado.
La eliminación conserva la correspondencia de etiquetas y posiciones originales.

Aplicar scaler activado significa que el archivo contiene entradas sin escalar.
Desactivado significa que YA están escaladas con el scaler activo: se comprueban
rango, nombres, dimensiones y categorías reconstruidas mediante inverse_transform;
la matriz se envía a la red sin aplicar transform otra vez. Exploración siempre
muestra unidades originales. La validación estructural no prueba por sí sola
qué scaler produjo un archivo: el usuario debe conservar esa correspondencia.

«Validar y guardar dataset preparado» llama a la API. Un error conserva el último
resultado válido; cambiar el borrador no lo sustituye hasta validar. La receta
se conserva para poder corregirla o volver a validarla. Tras preparar, Lotes
selecciona el nuevo dataset y lo deja disponible para Métricas. Para explorarlo,
se elige el origen subido en Inicio. Sin objetivo se habilitan lotes y exploración;
las métricas muestran que requieren etiquetas, sin inventarlas.

## Predicciones y evaluación

El formulario individual permanece igual. La tarjeta del modelo 1 muestra
la clase numérica 0/1 derivada del umbral configurado; la del modelo 2 muestra
probabilidad de churn. Se conservan barra, etiqueta, riesgo y umbral de ambas.
No se modificaron las redes ni sus salidas sigmoid; el cambio es de presentación.

Lotes descarga el dataset después de las eliminaciones indicadas, con sus nombres
y valores de origen, incluyendo columnas adicionales no usadas para inferencia.
Añade Fila_origen, Prediccion_Abandono_Modelo_1 (0/1),
Probabilidad_Abandono_Modelo_2 (0–1), archivos de los modelos y umbral del modelo 1.
Si un nombre ya existe se agrega un sufijo numérico; no se sobrescribe contenido.
Los índices mantienen la correspondencia tras eliminar filas. Mapeo y escalado
se aplican a las entradas de inferencia, no reescriben las columnas exportadas.

Métricas no prepara archivos. Requiere etiquetas reales del conjunto elegido.
Reproduce las medidas de Binary_Model y Regression_Model del src actual en WSL:
reporte de clasificación, matriz de confusión, MAE, RMSE, MAE/media y MAE/mediana.
Los errores del modelo 1 se calculan sobre clases; los del modelo 2 sobre sus
probabilidades frente a la etiqueta binaria. Las razones con denominador cero
son null. Se conservan accuracy, precision, recall, F1, ROC AUC y average precision;
AUC/AP requieren ambas clases. La clasificación del modelo 2 es auxiliar para
reporte/matriz y utiliza el umbral activo, sin reemplazar su probabilidad.

Los gráficos interactivos muestran cantidades por clase del modelo 1 (y reales
si existen etiquetas), y probabilidades por cliente del modelo 2, con detalle
al pasar el cursor y zoom horizontal. Ocupan filas completas. Las matrices de
confusión tienen detalle interactivo. Los gráficos no calculan inferencia local.
Métricas ofrece solo la plantilla de cliente individual y un ZIP con metricas.csv,
las dos matrices y los dos reportes; las predicciones se descargan desde Lotes.
Los 23 ejemplos del notebook son demostrativos: X_test se usó como validación,
por lo que no constituyen prueba final independiente.

## Exploración y asociaciones

Exploración usa exclusivamente el origen seleccionado en Inicio. Con objetivo
muestra tasas y distribuciones por abandono; sin objetivo muestra distribuciones
y cantidades, indicando «Sin objetivo» y sin inferir etiquetas.

Asociaciones permite todas las columnas disponibles (20 entradas y objetivo
cuando existe), sin límite de 12. Se puede usar todas o elegir un subconjunto
de al menos 2. La figura crece con el número de variables, muestra valores,
acomoda los nombres completos y aprovecha el ancho disponible. El icono de
expansión de Streamlit permite pantalla completa. Se ofrece SVG ampliable,
CSV y tabla completa de coeficientes. Variables constantes se advierten;
las asociaciones mixtas no prueban causalidad ni equivalen todas a Pearson.

## API por función

| Función | Rutas |
| --- | --- |
| Estado y modelos | GET /health, /artefactos, /configuracion; PUT /configuracion. |
| Artefactos | POST /files/modelo o /files/scaler. |
| Borrador y preparación | POST /files/datos?uso=preparacion; POST /datasets/prepare. |
| Individual | POST /predict/churn y /predict/risk_score. |
| Dataset subido | POST /datasets/predict y /datasets/evaluate. |
| Dataset predispuesto | GET /data/validation o /data/exploration; POST /predict/batch o /evaluate. |

## Diseño y verificación

Paleta coordinada: petróleo, verde, azul, violeta y cobre según página. Se
conservan cabeceras adaptables, margen superior, tablas con desplazamiento y
contenedores sin alturas fijas para texto. Los editores tienen desplazamiento
interno para mostrar todas las filas sin superponer controles.

Comprobación 2026-10-12: 33 pruebas satisfactorias tanto en Windows como en WSL.
La ejecución en WSL utilizó este código desde /mnt/c, las clases src originales,
su scaler y dos redes originales; produjo predicciones y métricas de 23 filas.
No se copiaron todavía app/ ni api/ al proyecto principal.
Streamlit AppTest con HTTP real verificó preparación en Lotes, eliminación de
filas/columnas, exportación alineada, cuatro gráficos en Métricas, selección de
ambas fuentes y conservación por hash de la configuración del usuario. La carga
del borrador se realizó por HTTP; AppTest no automatiza el selector nativo.
No se instalaron paquetes ni se modificaron modelos, notebooks o datos originales.

## Traslado a WSL después de la revisión

Copiar app/ y api/ juntas (versión 0.4.0), sin cachés __pycache__.
Conservar src/, models/, data/ y el entorno existentes en WSL. No copiar el
entorno Windows ni su configuración de modelos: modelo_74_accur.keras no existe
con ese nombre en el inventario WSL verificado. Elegir allí dos archivos reales
y su scaler desde Inicio y aplicar la configuración.

Desde la raíz del proyecto WSL:

```bash
.IA_Abandono_wsl/bin/python app/run.py
.IA_Abandono_wsl/bin/python -m unittest api.test_predict api.test_datasets api.test_evaluation -v
```

El entorno WSL comprobado usa Python 3.12.3; Windows usa 3.11.9. Se verificó la
compatibilidad con ambos entornos instalados, no una instalación desde cero.
Las rutas de datos y modelos se resuelven relativas a la raíz del proyecto.

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

## Integración en el proyecto principal WSL — 2026-10-12

Las carpetas app/ y api/ se incorporaron en la rama feature/pagina sobre el
commit local 8fe5a24. Se consultó origin/Feature/Modelos (b34fbe1): no había
actualizaciones remotas adicionales. Se preservaron íntegros los archivos
preexistentes de WSL; no se trasladaron modelos, datos, notebooks, src,
configuración de inferencia ni el entorno de Windows. Las 34 pruebas pasaron
con el entorno .IA_Abandono_wsl del proyecto principal.

Los modelos de referencia seleccionados en Windows (modelo_74_accur.keras y
regression_model.keras) no están con esos nombres en models/ de WSL al integrar.
No se sustituyeron por otros de forma automática. En WSL se deben disponer
esos artefactos y configurar explícitamente la app para reproducir esa selección.
Los apartados de traslado anteriores describen la preparación de la copia Windows;
esta sección registra la integración efectuada, sin publicar la rama al remoto.
