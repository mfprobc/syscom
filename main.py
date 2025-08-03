import requests
import os
import base64
from dotenv import load_dotenv

load_dotenv()

# === Configuración desde .env ===
SYSCOM_API_KEY = os.getenv("SYSCOM_API_KEY")
SYSCOM_API_SECRET = os.getenv("SYSCOM_API_SECRET")
SHOPIFY_DOMAIN = os.getenv("SHOPIFY_DOMAIN")
SHOPIFY_TOKEN = os.getenv("SHOPIFY_TOKEN")

# === Autenticación básica para Syscom ===
def syscom_auth_header():
    token = f"{SYSCOM_API_KEY}:{SYSCOM_API_SECRET}"
    b64 = base64.b64encode(token.encode()).decode()
    return {"Authorization": f"Basic {b64}"}

# === Obtener productos desde SYSCOM ===
def get_syscom_products():
    url = "https://developers.syscom.mx/api/v1/productos"
    headers = syscom_auth_header()
    productos = []
    page = 1

    while True:
        params = {"limit": 50, "page": page}
        r = requests.get(url, headers=headers, params=params)
        r.raise_for_status()
        data = r.json().get("data", [])
        if not data:
            break
        productos.extend(data)
        page += 1

    return productos

# === Buscar producto por SKU en Shopify ===
def shopify_get_product_by_sku(sku):
    url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/products.json?handle={sku}"
    headers = {"X-Shopify-Access-Token": SHOPIFY_TOKEN}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json().get("products", [])

# === Crear o actualizar producto en Shopify ===
def shopify_create_or_update(producto):
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_TOKEN,
        "Content-Type": "application/json"
    }

    sku = producto.get("codigo")
    precio = producto.get("precio", 0)
    nombre = producto.get("nombre", sku)
    stock = producto.get("stock", 0)
    imagen = producto.get("imagen")

    shopify_product = {
        "product": {
            "title": nombre,
            "body_html": producto.get("descripcion", ""),
            "vendor": "Syscom",
            "handle": sku,
            "variants": [{
                "sku": sku,
                "price": str(precio),
                "inventory_quantity": int(stock),
                "inventory_management": "shopify"
            }],
            "images": [{"src": imagen}] if imagen else []
        }
    }

    existing = shopify_get_product_by_sku(sku)
    if existing:
        product_id = existing[0]["id"]
        url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/products/{product_id}.json"
        r = requests.put(url, headers=headers, json=shopify_product)
        print(f"🔁 Actualizado: {sku}")
    else:
        url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/products.json"
        r = requests.post(url, headers=headers, json=shopify_product)
        print(f"✅ Creado: {sku}")

    if r.status_code not in [200, 201]:
        print(f"⚠️ Error con {sku}: {r.status_code} - {r.text}")

# === MAIN ===
def main():
    try:
        print("🔄 Iniciando sincronización...")
        productos = get_syscom_products()
        print(f"📦 Productos recuperados: {len(productos)}")
        for p in productos:
            shopify_create_or_update(p)
        print("✅ Sincronización finalizada.")
    except Exception as e:
        print(f"❌ Error general: {str(e)}")

if __name__ == "__main__":
    main()

