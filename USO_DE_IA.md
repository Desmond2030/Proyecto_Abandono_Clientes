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

