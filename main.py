import requests
import csv
import io

# --------- CONFIGURACIÓN ---------
# SYSCOM - URL del CSV
SYSCOM_CSV_URL = "https://betaweb.syscom.mx/principal/reporte_art_hora?cadena1=104562864&cadena2=f54cfb7feb4f6c7319c08719d7455714&all=1&format=shopify&format_shopify=stock&tipo_precio=precio_sin_dfi&moneda=usd&incremento=0&sel=22,37,30,26,32,38"

# SHOPIFY - Datos de tu tienda
SHOPIFY_DOMAIN = "mfprobc.shopify.com"
ACCESS_TOKEN = "shpat_XXXXXXXXXXXXXXXXXXXXXXXXXXXX"  # ← pon aquí tu token real

HEADERS = {
    "X-Shopify-Access-Token": ACCESS_TOKEN,
    "Content-Type": "application/json"
}

# --------- FUNCIONES ---------

def get_product_by_handle(handle):
    url = f"https://{SHOPIFY_DOMAIN}/admin/api/2023-07/products.json?handle={handle}"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        productos = resp.json().get("products", [])
        return productos[0] if productos else None
    else:
        print(f"❌ Error al buscar {handle}: {resp.status_code}")
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
    resp = requests.put(url, headers=HEADERS, json=payload)
    if resp.status_code == 200:
        print(f"✅ Actualizado: {product['title']} → ${price} / stock: {stock}")
    else:
        print(f"❌ Error actualizando {product['title']}: {resp.status_code}")

# --------- FLUJO PRINCIPAL ---------

# 1. Descargar CSV de SYSCOM
print("Descargando CSV de SYSCOM...")
csv_response = requests.get(SYSCOM_CSV_URL)
if csv_response.status_code != 200:
    print("❌ Error al descargar CSV:", csv_response.status_code)
    exit()

csv_text = csv_response.content.decode("utf-8")
reader = csv.DictReader(io.StringIO(csv_text))

# 2. Recorrer productos
for row in reader:
    handle = row.get("Handle")
    price = row.get("Variant Price")
    stock = row.get("Variant Inventory Qty")

    if not handle or not price or stock is None:
        continue

    product = get_product_by_handle(handle)
    if product:
        update_variant_price_and_stock(product, price, stock)
    else:
        print(f"⚠️ Producto no encontrado en Shopify: {handle}")

