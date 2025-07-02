import requests
import json
import os
import html
from datetime import datetime
from dotenv import load_dotenv
import time

# --- CONFIGURACIÓN ---
# Cargar claves desde .env (TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- OBJETIVOS DE LA BÚSQUEDA ---
#PRODUCT_ID = "E468756-000"
PRODUCT_ID = "E457428-000"
#COLOR_OBJETIVO_CODE = "61"
#COLOR_OBJETIVO_NOMBRE = "AZUL"
TALLAS_OBJETIVO = {"S", "M"}

# URLs
API_URL = "https://www.uniqlo.com/es/api/commerce/v5/es/products?path=37609%2C%2C%2C&flagCodes=discount&genderId=37609&offset=0&limit=36&imageRatio=3x4&httpFailure=true"
PRODUCT_URL = f"https://www.uniqlo.com/es/es/products/{PRODUCT_ID}"

# Archivo para evitar notificaciones repetidas
ESTADO_PATH = "estado_oferta_notificada.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "x-fr-clientid": "uq.es.web-spa"
}
# --- FIN DE LA CONFIGURACIÓN ---


def comprobar_oferta():
    """
    Busca el producto en la API y comprueba si cumple las condiciones de la oferta.
    """
    print(f"🔗 Consultando API en busca de ofertas para {PRODUCT_ID}...")
    try:
        res = requests.get(API_URL, headers=HEADERS, timeout=15)
        res.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al conectar con la API: {e}")
        return

    data = res.json().get("result", {})
    if not data or not data.get("items"):
        print("❌ La respuesta de la API no contiene 'items' o está vacía.")
        return
    
    # ID único para esta oferta específica 
    id_unico_oferta = f"{PRODUCT_ID}"

    # La API puede devvolver el mismo producto en varios "items" si tiene
    # diferentes sets de tallas por color. Debemos revisar todos.
    oferta_encontrada = False
    for item in data.get("items", []):
        # 1. Comprobar si es nuestro producto
        if item.get("productId") != PRODUCT_ID:
            continue
        # # 2. Comprobar si nuestro color está en este grupo
        # colores_del_item = {c.get("displayCode") for c in item.get("colors", [])}
        # if COLOR_OBJETIVO_CODE not in colores_del_item:
        #     continue

        # --- Si encontramos el producto y el color comprobamos las condiciones ---
        print(f"✅ Producto encontrados, comprobamos las condiciones...")

        precios = item.get("prices", {})
        promo_activa = precios.get("promo") is not None
        es_precio_dual = precios.get("isDualPrice") is True
    
        tallas_disponibles = {size.get("name") for size in item.get("sizes", [])}
        hay_talla_objetivo = not TALLAS_OBJETIVO.isdisjoint(tallas_disponibles)

        print(f"  - ¿Promo activa?: {'Sí' if promo_activa else 'No'}")
        print(f"  - ¿Precio dual?: {'Sí' if es_precio_dual else 'No'}")
        print(f"  - ¿Stock en {', '.join(TALLAS_OBJETIVO)}?: {'Sí' if hay_talla_objetivo else 'No'}")

        # Si se cumplen TODAS las condiciones
        if promo_activa and es_precio_dual and hay_talla_objetivo:
            if ya_notificado(f"{PRODUCT_ID}"):
                print("🤫 Oferta ya notificada previamente. No se enviará de nuevo.")
                oferta_encontrada = True
            else:
                print("🎉 ¡OFERTA ENCONTRADA! Enviando notificación...")
                nombre = item.get("name", "Producto sin nombre")
                precio_promo = precios.get("promo", {}).get("value", "N/A")
                precio_base = precios.get("base", {}).get("value", "N/A")
                tallas_en_stock_objetivo = ", ".join(sorted(list(TALLAS_OBJETIVO.intersection(tallas_disponibles))))

                mensaje = (
                    f"🚨 <b>¡Oferta encontrada!</b>\n"
                    f"<a href='{PRODUCT_URL}'>{html.escape(nombre)}</a>\n\n"
                    f"💰 <b>Precio: {precio_promo}€</b> (antes {precio_base}€)\n"
                    #f"🎨 <b>Colores:</b> {COLOR_OBJETIVO_NOMBRE}\n"
                    f"📏 <b>Tallas disponibles:</b> {tallas_en_stock_objetivo}"
            )
                enviar_telegram(mensaje)
                marcar_como_notificado(id_unico_oferta)
            # Al encontrar la oferta (este nofticada o no), terminamos la función
            return
    # Si el bucle termina, significa que no se encontró niguna oferta válida
    print("❌ No se encontraron ofertas válidas para el producto y color especificados.")
    # Si estaba noficada, signica que ya no está disponible. La reseteamos
    if ya_notificado(id_unico_oferta):
        print("🗑️ Oferta previamente notificada ya no está disponible. Reseteando estado.")
        resetear_notificacion(id_unico_oferta)


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
    """Comprueba si ya se ha notificado sobre este producto."""
    if not os.path.exists(ESTADO_PATH):
        return False
    with open(ESTADO_PATH, "r") as f:
        notificados = json.load(f)
    return product_id in notificados

def marcar_como_notificado(product_id):
    """Guarda el ID del producto para no volver a notificar."""
    notificados = []
    if os.path.exists(ESTADO_PATH):
        with open(ESTADO_PATH, "r") as f:
            notificados = json.load(f)
    
    if product_id not in notificados:
        notificados.append(product_id)
        with open(ESTADO_PATH, "w") as f:
            json.dump(notificados, f)

def resetear_notificacion(id_unico_oferta):
    """Borra el archivo de estado para permitir futuras notificaciones."""
    if os.path.exists(ESTADO_PATH):
        os.remove(ESTADO_PATH)
        print("🗑️ Estado de notificación reseteado. Se volverá a notificar si la oferta reaparece.")


def main():
    """Bucle principal para ejecutar la comprobación periódicamente."""
    intervalo_minutos = 15
    print(f"🚀 Iniciando monitor de ofertas para el producto {PRODUCT_ID}.")
    #print(f"Se comprobará cada {intervalo_minutos} minutos.")
    
    # while True:
    #     print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
    #     comprobar_oferta()
    #     print(f"--- Esperando {intervalo_minutos} minutos para la próxima revisión ---")
    #     time.sleep(intervalo_minutos * 60)

if __name__ == "__main__":
    main()