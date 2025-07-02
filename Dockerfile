# Usa una imagen ofical de Python ligera
FROM python:3.12-slim

# Crea el directorio de trabajo
WORKDIR /app

# Copia los archivos del proyecto
COPY . /app

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto (opcional, por si luegos alojas una API)
EXPOSE 8000

# Comando para ejecutar el bot
CMD ["python", "bot.py"]