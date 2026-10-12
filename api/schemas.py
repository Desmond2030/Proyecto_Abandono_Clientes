# ESTADO_ARCHIVO: EN_MODIFICACION
"""Contrato de entrada: datos procesados del notebook, todavía SIN escalar."""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Bit = Literal[0, 1]


class Estricto(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Cliente(Estricto):
    Adulto_Mayor: Bit
    Pareja: Bit
    Dependientes: Bit
    antiguedad: Annotated[float, Field(alias="Antiguedad(Meses)", ge=0)]
    Servicio_Telefono: Bit
    Lineas_Multiples: Bit
    Internet_DSL: Bit
    internet_fibra: Bit = Field(alias="Internet_Fiber optic")
    Seguridad_Online: Bit
    Copia_Seguridad_Online: Bit
    Proteccion_Dispositivos: Bit
    Soporte_Tecnico: Bit
    Streaming_TV: Bit
    Streaming_Peliculas: Bit
    Contrato: Literal[0, 1, 2]
    Facturacion_Electronica: Bit
    pago_electronico: Bit = Field(alias="MP_Electronic check")
    pago_correo: Bit = Field(alias="MP_Mailed check")
    pago_transferencia: Bit = Field(alias="MP_Bank transfer (automatic)")
    Cargos_Mensuales: Annotated[float, Field(ge=0)]

    @model_validator(mode="after")
    def servicios_coherentes(self):
        if self.Internet_DSL + self.internet_fibra > 1:
            raise ValueError("DSL y fibra óptica son mutuamente excluyentes.")
        if self.pago_electronico + self.pago_correo + self.pago_transferencia > 1:
            raise ValueError("Solo se admite un método de pago.")
        if not self.Servicio_Telefono and self.Lineas_Multiples:
            raise ValueError("Las líneas múltiples requieren servicio telefónico.")
        if not (self.Internet_DSL or self.internet_fibra) and any([
            self.Seguridad_Online, self.Copia_Seguridad_Online,
            self.Proteccion_Dispositivos, self.Soporte_Tecnico,
            self.Streaming_TV, self.Streaming_Peliculas,
        ]):
            raise ValueError("Los servicios de internet requieren DSL o fibra óptica.")
        return self


COLUMNAS = [f.alias or name for name, f in Cliente.model_fields.items()]
Slot = Literal["modelo_1", "modelo_2"]


class Configuracion(Estricto):
    modelo_1: str
    modelo_2: str
    scaler: str
    umbral: Annotated[float, Field(gt=0, lt=1)]
    riesgo_medio: Annotated[float, Field(gt=0, lt=1)]
    riesgo_alto: Annotated[float, Field(gt=0, lt=1)]

    @model_validator(mode="after")
    def limites(self):
        if self.riesgo_medio >= self.riesgo_alto:
            raise ValueError("El umbral medio debe ser menor que el alto.")
        if self.modelo_1 == self.modelo_2:
            raise ValueError("Seleccione dos archivos de modelo distintos.")
        return self


class Peticion(Estricto):
    cliente: Cliente
    modelo: Slot = "modelo_1"


class Lote(Estricto):
    clientes: Annotated[list[Cliente], Field(min_length=1, max_length=10000)]


class Evaluacion(Lote):
    etiquetas: Annotated[list[Bit], Field(min_length=1, max_length=10000)]
    conjunto: Annotated[str, Field(min_length=1, max_length=200)]

    @model_validator(mode="after")
    def correspondencia(self):
        if len(self.clientes) != len(self.etiquetas):
            raise ValueError("Cada cliente debe tener exactamente una etiqueta.")
        if not self.conjunto.strip():
            raise ValueError("Identifique el conjunto de evaluación.")
        return self


class Prediccion(Estricto):
    modelo: str
    probabilidad: Annotated[float, Field(ge=0, le=1)]
    abandono: Literal["Yes", "No"]
    riesgo: Literal["Bajo", "Medio", "Alto"]
    umbral: float


class RespuestaLote(Estricto):
    modelo_1: list[Prediccion]
    modelo_2: list[Prediccion]


class Preparacion(Estricto):
    fuente: Annotated[str, Field(min_length=1, max_length=200)]
    filas: Annotated[list[dict[str, str | float | bool | None]], Field(min_length=1, max_length=10000)]
    eliminar_columnas: list[str] = Field(default_factory=list)
    eliminar_filas: list[Annotated[int, Field(ge=1, le=10000)]] = Field(default_factory=list)
    eliminar_nulos: bool = False
    entradas: dict[str, str]
    valores: dict[str, dict[str, float]] = Field(default_factory=dict)
    objetivo: str | None = None
    valores_objetivo: dict[str, Bit] = Field(default_factory=dict)
    aplicar_scaler: bool


class DatasetInferencia(Estricto):
    entrada: Annotated[list[dict[str, float]], Field(min_length=1, max_length=10000)]
    aplicar_scaler: bool
    revision_preparacion: str
    etiquetas: list[Bit] | None = None
    conjunto: Annotated[str, Field(min_length=1, max_length=200)]

    @model_validator(mode="after")
    def contrato(self):
        if any(set(row) != set(COLUMNAS) for row in self.entrada):
            raise ValueError("Se requieren exactamente las 20 entradas del modelo.")
        if self.etiquetas is not None and len(self.etiquetas) != len(self.entrada):
            raise ValueError("Las etiquetas deben corresponder una a una a las filas.")
        return self
