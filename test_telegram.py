import requests
import os
from dotenv import load_dotenv

# Cargar las variables del .env
load_dotenv()

# Obtener token y chat ID
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

print("TOKEN:", TOKEN)
print("CHAT_ID:", CHAT_ID)


# Mensaje de prueba
mensaje = "✅ Hola Byron, tu bot de Uniqlo está funcionando correctamente."

# Comprobamos que haya datos
if not TOKEN or not CHAT_ID:
    print("❌ Error: TELEGRAM_TOKEN o TELEGRAM_CHAT_ID no están definidos en el .env")
else:
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": mensaje
    }

    response = requests.post(url, data=data)

    if response.status_code == 200:
        print("✅ Mensaje enviado correctamente.")
    else:
        print("❌ Error al enviar mensaje:", response.text)
