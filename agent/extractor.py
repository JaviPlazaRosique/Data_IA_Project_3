from __future__ import annotations

import re
from typing import Literal

from google.adk.agents import LlmAgent
from pydantic import BaseModel, Field, field_validator

from agent.config import get_settings


CategoriaBD = Literal["Música", "Arte y Teatro", "Deportes", "Familia y otros"]

_QUESTION_MAX_LEN = 150
_INJECTION_MARKERS = re.compile(
    r"(?i)\b(system|assistant|user|instruction|ignore|olvida|reveal|revela|prompt)\s*[:>]"
)


class UserQueryExtract(BaseModel):
    """Campos extraíbles directamente del mensaje del usuario."""

    question: str | None = Field(
        default=None,
        description=(
            "Parte semántica de la petición de planes, sin ciudad, sin fecha y sin franja horaria. "
            "Tres valores posibles: "
            "(a) cadena con la descripción del plan ('concierto romántico', 'partido emocionante') "
            "cuando el usuario pide un plan ESPECÍFICO; "
            "(b) null cuando el usuario pide planes pero de forma GENÉRICA, sin describir el tipo "
            "('qué planes hay', 'algo para hacer', 'recomiéndame un plan'); "
            "(c) cadena vacía cuando el usuario NO está pidiendo planes (saludo, despedida, "
            "agradecimiento, pregunta casual o fuera de dominio)."
        ),
    )
    ciudad: str | None = Field(
        default=None,
        description=(
            "Ciudad española mencionada explícitamente por el usuario "
            "(ej: 'Barcelona', 'Madrid'). null si no menciona ninguna."
        ),
    )
    category: CategoriaBD | None = Field(
        default=None,
        description=(
            "Categoría de BD. Mapeo: "
            "'concierto'/'festival'/'música' → 'Música'; "
            "'teatro'/'comedia'/'musical'/'ballet'/'danza'/'circo' → 'Arte y Teatro'; "
            "'fútbol'/'baloncesto'/'tenis'/'motor'/'ciclismo'/'partido' → 'Deportes'; "
            "'con niños'/'familiar'/'exposición'/'visita guiada'/'parque temático' → 'Familia y otros'. "
            "null si no encaja claramente en ninguna."
        ),
    )
    referencia_temporal: str | None = Field(
        default=None,
        description=(
            "Expresión temporal LITERAL usada por el usuario ('esta noche', 'este finde', "
            "'mañana por la tarde', 'el viernes que viene', 'esta semana'…). "
            "NO calcules fechas ISO: copia la frase tal cual. "
            "null si el usuario no menciona ninguna referencia temporal."
        ),
    )

    @field_validator("question", mode="after")
    @classmethod
    def _sanitize_question(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.replace("\r", " ").replace("\n", " ").strip()
        cleaned = _INJECTION_MARKERS.sub(" ", cleaned)
        cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
        return cleaned[:_QUESTION_MAX_LEN]


_EXTRACTOR_INSTRUCTION = """
Eres un extractor de parámetros para un sistema de recomendación de eventos en España.
Recibes la pregunta del usuario en lenguaje natural y devuelves SOLO un JSON conforme al
schema UserQueryExtract. No saludes, no expliques, no añadas texto fuera del JSON.

VALOR DEL CAMPO `question` (tres casos):
- TEXTO con la parte semántica del plan: cuando el usuario pide un plan ESPECÍFICO
  (ej: "concierto romántico", "partido emocionante", "algo para hacer con niños").
  Quita ciudad, fecha y franja horaria del texto.
- null: cuando el usuario pide planes pero de forma GENÉRICA, sin describir qué tipo
  de plan quiere ("qué planes hay", "qué hacer", "algo para hacer", "recomiéndame un
  plan"). NUNCA inventes una descripción tipo "plan variado": pon null y deja que el
  sistema devuelva variedad real.
- "": cuando el usuario NO está pidiendo planes (saludo, despedida, agradecimiento,
  pregunta casual o fuera de dominio).

Reglas estrictas para los otros campos:
- ciudad: el nombre tal cual lo dijo el usuario. null si no se menciona ninguna.
- category: una de las 4 válidas, o null si no es claro.
- REGLA CRÍTICA de category: solo asigna una categoría si el usuario usa una palabra
  que claramente la identifica (ej: "concierto" → "Música", "teatro" → "Arte y Teatro",
  "fútbol" → "Deportes", "con niños" → "Familia y otros"). Para preguntas genéricas
  category SIEMPRE es null.
- referencia_temporal: copia LITERAL de la expresión temporal del usuario.
  NO devuelvas fechas ISO ni intentes calcularlas. null si no hay referencia temporal.

Ejemplos:
Usuario: "concierto romántico en Barcelona esta noche"
→ {"question": "concierto romántico", "ciudad": "Barcelona",
   "category": "Música", "referencia_temporal": "esta noche"}

Usuario: "algo para hacer con niños este finde"
→ {"question": "algo para hacer con niños", "ciudad": null,
   "category": "Familia y otros", "referencia_temporal": "este finde"}

Usuario: "recomiéndame un plan"
→ {"question": null, "ciudad": null,
   "category": null, "referencia_temporal": null}

Usuario: "qué se puede hacer en Valencia"
→ {"question": null, "ciudad": "Valencia",
   "category": null, "referencia_temporal": null}

Usuario: "qué planes hay este finde"
→ {"question": null, "ciudad": null,
   "category": null, "referencia_temporal": "este finde"}

Usuario: "algo para hacer en Madrid mañana por la noche"
→ {"question": null, "ciudad": "Madrid",
   "category": null, "referencia_temporal": "mañana por la noche"}

Usuario: "hola, ¿cómo estás?"
→ {"question": "", "ciudad": null,
   "category": null, "referencia_temporal": null}

Usuario: "gracias!"
→ {"question": "", "ciudad": null,
   "category": null, "referencia_temporal": null}

Usuario: "adiós, hasta luego"
→ {"question": "", "ciudad": null,
   "category": null, "referencia_temporal": null}

Usuario: "¿quién ganó el mundial de fútbol de 2022?"
→ {"question": "", "ciudad": null,
   "category": null, "referencia_temporal": null}
"""


def build_extractor_agent() -> LlmAgent:
    settings = get_settings()
    return LlmAgent(
        name="user_query_extractor",
        model=settings.agent_model,
        instruction=_EXTRACTOR_INSTRUCTION,
        description="Extrae question, ciudad, category y referencia_temporal del mensaje del usuario.",
        output_schema=UserQueryExtract,
        output_key="extracted_query",
    )


extractor_agent = build_extractor_agent()
