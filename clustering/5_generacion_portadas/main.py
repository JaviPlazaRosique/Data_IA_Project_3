import os
import pandas as pd
import urllib.request
import ssl
import time
import re
import unicodedata
from urllib.parse import quote
from google import genai
from google.cloud import storage, bigquery

# ==========================================
# 1. CONFIGURACIÓN Y PARCHE DE SEGURIDAD
# ==========================================
ssl._create_default_https_context = ssl._create_unverified_context

PROJECT_ID = "project3grupo3"
LOCATION_VERTEX = "europe-west1" # Región para la IA (Gemini)
LOCATION_BQ = "EU"    # ⚠️ Región de BigQuery (Cámbialo a "EU" si te sigue dando error)
BUCKET_NAME = f"portadas-{PROJECT_ID}"

# Inicialización de Clientes
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET_NAME)
ai_client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION_VERTEX)

# AQUÍ ESTÁ LA SOLUCIÓN: Le decimos a BigQuery que busque en Europa
bq_client = bigquery.Client(project=PROJECT_ID, location=LOCATION_BQ)

# ==========================================
# 2. FUNCIONES AUXILIARES
# ==========================================
def slugify(value):
    """Convierte el nombre del evento en un nombre de archivo limpio."""
    value = str(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    return re.sub(r'[-\s]+', '-', value)

# ==========================================
# 3. CONEXIÓN A BIGQUERY (RAG)
# ==========================================
def obtener_eventos_con_contexto_bq():
    """Descarga los eventos y su contexto RAG."""
    print(f"📥 Conectando a BigQuery (Región: {LOCATION_BQ}) para descargar el contexto RAG...")
    
    query = f"""
        SELECT 
            nombre, 
            contexto_rag
        FROM `{PROJECT_ID}.recomendacion_planes.eventos`
        WHERE contexto_rag IS NOT NULL
    """
    try:
        df_bq = bq_client.query(query).to_dataframe()
        df_unicos = df_bq.drop_duplicates(subset=['nombre'])
        print(f"✅ Descargados {len(df_unicos)} eventos únicos con contexto desde BigQuery.")
        return df_unicos
    except Exception as e:
        print(f"❌ Error al conectar con BigQuery: {e}")
        return pd.DataFrame()

# ==========================================
# 4. DIRECTOR DE ARTE IA (GEMINI)
# ==========================================
def generar_descripcion_fondos(nombre_evento, contexto_rag):
    """Crea el escenario vacío basado en el contexto."""
    prompt = (
        f"Read this event context carefully: '{contexto_rag}'. "
        "Based EXACTLY on this context, create a prompt for a background image representing the atmosphere of the venue. "
        "CRITICAL RULES: NO PEOPLE, NO FACES, NO CROWDS, NO SILHOUETTES, NO TEXT. "
        "Start your description exactly with: 'Empty background, zero people, ...' "
        "Write only the visual description in English, 8k resolution, cinematic lighting."
    )
    try:
        res = ai_client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        return res.text.strip() if (res and res.text) else f"Empty background, zero people, cinematic atmosphere of {nombre_evento}"
    except:
        return f"Empty background, zero people, atmospheric professional photography representing {nombre_evento}"

# ==========================================
# 5. GENERACIÓN Y SUBIDA
# ==========================================
def procesar_evento(nombre_evento, contexto_rag):
    """Genera la imagen y la sube a GCS."""
    nombre_slug = slugify(nombre_evento)
    nombre_archivo = f"portadas/{nombre_slug}.jpg"
    blob = bucket.blob(nombre_archivo)

    # Forzamos la regeneración borrando el check de existencia
    print(f"🎨 Regenerando entorno basado en RAG para: {nombre_evento}")
    descripcion = generar_descripcion_fondos(nombre_evento, contexto_rag)
    
    prompt_final = quote(f"{descripcion[:180]}")
    url_api = f"https://image.pollinations.ai/prompt/{prompt_final}?width=768&height=1024&nologo=true&seed=42"

    for intento in range(3):
        try:
            req = urllib.request.Request(url_api, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=90) as response:
                blob.upload_from_string(response.read(), content_type='image/jpeg')
            print(f"✅ Subida con éxito: {nombre_slug}.jpg")
            time.sleep(30) 
            break
        except Exception as e:
            espera = 60 * (intento + 1)
            print(f"⚠️ Reintentando {nombre_evento} en {espera}s... ({e})")
            time.sleep(espera)

# ==========================================
# 6. EJECUCIÓN PRINCIPAL
# ==========================================
if __name__ == "__main__":
    df_eventos = obtener_eventos_con_contexto_bq()
    
    if not df_eventos.empty:
        print(f"🚀 Iniciando generación de imágenes...")
        for _, fila in df_eventos.iterrows():
            procesar_evento(fila['nombre'], fila['contexto_rag'])
    else:
        print("⚠️ No hay eventos para procesar o la tabla está vacía.")