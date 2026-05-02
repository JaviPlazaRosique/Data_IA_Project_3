from pydantic import BaseModel


class ClusterRecommendationRead(BaseModel):
    event_id: str
    event_name: str | None = None
    fecha_evento: str | None = None
    ciudad: str | None = None
    recinto_nombre: str | None = None
    segmento: str | None = None
    genero: str | None = None
    subgenero: str | None = None
    recommendation_rank: int
    recommendation_score: float
    cluster_source: str
