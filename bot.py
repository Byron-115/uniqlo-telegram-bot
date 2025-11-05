import requests
import json
import os
import html
from datetime import datetime
from dotenv import load_dotenv
import time

# --- IMPORTACIONES PARA EL SERVIDOR WEB ---
from threading import Thread
from flask import Flask
from waitress import serve

# --- CONFIGURACIÓN DE FLASK ---
# Creamos servidor web fake para que Railway no cierre el bot por inactividad
app = Flask(__name__)

@app.route('/')
def health_check():
    # Esta es la ruta que Railway usará para comprobar que el bot está activo
    return "Bot de Uniqlo activo", 200

def run_flask_app():
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

# --- FIN CONFIGURACIÓN DE FLASK ---



# --- CONFIGURACIÓN ---
# Cargar claves desde .env (TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- OBJETIVOS DE LA BÚSQUEDA ---
#PRODUCT_ID = "E468756-000"
PRODUCT_ID = "E469400-000"
#COLOR_OBJETIVO_CODE = "61"
#COLOR_OBJETIVO_NOMBRE = "AZUL"
TALLAS_OBJETIVO = {"003", "S"}  

# URLs
API_URL = "https://www.uniqlo.com/es/api/commerce/v5/es/products?path=37609%2C%2C%2C&flagCodes=discount&genderId=37609&offset=0&limit=36&imageRatio=3x4&httpFailure=true"
PRODUCT_URL = f"https://www.uniqlo.com/es/es/products/{PRODUCT_ID}/01?colorDisplayCode=30&sizeDisplayCode=008"

# Archivo para evitar notificaciones repetidas
ESTADO_PATH = "estado_oferta_notificada.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "x-fr-clientid": "uq.es.web-spa"
}
# --- FIN DE LA CONFIGURACIÓN ---


import json 

def comprobar_oferta():
    """
    Busca el producto en TODAS las páginas de la API de ofertas y comprueba si
    cumple las condiciones. VERSIÓN CORREGIDA FINAL.
    """
    print(f"🔗 Consultando API en busca de ofertas para {PRODUCT_ID}...")
    
    offset = 0
    limit = 36
    producto_encontrado_en_ofertas = False

    while True:
        paginated_api_url = f"https://www.uniqlo.com/es/api/commerce/v5/es/products?path=37609%2C%2C%2C&flagCodes=discount&genderId=37609&offset={offset}&limit={limit}&imageRatio=3x4&httpFailure=true"
        
        print(f"   - Revisando página (offset={offset})...")

        try:
            res = requests.get(paginated_api_url, headers=HEADERS, timeout=15)
            res.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error al conectar con la API en la página {offset}: {e}")
            return

        data = res.json().get("result", {})
        items = data.get("items", [])

        if not items:
            print("   - No hay más productos en la lista. Fin de la búsqueda.")
            break

        for item in items:
            if item.get("productId") != PRODUCT_ID:
                continue

            producto_encontrado_en_ofertas = True
            print(f"✅ ¡Producto {PRODUCT_ID} encontrado en la lista de ofertas! Comprobando tallas y precio...")

            precios = item.get("prices", {})
            promo_activa = precios.get("promo") is not None
            
            # <-- CAMBIO CLAVE: La comprobación de stock se simplifica
            tallas_disponibles_objetivo = []
            for size in item.get("sizes", []):
                # Si la talla está en la lista, asumimos que tiene stock
                if size.get("name") in TALLAS_OBJETIVO or size.get("displayCode") in TALLAS_OBJETIVO:
                    tallas_disponibles_objetivo.append(size.get("name") or size.get("displayCode"))

            hay_talla_objetivo_con_stock = len(tallas_disponibles_objetivo) > 0

            print(f"   - ¿Promo activa?: {'Sí' if promo_activa else 'No'}")
            print(f"   - ¿Stock en {', '.join(TALLAS_OBJETIVO)}?: {'Sí' if hay_talla_objetivo_con_stock else 'No'}")

            if promo_activa and hay_talla_objetivo_con_stock:
                id_unico_oferta = f"{PRODUCT_ID}"
                
                if ya_notificado(id_unico_oferta):
                    print("🤫 Oferta ya notificada previamente. No se enviará de nuevo.")
                else:
                    print("🎉 ¡OFERTA ENCONTRADA! Enviando notificación...")
                    nombre = item.get("name", "Producto sin nombre")
                    precio_promo = precios.get("promo", {}).get("value", "N/A")
                    precio_base = precios.get("base", {}).get("value", "N/A")
                    
                    mensaje = (
                        f"🚨 <b>¡Oferta encontrada!</b>\n"
                        f"<a href='{PRODUCT_URL}'>{html.escape(nombre)}</a>\n\n"
                        f"💰 <b>Precio: {precio_promo}€</b> (antes {precio_base}€)\n"
                        f"📏 <b>Tallas disponibles:</b> {', '.join(sorted(set(tallas_disponibles_objetivo)))}"
                    )
            
                    enviar_telegram(mensaje)
                    marcar_como_notificado(id_unico_oferta)
                
                return
        
        offset += limit

    if not producto_encontrado_en_ofertas:
        print(f"❌ El producto {PRODUCT_ID} no se encuentra actualmente en la lista de ofertas.")
        id_unico_oferta = f"{PRODUCT_ID}"
        if ya_notificado(id_unico_oferta):
            print("🗑️ La oferta previamente notificada ya no está disponible. Reseteando estado.")
            # resetear_notificacion(id_unico_oferta) # Puedes descomentar esto

def enviar_telegram(mensaje):
    """Envía un mensaje a través del bot de Telegram."""
    if not TOKEN or not CHAT_ID:
        print("❗️ Tokens de Telegram no configurados.")
        return
        
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "HTML", "disable_web_page_preview": False}
    
    try:
        res = requests.post(url, data=data, timeout=10)
        res.raise_for_status()
        print("✅ Mensaje de Telegram enviado con éxito.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al enviar mensaje a Telegram: {e}")

# --- Funciones para evitar spam de notificaciones ---
def ya_notificado(product_id):
    # Comprueba si ya se ha notificado sobre este producto
    if not os.path.exists(ESTADO_PATH):
        return False
    with open(ESTADO_PATH, "r") as f:
        notificados = json.load(f)
    return product_id in notificados

def marcar_como_notificado(product_id):
    # Guarda el ID del producto para no volver a notificar
    notificados = []
    if os.path.exists(ESTADO_PATH):
        with open(ESTADO_PATH, "r") as f:
            notificados = json.load(f)
    
    if product_id not in notificados:
        notificados.append(product_id)
        with open(ESTADO_PATH, "w") as f:
            json.dump(notificados, f)

def resetear_notificacion(id_unico_oferta):
    # Borra el archivo de estado para permitir futuras notificaciones
    if os.path.exists(ESTADO_PATH):
        os.remove(ESTADO_PATH)
        print("🗑️ Estado de notificación reseteado. Se volverá a notificar si la oferta reaparece.")


def main():
    """Bucle principal para ejecutar la comprobación periódicamente."""
    intervalo_minutos = 15
    print(f"🚀 Iniciando monitor de ofertas para el producto {PRODUCT_ID}.")
    print(f"Se comprobará cada {intervalo_minutos} minutos.")
    
    while True:
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
        comprobar_oferta()
        print(f"--- Esperando {intervalo_minutos} minutos para la próxima revisión ---")
        time.sleep(intervalo_minutos * 60)

def run_bot_background():
    """Función que ejecuta tu bot 'main()' en un hilo secundario."""
    # Damos 5 segundos para que el servidor Flask termine de arrancar
    # antes de que el bot empiece a llenar el log.
    print("🚀 Hilo del bot iniciado. Esperando 5s a que el servidor arranque...")
    time.sleep(5)
    
    # Llama a tu función principal (la del 'while True')
    main() 

# El bloque principal que se ejecuta
if __name__ == "__main__":
    
    # (Opcional: borrar el estado para prueba)
    if os.path.exists(ESTADO_PATH):
        os.remove(ESTADO_PATH)
        print("¡Archivo de estado borrado para prueba!")

    print("🚀 Iniciando el monitor de ofertas en un hilo (background)...")
    monitor_thread = Thread(target=run_bot_background)
    monitor_thread.start()

    print("🚀 Iniciando el servidor web (hilo principal) para Railway...")
    try:
        # ¡LA LÍNEA CRÍTICA!
        # NO hay valor por defecto. Lee el puerto que Railway le da.
        # Si 'PORT' no existe (ej. en tu PC), esto fallará con un error.
        port = int(os.environ.get("PORT", 8080)) 
        
    except TypeError:
        print("-------------------------------------------------------")
        print("❌ ERROR: La variable de entorno 'PORT' no está definida.")
        print("El script no puede arrancar sin un puerto de Railway.")
        print("-------------------------------------------------------")
        raise SystemExit # Salir del script si no hay puerto

    # Ejecutar el servidor en el hilo principal
    # Esto es lo que Railway espera.
    print(f"✅ Servidor Flask iniciándose en host 0.0.0.0 y puerto {port}...")
    app.run(host='0.0.0.0', port=port)