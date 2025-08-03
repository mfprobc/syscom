import requests

# === CREDENCIALES SYSCOM Y SHOPIFY ===
SYSCOM_CLIENT_ID = "pPKGzLKN5JZx7035pzGikbYycC5uD4JR"
SYSCOM_CLIENT_SECRET = "pImuEy4l9M6CNroyoW2wip4CywDmG9xYSTehFpri"
SHOPIFY_DOMAIN = "gjgn71-z3.myshopify.com"
SHOPIFY_TOKEN = "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"

# === Obtener token desde Syscom ===
def get_syscom_token():
    url = "https://developers.syscom.mx/oauth/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {
        "client_id": SYSCOM_CLIENT_ID,
        "client_secret": SYSCOM_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    r = requests.post(url, headers=headers, data=payload)
    if r.status_code == 401:
        raise Exception("⛔ Claves Syscom inválidas o formato incorrecto")
    r.raise_for_status()
    return r.json().get("access_token")

# === Obtener productos desde Syscom ===
def get_syscom_products(token):
    productos = []
    page = 1
    headers = {"Authorization": f"Bearer {token}"}
    while True:
        params = {"limit": 50, "page": page}
        r = requests.get("https://developers.syscom.mx/api/v1/productos",
                         headers=headers, params=params)
        if r.status_code == 401:
            raise Exception("⛔ Token Syscom inválido o expirado")
        r.raise_for_status()
        data = r.json().get("data", [])
        if not data:
            break
        productos.extend(data)
        page += 1
    return productos

# === Buscar por SKU en Shopify ===
def shopify_get_product_by_sku(sku):
    url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/products.json?handle={sku}"
    headers = {"X-Shopify-Access-Token": SHOPIFY_TOKEN}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json().get("products", [])

# === Crear o actualizar producto ===
def shopify_create_or_update(p):
    sku = p.get("codigo")
    price = p.get("precio", 0)
    title = p.get("nombre", sku)
    stock = p.get("stock", 0)
    img = p.get("imagen")

    payload = {"product": {
        "title": title,
        "body_html": p.get("descripcion", ""),
        "vendor": "Syscom",
        "handle": sku,
        "variants": [{
            "sku": sku,
            "price": str(price),
            "inventory_quantity": int(stock),
            "inventory_management": "shopify"
        }],
        "images": [{"src": img}] if img else []
    }}

    headers = {
        "X-Shopify-Access-Token": SHOPIFY_TOKEN,
        "Content-Type": "application/json"
    }

    existing = shopify_get_product_by_sku(sku)
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
        print("🔄 Obteniendo token de Syscom...")
        token = get_syscom_token()
        print("🟢 Token válido")
        productos = get_syscom_products(token)
        print(f"📦 Productos recibidos: {len(productos)}")
        for p in productos:
            shopify_create_or_update(p)
        print("✅ Sincronización completada.")
    except Exception as e:
        print(f"❌ Error general: {str(e)}")

if __name__ == "__main__":
    main()
