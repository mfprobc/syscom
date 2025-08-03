import requests

# === CONFIGURACIÓN MANUAL ===
SYSCOM_CLIENT_ID = "TU_CLIENT_ID"
SYSCOM_CLIENT_SECRET = "TU_CLIENT_SECRET"
SHOPIFY_DOMAIN = "gjgn71-z3.myshopify.com"
SHOPIFY_TOKEN = "shpat_..."

# === Obtener token Syscom (OAuth2) ===
def get_syscom_token():
    url = "https://developers.syscom.mx/oauth/token"
    data = {
        "client_id": SYSCOM_CLIENT_ID,
        "client_secret": SYSCOM_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    r = requests.post(url, data=data)
    r.raise_for_status()
    return r.json()["access_token"]

# === Obtener productos desde Syscom ===
def get_syscom_products(token):
    productos = []
    page = 1
    headers = {"Authorization": f"Bearer {token}"}
    while True:
        params = {"limit": 50, "page": page}
        r = requests.get("https://developers.syscom.mx/api/v1/productos",
                         headers=headers, params=params)
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
    sku = producto.get("codigo")
    precio = producto.get("precio", 0)
    nombre = producto.get("nombre", sku)
    stock = producto.get("stock", 0)
    imagen = producto.get("imagen")

    payload = {
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
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_TOKEN,
        "Content-Type": "application/json"
    }

    if existing:
        pid = existing[0]["id"]
        url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/products/{pid}.json"
        r = requests.put(url, headers=headers, json=payload)
        print(f"🔁 Actualizado: {sku}")
    else:
        url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/products.json"
        r = requests.post(url, headers=headers, json=payload)
        print(f"✅ Creado: {sku}")

    if r.status_code not in (200, 201):
        print(f"⚠️ Error con {sku}: {r.status_code} {r.text}")

# === MAIN ===
def main():
    try:
        print("🔄 Solicitando token Syscom...")
        token = get_syscom_token()
        productos = get_syscom_products(token)
        print(f"📦 {len(productos)} productos obtenidos de Syscom")
        for p in productos:
            shopify_create_or_update(p)
        print("✅ Sincronización finalizada.")
    except Exception as e:
        print(f"❌ Error general: {str(e)}")

if __name__ == "__main__":
    main()

