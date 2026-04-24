from pydantic import BaseModel, ConfigDict


class NearbyPlace(BaseModel):
    model_config = ConfigDict(extra="ignore")

    nombre: str | None = None
    direccion: str | None = None
    rating: float | None = None
    distancia_m: float | None = None


class AntelacionRecomendada(BaseModel):
    model_config = ConfigDict(extra="ignore")

    minutos_antelacion: int | None = None
    motivo: str | None = None


class EventRead(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    nombre: str | None = None
    url: str | None = None
    fecha: str | None = None
    hora: str | None = None
    fecha_utc: str | None = None
    estado: str | None = None
    venta_inicio: str | None = None
    venta_fin: str | None = None
    segmento: str | None = None
    genero: str | None = None
    subgenero: str | None = None
    recinto_id: str | None = None
    recinto_nombre: str | None = None
    ciudad: str | None = None
    direccion: str | None = None
    latitud: float | None = None
    longitud: float | None = None
    artista_id: str | None = None
    artista_nombre: str | None = None
    artista_imagen: str | None = None
    imagen_evento: str | None = None
    promotor: str | None = None
    restaurantes_cercanos: list[NearbyPlace] = []
    alojamientos_cercanos: list[NearbyPlace] = []
    antelacion_recomendada: AntelacionRecomendada | None = None
