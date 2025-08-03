import requests
import csv
import io
import re
import json

# Configuración Shopify
SHOPIFY_DOMAIN = "mfprobc.shopify.com"
ACCESS_TOKEN = "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"

HEADERS_SHOPIFY = {
    "X-Shopify-Access-Token": ACCESS_TOKEN,
    "Content-Type": "application/json"
}

# URL CSV de SYSCOM (actualizado cada hora)
CSV_URL = "http://betaweb.syscom.mx/principal/reporte_art_hora?cadena1=104562864&cadena2=f54cfb7feb4f6c7319c08719d7455714&all=1&format=shopify&format_shopify=stock&tipo_precio=precio_sin_dfi&moneda=usd&incremento=0&sel=22,37,30,26,32,38"

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

def get_product_by_handle(handle):
    url = f"https://{SHOPIFY_DOMAIN}/admin/api/2023-07/products.json?handle={handle}"
    resp = requests.get(url, headers=HEADERS_SHOPIFY)
    if resp.status_code == 200:
        productos = resp.json().get("products", [])
        return productos[0] if productos else None
    else:
        log(f"❌ Error al buscar {handle}: {resp.status_code}")
        return None

def update_variant(product, price, stock):
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

def crear_producto(handle, title, body, price, stock):
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
    resp = requests.post(url, headers=HEADERS_SHOPIFY, json=payload)
    if resp.status_code == 201:
        log(f"🆕 Producto creado: {title} → ${price} / stock: {stock}")
    else:
        log(f"❌ Error al crear producto {handle}: {resp.status_code}")
        log(resp.text)

# ------------------ FLUJO PRINCIPAL ------------------

log("🟡 INICIANDO SINCRONIZACIÓN")

try:
    log("📥 Descargando archivo CSV...")
    r = requests.get(CSV_URL)
    r.raise_for_status()
    csv_text = r.content.decode("latin-1")
except Exception as e:
    log(f"❌ Error al descargar CSV: {e}")
    exit()

reader = csv.DictReader(io.StringIO(csv_text))
productos = list(reader)
log(f"📦 Productos leídos: {len(productos)}")

for p in productos:
    handle = limpiar_texto(p.get("Codigo"), 255)
    title = limpiar_texto(p.get("Descripcion"), 255)
    body = limpiar

