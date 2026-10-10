<!-- ESTADO_ARCHIVO: EN_MODIFICACION -->

# Telco Customer Churn — Contexto del dataset

Documento de referencia sobre `WA_Fn-UseC_-Telco-Customer-Churn.csv` (Kaggle, `blastchar/telco-customer-churn`).
Convención de confianza: **[F]** = afirmado por una fuente citada; **[D]** = verificado directamente en el CSV local; **[I]** = interpretación a partir de los nombres y valores (el dataset no trae diccionario formal).

## 1. Procedencia

| Aspecto | Dato | Respaldo |
| --- | --- | --- |
| Origen | IBM Sample Data Sets (muestras de IBM Cognos Analytics) | [F] 1, 2, 4 |
| Publicación en Kaggle | Usuario `BlastChar`, versión 1 "Initial release", 23-feb-2018 | [F] 2 |
| Subtítulo / propósito en Kaggle | "Focused customer retention programs"; predecir comportamiento para retener clientes | [F] 2 |
| Naturaleza de los datos | **Ficticios.** IBM describe una empresa de telecomunicaciones ficticia | [F] 1, 3 |
| Cobertura (versión IBM 11.1.3) | 7.043 clientes en California, servicios de telefonía fija e Internet, datos del trimestre fiscal Q3 | [F] 3 |
| Licencia | Kaggle: "Data files © Original Authors". No hay licencia abierta explícita en Kaggle | [F] 2 |
| Tamaño en Kaggle | ≈ 977,5 KB | [F] 2 |

**Aspectos a resaltar**

- Algunas fuentes lo llaman "real-world" (p. ej. la entrada de Mendeley, DOI 10.17632/phsxg9ssrf.1, CC BY 4.0 de un tercero), pero IBM lo describe como **ficticio**. Los hallazgos no deben presentarse como comportamiento de clientes reales.
- La definición temporal de `Churn` es **inconsistente en las fuentes de IBM**: la muestra 11.1.1 y Kaggle dicen "dejó la empresa en el último mes"; las tablas de datos de la 11.1.3 indican "este trimestre". Este proyecto debe citar ambas redacciones y no asumir un periodo único. [F] 3, 4
- IBM publicó después una versión ampliada (5 tablas: Demographics, Location, Population, Services, Status; con `Churn Score`, `CLTV`, `Satisfaction Score`, etc.). **El CSV de Kaggle no incluye esas columnas** y sus nombres difieren de los de Cognos. [F] 3
- Los comportamientos temporales están agregados en indicadores estáticos (`tenure`, `TotalCharges`); es una **foto transversal**, sin serie temporal. [F] 5
- El dataset es muy usado en tutoriales; no hay documentación primaria que detalle la generación de los datos (se desconoce si fueron simulados o derivados de datos reales anonimizados). **No afirmar ninguna de las dos cosas.**

## 2. Estructura general [D]

| Característica | Valor |
| --- | --- |
| Registros / columnas | 7.043 / 21 |
| Unidad de observación | Un cliente por fila |
| `customerID` | 7.043 valores únicos (10 caracteres, formato `NNNN-AAAAA`); sin filas duplicadas |
| Variable objetivo | `Churn` (Yes/No) |
| Desbalance | No: 5.174 (73,5 %) · Yes: 1.869 (26,5 %) |
| Valores nulos reconocidos por pandas | Ninguno, pero **hay 11 valores en blanco** en `TotalCharges` (ver §5) |

## 3. Diccionario de variables

Los nombres en español son los asignados al renombrar las columnas en el análisis.

### 3.1 Identificador y objetivo

| Variable original | Renombrada | Significado | Valores [D] |
| --- | --- | --- | --- |
| `customerID` | `ID_Cliente` | Identificador único del cliente. No es predictor. | Texto, 7.043 únicos |
| `Churn` | `Abandonó` | El cliente dejó la empresa (variable objetivo). | No 5.174 · Yes 1.869 |

### 3.2 Demografía

| Variable original | Renombrada | Significado | Valores [D] |
| --- | --- | --- | --- |
| `gender` | `Género` | Género del cliente. | Male 3.555 · Female 3.488 |
| `SeniorCitizen` | `Adulto_Mayor` | Indica si el cliente es adulto mayor (Kaggle lo describe como rango de edad). El umbral de edad no figura en las fuentes consultadas. | **Numérica 0/1** (no Yes/No): 0 = 5.901 · 1 = 1.142 |
| `Partner` | `Pareja` | Tiene pareja. | No 3.641 · Yes 3.402 |
| `Dependents` | `Dependientes` | Tiene dependientes. | No 4.933 · Yes 2.110 |

### 3.3 Servicios contratados

| Variable original | Renombrada | Significado [I] | Valores [D] |
| --- | --- | --- | --- |
| `PhoneService` | `Servicio_Telefono` | Contrata telefonía. | Yes 6.361 · No 682 |
| `MultipleLines` | `Lineas_Multiples` | Contrata varias líneas telefónicas. | No 3.390 · Yes 2.971 · No phone service 682 |
| `InternetService` | `Servicio_Internet` | Tipo de proveedor de Internet. | Fiber optic 3.096 · DSL 2.421 · No 1.526 |
| `OnlineSecurity` | `Seguridad_Online` | Complemento de seguridad en línea. | No 3.498 · Yes 2.019 · No internet service 1.526 |
| `OnlineBackup` | `Copia_Seguridad_Online` | Complemento de respaldo en línea. | No 3.088 · Yes 2.429 · No internet service 1.526 |
| `DeviceProtection` | `Proteccion_Dispositivos` | Protección de dispositivos. | No 3.095 · Yes 2.422 · No internet service 1.526 |
| `TechSupport` | `Soporte_Tecnico` | Soporte técnico. | No 3.473 · Yes 2.044 · No internet service 1.526 |
| `StreamingTV` | `Streaming_TV` | Contenido de TV por streaming. | No 2.810 · Yes 2.707 · No internet service 1.526 |
| `StreamingMovies` | `Streaming_Peliculas` | Películas por streaming. | No 2.785 · Yes 2.732 · No internet service 1.526 |

### 3.4 Cuenta y facturación

| Variable original | Renombrada | Significado | Valores [D] |
| --- | --- | --- | --- |
| `tenure` | `Antiguedad_Meses` | Meses que el cliente ha permanecido en la empresa. | Entero 0–72; media 32,4; mediana 29 |
| `Contract` | `Contrato` | Tipo de contrato. | Month-to-month 3.875 · Two year 1.695 · One year 1.473 |
| `PaperlessBilling` | `Facturacion_Electronica` | Factura sin papel (electrónica). | Yes 4.171 · No 2.872 |
| `PaymentMethod` | `Metodo_Pago` | Método de pago. | Electronic check 2.365 · Mailed check 1.612 · Bank transfer (automatic) 1.544 · Credit card (automatic) 1.522 |
| `MonthlyCharges` | `Cargos_Mensuales` | Cargo mensual vigente (moneda no especificada en las fuentes). | 18,25–118,75; media 64,76; mediana 70,35 |
| `TotalCharges` | `Cargos_Totales` | Cargo acumulado total. Se almacena como **texto** en el CSV. | 18,80–8.684,80 (7.032 valores numéricos); media 2.283,30; **11 en blanco** |

## 4. Cómo se integran las variables

- **Servicios dependientes (categorías "sin servicio")** [D]: las 6 variables de complementos de Internet (`OnlineSecurity` … `StreamingMovies`) toman "No internet service" exactamente en los 1.526 clientes con `InternetService = No`; `MultipleLines` toma "No phone service" exactamente en los 682 clientes con `PhoneService = No`. Es información redundante: "No internet service"/"No phone service" equivale funcionalmente a "No" más la ausencia del servicio base. Tenerlo presente al codificar (colinealidad en `get_dummies`) y al interpretar importancias.
- **Relación monto–antigüedad** [D, I]: para los 7.032 clientes con dato, `TotalCharges / (tenure × MonthlyCharges)` tiene mediana 1,00 (rango 0,69–1,57). `TotalCharges` es aproximadamente el cargo mensual acumulado; está fuertemente ligado a `tenure` y `MonthlyCharges` (posible redundancia). La desviación se explica por cambios de tarifa a lo largo del tiempo o descuentos, hipótesis no documentada por las fuentes.
- **Contrato y permanencia** [D]: la antigüedad media es 37,6 meses en quienes se quedaron y 18,0 en quienes abandonaron.

## 5. Calidad de datos: puntos a resaltar

| Hallazgo | Detalle [D] | Implicación |
| --- | --- | --- |
| `TotalCharges` con 11 espacios en blanco | Los 11 casos tienen `tenure = 0` y `Churn = No`. `isnull()` no los detecta porque son cadenas con espacio; la conversión a `float` falla. | Son clientes aún sin primer cobro (no un fallo aleatorio): imputar o eliminar es una decisión que debe justificarse y documentarse. Eliminarlos pierde 0,16 % de filas. Una opción defendible es tratarlos como 0 (aún sin facturación), pero es una suposición no confirmada por las fuentes. |
| `tenure = 0` | Exactamente 11 registros, los mismos anteriores. | Clientes recién incorporados en el periodo ("Joined" en el modelo de datos ampliado de IBM). |
| `SeniorCitizen` numérica | Única variable binaria codificada 0/1; las demás usan Yes/No. | Homogeneizar si se trata como categórica; no confundir con medición continua. |
| Categorías "No internet/phone service" | Ver §4. | Decidir si se colapsan a "No". |
| Desbalance de clase | 26,5 % de abandono. | Justifica `class_weight` y métricas distintas a accuracy (recall, F1). |
| Duplicados / ID | 0 filas duplicadas; 0 `customerID` repetidos. | Sin problemas. |

## 6. Asociaciones descriptivas ya visibles [D]

No implican causalidad.

| Segmento | Tasa de abandono (Yes) |
| --- | --- |
| Contrato Month-to-month | 42,7 % |
| Contrato One year | 11,3 % |
| Contrato Two year | 2,8 % |

La antigüedad baja y el contrato mensual se asocian con mayor abandono; la abundancia de clientes mensuales (55 %) explica gran parte del volumen de abandonos.

## 7. Limitaciones de uso

- Datos ficticios de una sola región (California) y un solo corte temporal: conclusiones no extrapolables a clientes reales sin validación.
- Sin fecha de observación, moneda, ni criterio de edad del adulto mayor documentados.
- `Churn` es una etiqueta puntual; no indica motivo ni momento del abandono.
- Los datos de Kaggle no incluyen `Churn Score`, `CLTV` ni `Satisfaction Score` de la versión ampliada de IBM; **no usar esos nombres** para este CSV.
- Licencia de redistribución no abierta ("© Original Authors"): citar la procedencia si se redistribuye.

## 8. Fuentes

1. IBM Community — *New Base Samples for IBM Cognos Analytics 11.1.1* (nov. 2018): https://community.ibm.com/community/user/businessanalytics/blogs/steven-macko/2018/11/26/new-base-samples-for-ibm-cognos-analytics-1111
2. Kaggle — *Telco Customer Churn* (BlastChar), metadatos vía API pública: https://www.kaggle.com/datasets/blastchar/telco-customer-churn
3. IBM Community — *Telco customer churn (Cognos Analytics 11.1.3)* (jul. 2019): https://community.ibm.com/community/user/blogs/steven-macko/2019/07/11/telco-customer-churn-1113
4. IBM Community — *New Base Samples for IBM Cognos Analytics 11.1.3*: https://community.ibm.com/community/user/blogs/steven-macko/2019/07/10/new-base-samples-for-ibm-cognos-analytics-1113
5. Mendeley Data — *Telco customer churn IBM dataset* (copia derivada; solo usada para la nota de agregación temporal): https://data.mendeley.com/datasets/phsxg9ssrf
6. Datos locales: `data/raw/WA_Fn-UseC_-Telco-Customer-Churn.csv` (todas las cifras marcadas [D]).
