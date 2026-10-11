# Uso de IA

## Intervención 1 — Documento de contexto del dataset

**Herramienta:** Claude Code (Claude Sonnet 5.5, Anthropic).

**Tareas:**
- Búsqueda y lectura de fuentes sobre el dataset (IBM Community/Cognos Analytics, metadatos de Kaggle, Mendeley Data).
- Verificación de cifras sobre `data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv` (distribuciones, valores en blanco, relaciones entre variables).
- Redacción de `data/raw/docs/Telco_Data_Context.md`.
- Actualización de `AGENTS.md` (seguimiento de archivos y tabla de archivos controlados).

**Prompt utilizado (resumen):** Generar en `data/raw/docs` el documento `Telco_Data_Context.md` con el máximo contenido verídico y respaldado por fuentes confiables sobre el dataset de Kaggle `blastchar/telco-customer-churn`; incluir tablas con el nombre de la variable, su significado y su renombrado al español (captura de las columnas renombradas); ser conciso sin recortar contenido importante; no crear otras carpetas ni archivos.

**Reflexión sobre cómo la IA ayudó en el aprendizaje:** _(pendiente, la completa el desarrollador)_

**Modificaciones realizadas por el desarrollador al código/análisis generado:** _(pendiente, las completa el desarrollador)_

## Intervención 2 — Revisión de cambios y redacción del mensaje de commit

**Fecha:** 2026-10-10.

**Herramienta:** ChatGPT (Codex).

**Tareas:**
- Consulta del estado de Git, diferencias pendientes e historial de commits.
- Lectura de documentación, módulos de `src/` y celdas de los notebooks para resumir los cambios existentes.
- Redacción de un mensaje de commit en español con el formato `features/Título: descripción`, observado en el historial disponible; los proyectos vecinos consultados no tenían repositorio Git propio.
- Identificación de que el CSV original y el Parquet procesado siguen apareciendo como archivos no versionados pese a las entradas de `.gitignore`.
- Sin ejecución de notebooks, instalación de dependencias ni creación del commit; el usuario realizará el commit.

**Prompt utilizado:** «Genera un mensaje tipo commit que contenga todos los cambios realizados en el proyecto, yo realizare el commit pero tu indicaras los cambios mediante el mensaje, mantén una convención con los otros proyectos».

**Reflexión sobre cómo la IA ayudó en el aprendizaje:** _(pendiente, la completa el desarrollador)_

**Modificaciones realizadas por el desarrollador al código/análisis generado:** _(pendiente, las completa el desarrollador)_

## Intervención 3 — Mensaje de commit para particiones y escalado

**Fecha:** 2026-10-10.

**Herramienta:** ChatGPT (Codex).

**Tareas:**
- Revisión del estado de Git y de las diferencias respecto al commit bfb8d28, incluidos archivos nuevos y comparación de las celdas de los notebooks renombrados.
- Redacción del mensaje con la convención existente `features/Título: descripción`, centrado en numeración de notebooks, particiones estratificadas, escalado, persistencia y exclusiones de Git.
- Identificación mediante lectura del código de un problema pendiente en la exportación `.npy`: `save_data` usa `self.array`, mientras el notebook asigna los subconjuntos a `data`; además, el setter de `array` se llama a sí mismo.
- Sin cambios al código o a los notebooks, sin ejecutarlos y sin crear el commit.

**Prompt utilizado:** «Genera un mensaje tipo commit que contenga todos los cambios realizados en el proyecto, yo realizare el commit pero tu indicaras los cambios mediante el mensaje, mantén una convención con los otros proyectos».

**Reflexión sobre cómo la IA ayudó en el aprendizaje:** _(pendiente, la completa el desarrollador)_

**Modificaciones realizadas por el desarrollador al código/análisis generado:** _(pendiente, las completa el desarrollador)_


## Intervención 4 — Ajuste de dependencias del proyecto

**Fecha:** 2026-10-11.

**Herramienta:** ChatGPT (Codex).

**Prompt utilizado:** «Pon el archivo [requirements.txt](requirements.txt) en regla con el proyecto».

**Tareas:**
- Revisión de las instrucciones, README, estado de Git, imports de los módulos y notebooks actuales, y metadatos del entorno Python 3.11.9 existente.
- Incorporación de scipy, dython, pyarrow, keras y nbformat como dependencias explícitas; declaración de ipykernel para los notebooks.
- Establecimiento de matplotlib>=3.10 por el argumento orientation de boxplot y keras>=3 en consonancia con TensorFlow>=2.16; conservación de las dependencias previstas para API y dashboard, identificadas mediante comentarios.
- Consulta de documentación oficial: https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.boxplot.html y https://pandas.pydata.org/docs/reference/api/pandas.read_parquet.html.
- Verificación de sintaxis, ausencia de duplicados, cobertura de imports externos y cumplimiento de restricciones por las versiones instaladas. pip check no encontró conflictos en el entorno existente.
- Comprobación satisfactoria de imports de las dependencias añadidas y del kernel, TensorFlow/Keras, lectura/escritura Parquet en memoria con datos ficticios y creación de un boxplot horizontal sin guardar archivos.
- Jupyter y Notebook no están instalados en el entorno local; jupyter se conserva en requirements.txt. No se instalaron paquetes ni se validó una instalación desde cero. El archivo declara dependencias directas y no bloquea todas sus versiones.
- El notebook nuevo del modelo ANN está vacío; se revisaron los otros tres notebooks y los módulos de src. AGENTS.md conserva una descripción anterior del proyecto. No se modificaron código, notebooks, datos ni cambios previos del usuario, ni se ejecutó entrenamiento.

**Reflexión sobre cómo la IA ayudó en el aprendizaje:** _(pendiente, la completa el desarrollador)_

**Modificaciones realizadas por el desarrollador al código/análisis generado:** _(pendiente, las completa el desarrollador)_

## Intervención 5 — Mensaje de commit para la base ANN y persistencia de datos

**Fecha:** 2026-10-11.

**Herramienta:** ChatGPT (Codex).

**Tareas:**
- Revisión del estado de Git, historial y diferencias respecto al commit cb884d3, incluidos los archivos nuevos y las celdas modificadas del notebook de particiones.
- Redacción del mensaje con la convención `features/Título: descripción`, abarcando la base de clases ANN, exportación de particiones en CSV, manejo del escalador, utilidades, dependencias y exclusiones.
- Comprobación de que el notebook del primer modelo está vacío; la implementación ANN se describe como desarrollo inicial, sin afirmar entrenamiento ni resultados validados.
- Solo se añadió este registro al documento; no se modificaron código, notebooks, dependencias ni datos. No se ejecutaron pruebas, notebooks o entrenamientos, ni se creó el commit.

**Prompt utilizado:** «Genera un mensaje tipo commit que contenga todos los cambios realizados en el proyecto, yo realizare el commit pero tu indicaras los cambios mediante el mensaje, mantén una convención con los otros proyectos».

**Reflexión sobre cómo la IA ayudó en el aprendizaje:** _(pendiente, la completa el desarrollador)_

**Modificaciones realizadas por el desarrollador al código/análisis generado:** _(pendiente, las completa el desarrollador)_
