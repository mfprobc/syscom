import requests
import re

# --------- CONFIGURACIÓN ---------
# SYSCOM - Autenticación y endpoints
SYSCOM_TOKEN_URL = "https://developers.syscom.mx/api/v1/token"
SYSCOM_PRODUCTOS_URL = "https://developers.syscom.mx/api/v1/productos"

CLIENT_ID = "pPKGzLKN5JZx7035pzGikbYycC5uD4JR"
CLIENT_SECRET = "pImuEy4l9M6CNroyoW2wip4CywDmG9xYSTehFpri"

# SHOPIFY - Datos de tu tienda
SHOPIFY_DOMAIN = "mfprobc.shopify.com"
ACCESS_TOKEN = "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"

HEADERS_SHOPIFY = {
    "X-Shopify-Access-Token": ACCESS_TOKEN,
    "Content-Type": "application/json"
}

# --------- FUNCIONES ---------

def limpiar_texto(texto, max_length=None):
    if not texto:
        return ""
    texto = texto.strip()
    texto = texto.replace("™", "").replace("®", "").replace("°", "").replace("•", "-")
    texto = texto.replace("”", '"').replace("“", '"').replace("’", "'").replace("‘", "'")
    texto = re.sub(r"[^\x20-\x7EñÑáéíóúÁÉÍÓÚüÜ]", "", texto)
    texto = re.sub(r"\s+", " ", texto)
    if max_length and len(texto) > max_length:
        texto = texto[:max_length].rstrip()
    return texto

def log(mensaje):
    print(mensaje)
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(mensaje + "\n")

def get_syscom_access_token():
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    response = requests.post(SYSCOM_TOKEN_URL, data=payload)
    response.raise_for_status()
    return response.json()["access_token"]

def get_product_by_handle(handle):
    url = f"https://{SHOPIFY_DOMAIN}/admin/api/2023-07/products.json?handle={handle}"
    resp = requests.get(url, headers=HEADERS_SHOPIFY)
    if resp.status_code == 200:
        productos = resp.json().get("products", [])
        return productos[0] if productos else None
    else:
        log(f"❌ Error al buscar {handle}: {resp.status_code}")
        return None

def update_variant_price_and_stock(product, price, stock):
    variant_id = product["variants"][0]["id"]
    url = f"https://{SHOPIFY_DOMAIN}/admin/api/2023-07/variants/{variant_id}.json"
    payload = {
        "variant": {
            "id": variant_id,
            "price": price,
            "inventory_quantity": int(stock),
            "inventory_management": "shopify"
        }
    }
    resp = requests.put(url, headers=HEADERS_SHOPIFY, json=payload)
    if resp.status_code == 200:
        log(f"✅ Actualizado: {product['title']} → ${price} / stock: {stock}")
    else:
        log(f"❌ Error actualizando {product['title']}: {resp.status_code}")
        log(resp.text)

def crear_producto_en_shopify(handle, title, body, price, stock):
    url = f"https://{SHOPIFY_DOMAIN}/admin/api/2023-07/products.json"
    payload = {
        "product": {
            "title": title,
            "body_html": body,
            "handle": handle,
            "variants": [
                {
                    "price": price,
                    "inventory_quantity": int(stock),
                    "inventory_management": "shopify"
                }
            ]
        }
    }
    response = requests.post(url, headers=HEADERS_SHOPIFY, json=payload)
    if response.status_code == 201:
        log(f"🆕 Producto creado: {title} → ${price} / stock: {stock}")
    else:
        log(f"❌ Error al crear producto {handle}: {response.status_code}")
        log(response.text)

# --------- FLUJO PRINCIPAL ---------

log("\n🟡 SINCRONIZACIÓN INICIADA")

try:
    log("🔐 Obteniendo token de SYSCOM...")
    access_token = get_syscom_access_token()
except Exception as e:
    log(f"❌ Error al obtener token SYSCOM: {e}")
    exit()

try:
    log("📦 Consultando productos desde SYSCOM...")
    headers_syscom = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(SYSCOM_PRODUCTOS_URL, headers=headers_syscom)
    response.raise_for_status()
    productos = response.json().get("data", [])
except Exception as e:
    log(f"❌ Error al consultar productos SYSCOM: {e}")
    exit()

log(f"🔄 Procesando {len(productos)} productos...\n")

for p in productos:
    handle = limpiar_texto(p.get("codigo"), max_length=255)
    title = limpiar_texto(p.get("descripcion"), max_length=255)
    body = limpiar_texto(p.get("descripcion"), max_length=3000)
    price = p.get("precio")
    stock = p.get("disponible")

    if not handle or not price:
        continue

    try:
        product = get_product_by_handle(handle)
        if product:
            update_variant_price_and_stock(product, price, stock)
        else:
            crear_producto_en_shopify(handle, title, body, price, stock)
    except Exception as e:
        log(f"❌ Error procesando {handle}: {e}")

log("✅ SINCRONIZACIÓN COMPLETADA")

