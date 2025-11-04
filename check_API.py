import requests
import json

API_URL = "https://www.uniqlo.com/es/api/commerce/v5/es/products?path=37609%2C%2C%2C&flagCodes=discount&genderId=37609&offset=0&limit=36&imageRatio=3x4&httpFailure=true"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "x-fr-clientid": "uq.es.web-spa"
}

print(f"Intentando conectar con la API...")

try: 
    # Hacemos la petición
    response = requests.get(API_URL, headers=HEADERS, timeout=15)

    # Comprobamos el código de estado HTTP
    print(f"Código de estado HTTP: {response.status_code}")

    # Intentamos forzar un error si el código no es 2xx (OK)
    response.raise_for_status()

    # Intentamos interpretar la respuesta como JSON
    data = response.json()
    print("La respuesta es un JSON válido.")

    # Imprimimos una parte de los datos para ver la estructura
    print("\n--- Vista previa de los datos recibidos (primer item) ---")
    if data.get("result", {}.get("items")):
        primer_item = data["result"]["items"][0]
        # Imprimimos sólo algunas claves para no saturar la pantalla
        print(f"  - Product ID: {primer_item.get('productId')}")
        print(f"  - Nombre: {primer_item.get('name')}")
        print(f"  - Precio Promo: {primer_item.get('prices', {}).get('promo')}")
        print(f"  - Número de colores: {len(primer_item.get('colors', []))}")
        print(f"  - Número de tallas: {len(primer_item.get('sizes', []))}")

    else: 
        print("❌ La estructura esperada ('result' -> 'items') no se encontró en el JSON.")
        print("\n--- Respuesta JSON completa ---")
        print(json.dumps(data, indent=2, ensure_ascii=False))
except requests.exceptions.HTTPError as e:
    print(f"❌ Error HTTP: {e}")
    print(f"El servidor respondió con un error. Esto puede deberse a que la URL ya no es válida o los headers son incorrectos.")

except requests.exceptions.RequestException as e:
    print(f"❌ Error de Conexión: {e}")
    print("No se pudo conectar al servidor. Revisa tu conexión a internet o si la web de Uniqlo está caída.")

except json.JSONDecodeError:
    print("❌ Error de JSON: La respuesta no pudo ser decodificada.")
    print("Esto suele pasar si la API devuelve un error en formato HTML en lugar de JSON (por ejemplo, una página de 'Acceso Denegado').")
    print("\n--- Contenido de la respuesta (primeros 300 caracteres) ---")
    print(response.text[:300]) 