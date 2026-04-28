import logging
import os
from datetime import datetime, timedelta, timezone

import functions_framework
import psycopg2
import sendgrid
from jose import jwt
from sendgrid.helpers.mail import Mail

logger = logging.getLogger(__name__)

host_bd = os.getenv("DB_HOST")
nombre_bd = os.getenv("DB_NAME")
usuario_bd = os.getenv("DB_USER")
contrasena_bd = os.getenv("DB_PASSWORD")
clave_jwt = os.getenv("JWT_SECRET_KEY")
algoritmo_jwt = os.getenv("JWT_ALGORITHM", "HS256")
clave_sendgrid = os.getenv("SENDGRID_API_KEY")
email_remitente = os.getenv("SENDGRID_FROM_EMAIL", "noreply@theelectriccurator.com")
url_recepcion   = os.getenv("RECEPCION_EMAIL_FUNCTION_URL")
dias_expiracion = int(os.getenv("RATING_TOKEN_EXPIRE_DAYS", "30"))


def obtener_usuario(id_usuario):
    with psycopg2.connect(host=host_bd, dbname=nombre_bd, user=usuario_bd, password=contrasena_bd) as conexion:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT email, full_name FROM users WHERE id = %s", (id_usuario,))
            fila = cursor.fetchone()
            return (fila[0], fila[1]) if fila else (None, None)


def generar_token(id_usuario, id_evento, nombre_evento):
    payload = {
        "sub": id_usuario,
        "event_id": id_evento,
        "event_name": nombre_evento,
        "type": "rating",
        "exp": datetime.now(timezone.utc) + timedelta(days=dias_expiracion),
    }
    return jwt.encode(payload, clave_jwt, algorithm=algoritmo_jwt)


def construir_email(nombre_evento, url_base):
    url_me_gusta    = f"{url_base}&rating=like"
    url_no_me_gusta = f"{url_base}&rating=dislike"

    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f0eeff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:40px 20px;">
      <table width="600" cellpadding="0" cellspacing="0"
             style="max-width:600px;background:#ffffff;border-radius:20px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
        <tr>
          <td style="background:linear-gradient(135deg,#7c3aed,#4f46e5);padding:36px;text-align:center;">
            <div style="font-size:36px;margin-bottom:6px;">⚡</div>
            <h1 style="color:#ffffff;margin:0;font-size:22px;font-weight:800;letter-spacing:-0.5px;">
              The Electric Curator
            </h1>
          </td>
        </tr>
        <tr>
          <td style="padding:40px;text-align:center;">
            <h2 style="color:#1a1a2e;font-size:20px;margin:0 0 8px;font-weight:700;">
              ¿Te gustó el evento?
            </h2>
            <p style="color:#6b7280;margin:0 0 36px;font-size:15px;line-height:1.5;">
              Cuéntanos qué te pareció
              <strong style="color:#1a1a2e;">{nombre_evento}</strong>
            </p>
            <table cellpadding="0" cellspacing="0" style="margin:0 auto;">
              <tr>
                <td style="padding:0 12px;">
                  <a href="{url_me_gusta}"
                     style="display:inline-block;text-decoration:none;background:#4f46e5;color:#ffffff;
                            border-radius:16px;padding:18px 36px;font-size:28px;font-weight:700;
                            letter-spacing:-0.5px;min-width:120px;text-align:center;">
                    👍<br>
                    <span style="font-size:13px;font-weight:600;opacity:0.9;">Me gustó</span>
                  </a>
                </td>
                <td style="padding:0 12px;">
                  <a href="{url_no_me_gusta}"
                     style="display:inline-block;text-decoration:none;background:#f8f5ff;color:#1a1a2e;
                            border:2px solid #e0d7ff;border-radius:16px;padding:18px 36px;font-size:28px;
                            font-weight:700;letter-spacing:-0.5px;min-width:120px;text-align:center;">
                    👎<br>
                    <span style="font-size:13px;font-weight:600;color:#6b7280;">No me gustó</span>
                  </a>
                </td>
              </tr>
            </table>
            <p style="color:#9ca3af;font-size:12px;margin:36px 0 0;line-height:1.6;">
              Tu opinión nos ayuda a mejorar las recomendaciones.<br>
              Este enlace es válido durante {dias_expiracion} días.
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


@functions_framework.http
def enviar_email_valoracion(request):
    try:
        datos = request.get_json(silent=True) or {}
        id_usuario   = datos.get("user_id")
        id_evento    = datos.get("event_id")
        nombre_evento = datos.get("event_name") or "el evento"

        if not id_usuario or not id_evento:
            return ("Faltan campos obligatorios: user_id y event_id", 400)

        email, nombre = obtener_usuario(id_usuario)
        if not email:
            logger.warning("Usuario no encontrado: %s", id_usuario)
            return ("Usuario no encontrado", 404)

        token      = generar_token(id_usuario, id_evento, nombre_evento)
        url_pagina = f"{url_recepcion}?token={token}"

        cliente_sg = sendgrid.SendGridAPIClient(api_key=clave_sendgrid)
        mensaje = Mail(
            from_email=email_remitente,
            to_emails=email,
            subject=f"¿Te gustó {nombre_evento}?",
            html_content=construir_email(nombre_evento, url_pagina),
        )
        respuesta = cliente_sg.send(mensaje)

        if respuesta.status_code >= 400:
            logger.error("Error de SendGrid: status=%s body=%s", respuesta.status_code, respuesta.body)
            return ("Error al enviar el email", 500)

        logger.info("Email enviado a %s para evento %s", email, id_evento)
        return ("OK", 200)

    except Exception:
        logger.exception("Error inesperado en enviar_email_valoracion")
        return ("Error interno", 500)
