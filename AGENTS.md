<!-- ESTADO_ARCHIVO: EN_MODIFICACION -->

# AGENTS.md

Las partes en las que se indique como "editable por el agente" se permitira la actualizacion de esas partes en cualquier momento que se requiera o indique.

## 1. Propósito y alcance

Instrucciones para los agentes que trabajen en `Proyecto_B_Abandono_Clientes`,
proyecto académico de predicción de abandono de clientes de telecomunicaciones
mediante redes neuronales artificiales (ANN).

- Responsable: Desmond Akin Bermúdez Rodríguez.
- Curso: BD-151 Inteligencia Artificial Aplicada, Colegio Universitario de Cartago.
- Profesor: Osvaldo González Chaves. Año: 2026.
- Alcance: todo el repositorio; respetar las instrucciones internas de cada
  directorio y las restricciones de los documentos de contexto.
- Las decisiones explícitas del usuario prevalecen sobre estas convenciones,
  dentro de las instrucciones de mayor prioridad del entorno del agente.
- Una decisión pendiente no equivale a autorización ni obliga a detener tareas
  independientes que puedan resolverse dentro del alcance solicitado.

## 2. Etapa y objetivo del proyecto

### Estado(editable por el agente)

El proyecto está en la etapa de análisis exploratorio de datos (EDA). Su objetivo
es predecir el abandono de un servicio de telecomunicaciones y estimar niveles de
riesgo para apoyar estrategias de retención.

No hay actualmente código de API, dashboard, entrenamiento, modelos guardados ni
suite de pruebas. El árbol y los comandos del README describen en parte la
estructura objetivo


### Seguimiento de archivos(editable por el agente)

- `README.md` describe el problema, los lineamientos y los entregables previstos.
- `requirements.txt` declara dependencias de análisis, entrenamiento, API,
  dashboard y notebooks; declararlas no significa que esos componentes existan.
- `data/raw/` contiene el CSV de Telco Customer Churn y un archivo ZIP.
  El CSV local tiene 7.043 registros y 21 columnas.
- `data/raw/docs/Telco_Data_Context.md` documenta procedencia, diccionario de
  variables, calidad de datos y limitaciones del dataset, con fuentes citadas.
- `notebooks/EDA.ipynb` carga los datos, explora dimensiones, tipos, valores
  faltantes y categorías, renombra columnas al español e incluye un análisis de
  asociaciones mixtas con `dython`.
- El notebook está en desarrollo: tiene ejecuciones fuera de orden y un error
  guardado al convertir `Cargos_Totales` a `float64`. El CSV contiene 11 valores
  en blanco en `TotalCharges`; no afirmar que los datos están limpios solo porque
  `isnull()` o `isna()` no detecten esos textos como nulos.
- Existe un entorno virtual local `.IA_Abonado/` con Python 3.11.9.

### Entregables previstos

- Preprocesamiento reproducible y particiones de entrenamiento y prueba.
- Modelo 1: clasificación binaria de abandono (`Churn`, Yes/No).
- Modelo 2: probabilidad de abandono entre 0 y 1, con arquitectura distinta
  y niveles de riesgo definidos mediante umbrales justificados.
- Comparación de al menos dos configuraciones por modelo y selección razonada.
- API FastAPI con `POST /predict/churn` y `POST /predict/risk_score`.
- Dashboard Streamlit para predicciones, análisis y métricas.
- Análisis de ROI potencial de estrategias de retención.


## 3. Fuentes de contexto

Antes de modificar, consultar:

1. La petición actual del usuario y las instrucciones aplicables.
2. `README.md` para el alcance académico y los entregables.
3. `requirements.txt` para las dependencias declaradas.
4. Los notebooks, datos o código relacionados con la tarea.

Si el README difiere de la implementación, señalar la diferencia sin inventar
decisiones ni completar componentes ajenos a la petición.

Consultar `Proyect_Context/` solo cuando se pregunte por eventos pasados o se
necesite información histórica. Antes de escribir allí, leer sus instrucciones y
las últimas dos historias disponibles; respetar el estado y los permisos de cada
documento. No asumir antecedentes que no se hayan consultado.



## 4. Estructura actual y prevista(editable por el agente)

| Directorio | Estado y uso | Capacidad |
| --- | --- |
| `data/raw/` | Existente: datos originales; conservar sin modificaciones. | Disponible |
| `notebooks/` | Existente: contiene el notebook EDA en desarrollo. | En Proceso |
| `Proyect_Context/` | Existente: documentos de contexto sujetos a sus propias instrucciones. | Disponible |
| `.IA_Abonado/` | Existente: entorno virtual local; no incorporar a Git. | Disponible |
| `.vscode/` | Existente: configuración local del editor, excluida de Git. | Disponible |
| `data/processed/` | Previsto: datos derivados y particiones; aún no existe. | No disponible |
| `src/` | Previsto: configuración, preprocesamiento y entrenamiento; aún no existe. | No disponible |
| `models/` | Previsto: modelos Keras, escalador y columnas de entrada; aún no existe. | No disponible |
| `api/` | Previsto: API FastAPI e inferencia; aún no existe. | No disponible |
| `app/` | Previsto: dashboard Streamlit; aún no existe. | No disponible |

Comprobar los archivos antes de presentar una capacidad como disponible.

El README propone cinco notebooks numerados; actualmente solo existe
`notebooks/EDA.ipynb`. No renombrarlo ni crear toda la estructura prevista como
efecto secundario de otra tarea. Incorporar directorios cuando el trabajo
solicitado los necesite y lo indique el desarrollador, mantener coherentes sus rutas 
y no crear directorios fuera de los que se indiquen en el README.

### Sobre el archivo 'USO_DE_IA.md '

El texto de este archivo no puede ser modificado ni eliminado por parte del agente, solo puede agregrar la intervencion que realizo sobre el proyecto al final de dicha intervencion.

En este archivo se documentaran las integraran y las acciones del agente sobre el proyecto por lo que en cada intervencion del agente debe de quedar documentada en este documento:
- Qué herramientas de IA se utilisó(ChatGPT, Claude, Gemini, ...) y para qué tareas específicas
- Prompts utilizados.
- Reflexión sobre cómo la IA ayudó en su aprendizaje (1-2 párrafos)(Accion por parte del desarrollador, no lo maneja el agente)
- Qué modificaciones hicieron al código/análisis generado por IA(Accion por parte del desarrollador, no lo maneja el agente)

## 5. Tecnologías y dependencias

- Python 3.11 según el README; entorno local identificado como Python 3.11.9.
- Datos: NumPy, pandas y openpyxl.
- Visualización: Matplotlib y seaborn; el EDA también importa `dython`.
- Aprendizaje automático previsto: scikit-learn, TensorFlow/Keras y joblib.
- API prevista: FastAPI, Uvicorn y Pydantic.
- Dashboard previsto: Streamlit y requests.
- Notebooks: Jupyter. 
- Instalación mediante `pip` y control de versiones con Git.

Las dependencias no están fijadas a versiones exactas; solo TensorFlow y Pydantic
tienen mínimos declarados (`>=2.16` y `>=2`). El notebook importa `dython` y
`nbformat`, que no aparecen como dependencias directas en `requirements.txt`.
No dar por reproducible el entorno solo porque funcione localmente; resolver
esas diferencias cuando se solicite trabajar en dependencias o ejecución.

No incorporar gestores, frameworks, infraestructura o herramientas de calidad
por una convención heredada. No instalar paquetes ni cambiar versiones como
efecto secundario de una tarea documental.

## 6. Comandos de referencia

Ejecutar desde la raíz en PowerShell. Usar el entorno existente sin depender de
la activación de la terminal:

```powershell
Test-Path .\.IA_Abonado\Scripts\python.exe
.\.IA_Abonado\Scripts\python.exe --version
```

Si el entorno falta o no funciona, informar la limitación; no sustituirlo
silenciosamente por otra instalación ni recrearlo sin que la tarea lo requiera.

### Instalar las dependencias declaradas

```powershell
.\.IA_Abonado\Scripts\python.exe -m pip install -r .\requirements.txt
```

Usar solo si la tarea requiere preparar o actualizar el entorno. La instalación
de este archivo no resuelve por sí sola la dependencia directa faltante `dython`.

### Abrir el notebook existente

```powershell
Set-Location .\notebooks
..\.IA_Abonado\Scripts\python.exe -m jupyter notebook EDA.ipynb
```

El notebook usa rutas relativas a `notebooks/`; mantener ese directorio de
trabajo al ejecutarlo. Para los comandos siguientes, regresar a la raíz.

### API y dashboard: comandos previstos

Solo serán utilizables cuando existan sus implementaciones y artefactos:

```powershell
.\.IA_Abonado\Scripts\python.exe -m uvicorn api.main:app --reload
.\.IA_Abonado\Scripts\python.exe -m streamlit run .\app\Home.py
```

No existe un comando de pruebas establecido ni configuración de formato,
análisis de tipos, publicación o integración continua. No presentar comandos
de esas herramientas como parte de la base actual.

## 7. Convenciones de datos, notebooks y modelos

- Redactar documentación e interpretaciones en español y seguir la nomenclatura
  cercana; evitar renombrados ajenos a la tarea.
- Conservar intactos los datos de `data/raw/`. Guardar transformaciones en
  objetos derivados o en `data/processed/` cuando corresponda.
- Mantener explícita la relación entre nombres originales y traducciones,
  especialmente `Churn`/`Abandono` y `TotalCharges`/`Cargos_Totales`.
- Validar tipos, cadenas vacías o con espacios, duplicados y categorías antes de
  concluir que los datos están limpios. Justificar imputaciones o eliminaciones;
  no elegirlas automáticamente para hacer desaparecer un error.
- Excluir el identificador del cliente de las variables predictoras y separar
  la variable objetivo para evitar filtraciones de información.
- Respetar los lineamientos del README: `MinMaxScaler` ajustado solo con
  entrenamiento, codificación con `pd.get_dummies` y conservación de las columnas
  finales para reproducir las entradas durante la inferencia.
- Ajustar las transformaciones aprendidas usando entrenamiento; mantener iguales
  columnas y orden al transformar validación, prueba y nuevas observaciones.
- Entrenar con `validation_split` y `EarlyStopping`; reservar prueba para la
  evaluación final, sin usarla para elegir arquitectura, umbrales o transformaciones.
- Comparar al menos dos configuraciones por modelo y abordar el desbalance con
  `class_weight` según los entregables. Registrar semillas, particiones,
  hiperparámetros y criterios de selección cuando se implemente el entrenamiento.
- Reportar las métricas previstas (accuracy, precision, recall y F1) con su
  conjunto de evaluación; justificar umbrales de decisión y de riesgo.
- Distinguir una probabilidad estimada de una certeza de abandono. No inventar
  métricas ni presentar asociaciones como causalidad o ROI potencial como ahorro
  observado; declarar los supuestos de cualquier cálculo de retención.
- Mantener los notebooks ejecutables de principio a fin, con explicaciones
  coherentes con sus salidas. Los resultados guardados no prueban por sí solos
  que la versión actual sea reproducible.

Estas reglas orientan el trabajo futuro autorizado; no afirman que el pipeline
de entrenamiento o inferencia ya exista.

## 8. Flujo de trabajo y validación

### Antes de editar

- Revisar Git y las instrucciones aplicables, preservando cambios del usuario,
  incluidos archivos aún no versionados.
- Consultar el estado de los archivos y distinguir implementación de propuestas.
- Limitar los cambios al alcance solicitado.

### Durante el trabajo

- Hacer cambios proporcionales a la etapa del proyecto, sin imponer arquitectura
  o infraestructura futura.
- No sobrescribir datos originales, resultados o modelos del usuario para probar.
  Utilizar copias o ubicaciones temporales para las comprobaciones que lo necesiten.
- Evitar cambios masivos de metadatos o salidas de notebooks ajenos a la tarea.
- Respetar los archivos protegidos y las decisiones históricas consolidadas.

### Después de editar

- Revisar diferencias, rutas, coherencia y alcance de los archivos modificados.
- Para documentación, contrastar el contenido con el repositorio; no ejecutar
  notebooks, entrenamientos ni instalar paquetes por cambios solo de texto.
- Para cambios en notebooks, comprobar las celdas afectadas y, cuando sea viable,
  ejecutar desde un kernel limpio en orden. Informar si dependencias, tiempo de
  entrenamiento o recursos impiden la ejecución completa.
- Para lógica nueva, validar el comportamiento con comprobaciones pertinentes
  y pruebas cuando aporten cobertura útil; no afirmar que hay una suite existente.
- Informar qué cambió, qué se verificó y qué quedó sin comprobar. Distinguir las
  salidas preexistentes de las ejecuciones realizadas durante la tarea.

## 9. Seguridad, permisos y Git

- No publicar credenciales, tokens de Kaggle ni datos privados de clientes.
- No volcar filas identificables en registros o pruebas cuando basten agregados
  o datos ficticios. Conservar la procedencia del dataset y comprobar las
  condiciones de uso si una tarea requiere redistribuirlo.
- Respetar las exclusiones de `.gitignore` y evitar incorporar entornos,
  cachés o temporales. 
- No revertir cambios ajenos, borrar historial ni realizar operaciones
  destructivas de Git sin autorización expresa.
- Crear commits, publicar cambios o desplegar únicamente dentro del alcance
  autorizado. No hay una convención propia de commits establecida.

Consultar si una ambigüedad impide determinar el resultado esperado, si hace
falta alterar datos originales o archivos protegidos, o si una decisión excede
la petición. Continuar las partes independientes ya autorizadas.

## 10. Estado de los archivos

Todo archivo identificado mediante una ruta exacta en este documento debe constar
en la tabla de archivos controlados.

- `EN_MODIFICACION`: contenido provisional o sujeto a cambios.
- `ESTABLE`: validado expresamente por el usuario; el agente no puede asignar
  este estado por iniciativa propia.
- `No declarado` indica ausencia de un estado explícito; no equivale a validación
  ni autoriza a ignorar restricciones internas del archivo.
- `Only_Dev` indica que solo el desarrollador modifica el archivo en cuestion.
- Antes de editar un archivo estable, debe existir autorización para modificarlo
  y un cambio de estado a `EN_MODIFICACION` por parte del desarrollador en el documentop en cuestion.
- Al aplicar un distintivo, situarlo en la primera línea segura con comentarios
  propios del formato, respetando cabeceras obligatorias.
- En JSON estricto (incluidos notebooks), binarios, archivos generados, externos
  o protegidos, registrar el estado solo en la tabla. No alterar archivos solo
  consultados para añadirles un distintivo.
- Directorios, patrones, ejemplos y rutas dentro de comandos no obligan a
  registrar archivos. Evitar un inventario innecesario del repositorio.

### Archivos controlados

| Archivo | Estado | Método de identificación | Observaciones |
| --- | --- | --- | --- |
| `AGENTS.md` | `EN_MODIFICACION` | Comentario HTML en la primera línea | Adaptado al proyecto de abandono de clientes; pendiente de validación del usuario. |
| `README.md` | `Only_Dev` | Solo esta tabla | Alcance académico y estructura prevista; parte de lo descrito aún no existe. |
| `requirements.txt` | `EN_MODIFICACION` | Solo esta tabla | Dependencias declaradas; diferencias con los imports del EDA. |
| `.gitignore` | `EN_MODIFICACION` | Solo esta tabla | No excluye el entorno local `.IA_Abonado/`. |
| `notebooks/EDA.ipynb` | `Only_Dev` | Solo esta tabla, por ser JSON | EDA en desarrollo con salidas. |
| `data/raw/docs/Telco_Data_Context.md` | `EN_MODIFICACION` | Comentario HTML en la primera línea | Contexto documentado del dataset; pendiente de validación del usuario. |

## 11. Historial contextual

Respetar las instrucciones internas de `Proyect_Context/`: el documento descriptivo
está reservado al usuario y los elementos fijos del contexto están protegidos.

- Las nuevas historias corresponden únicamente a la zona posterior a
  `Context from here`, respetando permisos y estado del documento.
- Registrar decisiones relevantes solo cuando esté autorizado escribir en el
  historial. Editar otro archivo no concede por sí solo autorización para
  modificar un documento estable.
- Antes de integrar una historia, leer las últimas dos disponibles y conservar
  su orden. Resumir decisión, motivo, participante y archivos afectados según
  el formato interno.
- No reescribir decisiones consolidadas por el usuario o mediante un commit;
  añadir una nueva entrada que haga referencia a la anterior.
