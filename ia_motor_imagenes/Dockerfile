FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Variable de entorno para la imagen
ENV GOOGLE_CLOUD_PROJECT=${id_proyecto}

# Comando de ejecución
CMD ["python", "main.py"]