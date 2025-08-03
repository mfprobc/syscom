import requests
import json

# === CREDENCIALES DEFINIDAS DIRECTAMENTE ===
SYSCOM_CLIENT_ID = "c3f86bff3b5fea8c2bbfc914f5ab1001"
SYSCOM_CLIENT_SECRET = "f944c2a476a666dad9572d75d078989"
SHOPIFY_DOMAIN = "gjgn71-z3.myshopify.com"
SHOPIFY_TOKEN = "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"

# === Obtener token Syscom (OAuth2 con JSON) ===
def get_syscom_token():
    url = "https://developers.syscom.mx/oauth/token"
    headers = {"Content-Type": "application/json"}
    data = {
        "client_id": SYSCOM_CLIENT_ID,
        "client_secret": SYSCOM_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    r = requests.post(url, headers=headers, data=json.dumps(data))
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
            raise Exception("⛔ Token de Syscom inválido o expirado")
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
        print("🟢 Token obtenido correctamente")
        productos = get_syscom_products(token)
        print(f"📦 {len(productos)} productos obtenidos de Syscom")
        for p in productos:
            shopify_create_or_update(p)
        print("✅ Sincronización finalizada.")
    except Exception as e:
        print(f"❌ Error general: {str(e)}")

if __name__ == "__main__":
    main()
