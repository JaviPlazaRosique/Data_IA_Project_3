from __future__ import annotations

import calendar
import logging
import re
from datetime import date, datetime, timedelta
from functools import lru_cache
from typing import Any
from zoneinfo import ZoneInfo

import dateparser
from google.api_core.exceptions import GoogleAPICallError

from agent.services.bigquery_service import BigQueryRagService, BigQueryServiceError
from agent.services.embedding_service import EmbeddingService, EmbeddingError


@lru_cache(maxsize=1)
def _bigquery_service() -> BigQueryRagService:
    return BigQueryRagService()


@lru_cache(maxsize=1)
def _embedding_service() -> EmbeddingService:
    return EmbeddingService()

logger = logging.getLogger(__name__)


_TZ = ZoneInfo("Europe/Madrid")

CATEGORIAS_VALIDAS = ["Música", "Arte y Teatro", "Deportes", "Familia y otros"]
FRANJAS_VALIDAS_BD = ["mañana", "tarde", "noche"]

_MESES_ES = {
    "enero": 1, "ene": 1,
    "febrero": 2, "feb": 2,
    "marzo": 3, "mar": 3,
    "abril": 4, "abr": 4,
    "mayo": 5, "may": 5,
    "junio": 6, "jun": 6,
    "julio": 7, "jul": 7,
    "agosto": 8, "ago": 8,
    "septiembre": 9, "setiembre": 9, "sep": 9, "sept": 9,
    "octubre": 10, "oct": 10,
    "noviembre": 11, "nov": 11,
    "diciembre": 12, "dic": 12,
}

_RANGO_RE = re.compile(
    r"(?:del?|entre(?:\s+el)?)\s+(\d{1,2})"
    r"(?:\s+de\s+(\w+))?"
    r"\s+(?:al?|y(?:\s+el)?)\s+(\d{1,2})"
    r"(?:\s+de\s+(\w+))?",
    re.IGNORECASE,
)

_WEEKDAYS = {
    "lunes": 0,
    "martes": 1,
    "miércoles": 2, "miercoles": 2,
    "jueves": 3,
    "viernes": 4,
    "sábado": 5, "sabado": 5,
    "domingo": 6,
}

_FRANJAS = {
    "tarde": ("por la tarde", "esta tarde", "de tarde"),
    "noche": ("por la noche", "esta noche", "de noche", "de madrugada", "por la madrugada", "esta madrugada"),
    "mañana": ("por la mañana", "esta mañana", "de mañana"),
}


def calcular_rango_fechas(referencia: str, fecha_actual: str | None = None) -> dict[str, str | None]:
    """Convierte una referencia temporal en español a fechas y franja horaria.

    Args:
        referencia: Expresión temporal en lenguaje natural ("esta noche",
            "este finde", "el viernes que viene", "esta semana", etc.).
        fecha_actual: Fecha de hoy en formato 'YYYY-MM-DD'. Si se omite, se
            usa el reloj del servidor (Europe/Madrid). Útil para tests
            deterministas: permite inyectar una "hoy" fija sin mockear datetime.

    Returns:
        dict con:
          - date_from y date_to en formato YYYY-MM-DD (o None)
          - franja_horaria: 'mañana' | 'tarde' | 'noche' (o None)
        Pasa estos valores directamente como parámetros a rag_search.
    """
    today = date.fromisoformat(fecha_actual) if fecha_actual else datetime.now(_TZ).date()
    wd = today.weekday()  # 0=lunes … 6=domingo
    ref = referencia.lower().strip()
    result: dict[str, str | None] = {"date_from": None, "date_to": None, "franja_horaria": None}

    franja_detectada: str | None = None
    ref_sin_franjas = ref
    for franja, frases in _FRANJAS.items():
        for frase in frases:
            if frase in ref_sin_franjas:
                franja_detectada = franja
                ref_sin_franjas = ref_sin_franjas.replace(frase, " ")
    result["franja_horaria"] = franja_detectada

    def _set(d_from: date, d_to: date) -> dict[str, str | None]:
        result["date_from"] = d_from.isoformat()
        result["date_to"] = d_to.isoformat()
        return result

    if "pasado mañana" in ref_sin_franjas or "pasado manana" in ref_sin_franjas:
        d = today + timedelta(days=2)
        return _set(d, d)

    if "anteayer" in ref_sin_franjas:
        d = today - timedelta(days=2)
        return _set(d, d)

    if "ayer" in ref_sin_franjas:
        d = today - timedelta(days=1)
        return _set(d, d)

    if "hoy" in ref_sin_franjas:
        return _set(today, today)

    if "mañana" in ref_sin_franjas:
        d = today + timedelta(days=1)
        return _set(d, d)

    rango_match = _RANGO_RE.search(ref)
    if rango_match:
        d1, mes1_txt, d2, mes2_txt = rango_match.groups()
        try:
            mes2 = _MESES_ES.get((mes2_txt or "").lower()) if mes2_txt else None
            mes1 = _MESES_ES.get((mes1_txt or "").lower()) if mes1_txt else mes2
            if mes2 is None:
                mes2 = mes1
            if mes1 and mes2:
                year_from = today.year if mes1 >= today.month else today.year + 1
                year_to = year_from if mes2 >= mes1 else year_from + 1
                d_from = date(year_from, mes1, int(d1))
                d_to = date(year_to, mes2, int(d2))
                return _set(d_from, d_to)
        except ValueError:
            pass

    if any(x in ref for x in ("esta semana", "esta misma semana")):
        sunday = today + timedelta(days=(6 - wd) % 7)
        return _set(today, sunday)

    if any(x in ref for x in ("fin de semana", "finde", "este sábado", "este sabado")):
        if wd == 5:  # sábado: el finde es hoy + mañana
            return _set(today, today + timedelta(days=1))
        if wd == 6:  # domingo: el finde es solo hoy (último día)
            return _set(today, today)
        saturday = today + timedelta(days=(5 - wd) % 7)
        sunday = saturday + timedelta(days=1)
        return _set(saturday, sunday)

    if any(x in ref for x in ("semana que viene", "próxima semana", "proxima semana", "semana siguiente")):
        next_monday = today + timedelta(days=(7 - wd) % 7 or 7)
        next_sunday = next_monday + timedelta(days=6)
        return _set(next_monday, next_sunday)

    for nombre, idx in _WEEKDAYS.items():
        if nombre not in ref_sin_franjas:
            continue
        es_proximo = any(
            p in ref for p in (
                f"{nombre} que viene", f"próximo {nombre}", f"proximo {nombre}",
                f"{nombre} próximo", f"{nombre} proximo", f"{nombre} siguiente",
            )
        )
        days_ahead = (idx - wd) % 7
        if es_proximo:
            days_ahead += 7
        target = today + timedelta(days=days_ahead)
        return _set(target, target)

    if any(x in ref for x in ("este mes", "este mismo mes")):
        last_day = calendar.monthrange(today.year, today.month)[1]
        return _set(today, today.replace(day=last_day))

    if any(x in ref for x in ("próximo mes", "proximo mes", "el mes que viene")):
        if today.month == 12:
            first = today.replace(year=today.year + 1, month=1, day=1)
        else:
            first = today.replace(month=today.month + 1, day=1)
        last_day = calendar.monthrange(first.year, first.month)[1]
        return _set(first, first.replace(day=last_day))

    if any(x in ref for x in ("fin de mes", "final de mes", "finales de mes", "fin del mes")):
        last_day = calendar.monthrange(today.year, today.month)[1]
        start = today.replace(day=max(today.day, last_day - 6))
        return _set(start, today.replace(day=last_day))

    if any(x in ref for x in ("principio de mes", "principios de mes", "comienzo de mes")):
        if today.day < 7:
            return _set(today, today.replace(day=7))
        if today.month == 12:
            first = today.replace(year=today.year + 1, month=1, day=1)
        else:
            first = today.replace(month=today.month + 1, day=1)
        return _set(first, first.replace(day=7))

    iso_match = re.fullmatch(r"\s*(\d{4})-(\d{1,2})-(\d{1,2})\s*", ref)
    if iso_match:
        try:
            d = date(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
            return _set(d, d)
        except ValueError:
            pass

    ref_limpia = re.sub(r"^(el|la|los|las|para|este|esta)\s+", "", ref_sin_franjas).strip()
    parsed = dateparser.parse(
        ref_limpia or referencia,
        languages=["es"],
        settings={
            "RELATIVE_BASE": datetime.combine(today, datetime.min.time()),
            "PREFER_DATES_FROM": "future",
            "DATE_ORDER": "DMY",
        },
    )
    if parsed:
        d = parsed.date()
        return _set(d, d)

    if franja_detectada:
        return _set(today, today)

    result["nota"] = f"Referencia no reconocida: '{referencia}'"
    return result


def _agrupar_sesiones(rows: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
    """Colapsa filas con mismo `id` (mismo evento) en una sola entrada con sesiones[].

    BigQuery puede devolver varias filas del mismo evento si tiene varias sesiones
    (distintas fechas/franjas) que caen dentro del rango filtrado. Aquí las juntamos
    en un único dict con `sesiones` como lista ordenada de {fecha, franja_horaria}.
    """
    grupos: dict[str, dict[str, Any]] = {}
    orden: list[str] = []
    for row in rows:
        clave = row.get("id") or ""
        sesion = {"fecha": row.get("fecha_evento"), "franja_horaria": row.get("franja_horaria")}
        if clave not in grupos:
            grupos[clave] = {
                "id": row.get("id"),
                "title": row.get("title"),
                "category": row.get("category"),
                "ciudad": row.get("ciudad"),
                "content": row.get("content"),
                "source_url": row.get("source_url"),
                "distance": row.get("distance"),
                "sesiones": [sesion],
            }
            orden.append(clave)
        else:
            existing = grupos[clave]
            if sesion not in existing["sesiones"]:
                existing["sesiones"].append(sesion)
            new_distance = row.get("distance")
            if new_distance is not None and (
                existing["distance"] is None or new_distance < existing["distance"]
            ):
                existing["distance"] = new_distance
    for clave in orden:
        grupos[clave]["sesiones"].sort(key=lambda s: (s["fecha"] or "", s["franja_horaria"] or ""))
    return [grupos[c] for c in orden[:top_k]]


def rag_search(
    question: str,
    top_k: int = 5,
    category: str | None = None,
    ciudad: str | None = None,
    franja_horaria: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    """Busca eventos afines en BigQuery VECTOR_SEARCH usando la pregunta del usuario.

    Cuando un evento tiene varias sesiones (mismo evento en distintos días u horarios)
    que caen dentro del rango filtrado, se devuelve UNA sola entrada con todas las
    sesiones agrupadas en `sesiones`. Menciónalas todas al usuario para que pueda elegir.

    Args:
        question: Descripción del plan o evento que busca el usuario.
        top_k: Número máximo de eventos únicos (1-20).
        category: Filtro opcional de categoría (ej: 'Música', 'Deportes').
        ciudad: Filtro exacto de ciudad (ej: 'Barcelona', 'Madrid').
        franja_horaria: Filtro de horario (ej: 'mañana', 'tarde', 'noche').
        date_from: Fecha mínima del evento en formato YYYY-MM-DD (opcional).
            Si no se pasa, se filtra automáticamente desde la fecha de hoy:
            nunca se devuelven eventos pasados.
        date_to: Fecha máxima del evento en formato YYYY-MM-DD (opcional).

    Returns:
        dict con:
          - count: nº de eventos únicos.
          - results: lista de eventos. Cada evento incluye sus campos más
            `sesiones`: lista de {fecha, franja_horaria} en las que está disponible.
    """
    try:
        top_k_raw = max(top_k * 4, 20)
        rows = _bigquery_service().rag_search(
            question,
            _embedding_service(),
            top_k=top_k_raw,
            category=category,
            ciudad=ciudad,
            franja_horaria=franja_horaria,
            date_from=date_from,
            date_to=date_to,
        )
        eventos = _agrupar_sesiones(rows, top_k=top_k)
        logger.info(
            "rag_tool_done",
            extra={"rows": len(rows), "eventos_unicos": len(eventos)},
        )
        return {"source": "bigquery_rag", "count": len(eventos), "results": eventos}
    except (BigQueryServiceError, EmbeddingError, ValueError, GoogleAPICallError) as exc:
        logger.warning(
            "rag_tool_error",
            extra={"error_type": type(exc).__name__, "error": str(exc)},
        )
        return {"source": "bigquery_rag", "error": str(exc)}


def buscar_eventos(
    question: str,
    referencia_temporal: str | None = None,
    ciudad: str | None = None,
    category: str | None = None,
    top_k: int = 5,
) -> dict[str, Any]:
    """Pipeline completo de búsqueda de eventos.

    Orquesta internamente las llamadas que antes hacía el agente paso a paso:
    1. Si hay referencia_temporal, obtiene la fecha real y la traduce a rango ISO + franja.
    2. Llama a rag_search con todos los filtros y devuelve los eventos agrupados por sesión.

    Args:
        question: parte semántica de la búsqueda (sin ciudad, sin fecha, sin franja).
        referencia_temporal: expresión literal del usuario ("esta noche", "este finde", …) o None.
        ciudad: ciudad española o None.
        category: una de "Música" | "Arte y Teatro" | "Deportes" | "Familia y otros", o None.
        top_k: nº máximo de eventos únicos a devolver.

    Returns:
        Mismo dict que rag_search: {source, count, results} con `sesiones` por evento.
    """
    franja: str | None = None
    date_from: str | None = None
    date_to: str | None = None

    if referencia_temporal:
        rango = calcular_rango_fechas(referencia_temporal)
        franja = rango.get("franja_horaria")
        date_from = rango.get("date_from")
        date_to = rango.get("date_to")

    return rag_search(
        question=question,
        top_k=top_k,
        category=category,
        ciudad=ciudad,
        franja_horaria=franja,
        date_from=date_from,
        date_to=date_to,
    )