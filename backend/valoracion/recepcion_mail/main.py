import logging
import os
from datetime import datetime, timezone

import functions_framework
from google.cloud import bigquery
from jose import jwt
from jose.exceptions import JWTError

logger = logging.getLogger(__name__)

clave_jwt     = os.getenv("JWT_SECRET_KEY")
algoritmo_jwt = os.getenv("JWT_ALGORITHM", "HS256")
id_proyecto   = os.getenv("GOOGLE_CLOUD_PROJECT")
id_dataset    = os.getenv("BQ_DATASET_ID", "recomendacion_planes")
id_tabla      = os.getenv("BQ_TABLE_ID", "valoraciones_eventos")

cliente_bq = bigquery.Client(project=id_proyecto)


def validar_token(token):
    try:
        payload = jwt.decode(token, clave_jwt, algorithms=[algoritmo_jwt])
        if payload.get("type") != "rating":
            return None
        return payload
    except JWTError:
        return None


def guardar_valoracion(id_usuario, id_evento, nombre_evento, valoracion):
    tabla = f"{id_proyecto}.{id_dataset}.{id_tabla}"
    fila = {
        "id_usuario":     id_usuario,
        "id_evento":      id_evento,
        "nombre_evento":  nombre_evento,
        "valoracion":     valoracion,
        "fecha_valoracion": datetime.now(timezone.utc).isoformat(),
    }
    errores = cliente_bq.insert_rows_json(tabla, [fila])
    if errores:
        raise RuntimeError(f"Error insertando en BigQuery: {errores}")


def pagina_confirmacion(nombre_evento, valoracion):
    emoji   = "👍" if valoracion == "like" else "👎"
    mensaje = "¡Nos alegramos!" if valoracion == "like" else "¡Gracias por contárnoslo!"

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Valoración registrada</title>
</head>
<body style="margin:0;padding:0;background:#f0eeff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:80px 20px;">
      <table width="480" cellpadding="0" cellspacing="0"
             style="max-width:480px;background:#ffffff;border-radius:20px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
        <tr>
          <td style="background:linear-gradient(135deg,#7c3aed,#4f46e5);padding:36px;text-align:center;">
            <div style="font-size:36px;margin-bottom:6px;">⚡</div>
            <h1 style="color:#ffffff;margin:0;font-size:22px;font-weight:800;letter-spacing:-0.5px;">
              The Electric Curator
            </h1>
          </td>
        </tr>
        <tr>
          <td style="padding:48px 40px;text-align:center;">
            <div style="font-size:64px;margin-bottom:16px;">{emoji}</div>
            <h2 style="color:#1a1a2e;font-size:22px;margin:0 0 12px;font-weight:700;">
              Valoración registrada
            </h2>
            <p style="color:#6b7280;font-size:15px;margin:0;line-height:1.6;">
              {mensaje} Tu opinión sobre
              <strong style="color:#1a1a2e;">{nombre_evento}</strong>
              nos ayuda a mejorar las recomendaciones.
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def pagina_error(mensaje):
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Error</title>
</head>
<body style="margin:0;padding:0;background:#f0eeff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:80px 20px;">
      <div style="max-width:480px;background:#ffffff;border-radius:20px;padding:48px 40px;
                  text-align:center;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
        <div style="font-size:48px;margin-bottom:16px;">⚠️</div>
        <h2 style="color:#1a1a2e;margin:0 0 8px;font-size:20px;">{mensaje}</h2>
      </div>
    </td></tr>
  </table>
</body>
</html>"""


cabeceras_html = {"Content-Type": "text/html; charset=utf-8"}


@functions_framework.http
def recibir_valoracion(request):
    token     = request.args.get("token")
    valoracion = request.args.get("rating")

    if not token:
        return (pagina_error("Enlace no válido"), 400, cabeceras_html)

    if valoracion not in ("like", "dislike"):
        return (pagina_error("Valoración no reconocida"), 400, cabeceras_html)

    payload = validar_token(token)
    if not payload:
        return (pagina_error("El enlace ha caducado o ya no es válido"), 400, cabeceras_html)

    id_usuario    = payload.get("sub")
    id_evento     = payload.get("event_id")
    nombre_evento = payload.get("event_name") or "el evento"

    try:
        guardar_valoracion(id_usuario, id_evento, nombre_evento, valoracion)
        logger.info("Valoración guardada: usuario=%s evento=%s valoracion=%s", id_usuario, id_evento, valoracion)
        return (pagina_confirmacion(nombre_evento, valoracion), 200, cabeceras_html)
    except Exception:
        logger.exception("Error al guardar valoración en BigQuery")
        return (pagina_error("Error al registrar tu valoración. Inténtalo de nuevo."), 500, cabeceras_html)
