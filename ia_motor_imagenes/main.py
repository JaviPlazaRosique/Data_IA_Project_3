import os
import pandas as pd
import urllib.request
import ssl
import time
import re
import unicodedata
from urllib.parse import quote
from google import genai
from google.cloud import storage

# 1. CONFIGURACIÓN
ssl._create_default_https_context = ssl._create_unverified_context
PROJECT_ID = "project3grupo3"
LOCATION = "us-central1"
BUCKET_NAME = f"portadas-{PROJECT_ID}"
RUTA_CSV = "../3_generacion_interacciones_demo/outputs/real_events.csv"

# Clientes
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET_NAME)
ai_client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

def slugify(value):
    """Convierte el nombre del evento en un nombre seguro para archivos."""
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    return re.sub(r'[-\s]+', '-', value)

def generar_descripcion_sin_caras(nombre_evento):
    """
    Usa Gemini para crear un prompt que evite personas y se centre en el 'mood'.
    """
    prompt = (
        f"Analyze this event name: '{nombre_evento}'. "
        "I need a cinematic photo description for this event following these STRICT RULES: "
        "1. NO HUMAN FACES. No portraits of people. "
        "2. If it's a singer or concert, describe the stage, neon lights, musical instruments, or the crowd from behind/far away. "
        "3. If it's a celebrity, describe the 'mood' or the environment they represent (e.g., luxury, sport, art). "
        "4. Focus on texture, lighting, and atmosphere. "
        "Write only the visual description in English, high quality, 8k, professional photography."
    )
    try:
        res = ai_client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
        return res.text.strip() if (res and res.text) else f"Cinematic atmosphere of {nombre_evento}"
    except:
        return f"Artistic professional photography of {nombre_evento}, atmospheric lighting, no people"

def procesar_evento(nombre_evento):
    """Genera y sube la imagen evitando saturación."""
    nombre_slug = slugify(nombre_evento)
    nombre_archivo = f"portadas/{nombre_slug}.jpg"
    blob = bucket.blob(nombre_archivo)

    if blob.exists():
        print(f"⏩ Ya existe: {nombre_evento}")
        return

    print(f"🎨 Creando atmósfera para: {nombre_evento}")
    descripcion = generar_descripcion_sin_caras(nombre_evento)
    
    # Añadimos 'no people, no faces' al final del prompt para reforzar
    prompt_final = quote(f"{descripcion[:180]} - no people, no faces, cinematic mood")
    
    url_api = f"https://image.pollinations.ai/prompt/{prompt_final}?width=768&height=1024&nologo=true&seed=42"

    for intento in range(3):
        try:
            req = urllib.request.Request(url_api, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=60) as response:
                blob.upload_from_string(response.read(), content_type='image/jpeg')
            print(f"✅ Subida con éxito: {nombre_slug}.jpg")
            time.sleep(12) # Pausa generosa para evitar Error 429
            break
        except Exception as e:
            espera = 20 * (intento + 1)
            print(f"⚠️ Reintentando {nombre_evento} en {espera}s... ({e})")
            time.sleep(espera)

if __name__ == "__main__":
    if not os.path.exists(RUTA_CSV):
        print("❌ CSV no encontrado.")
    else:
        df = pd.read_csv(RUTA_CSV)
        eventos_unicos = df['nombre'].unique()
        
        print(f"🚀 Procesando {len(eventos_unicos)} eventos (Sin caras, solo mood).")
        
        for nombre in eventos_unicos:
            procesar_evento(nombre)