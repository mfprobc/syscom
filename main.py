import requests

# === CREDENCIALES SYSCOM Y SHOPIFY ===
SYSCOM_CLIENT_ID = "pPKGzLKN5JZx7035pzGikbYycC5uD4JR"
SYSCOM_CLIENT_SECRET = "pImuEy4l9M6CNroyoW2wip4CywDmG9xYSTehFpri"
SHOPIFY_DOMAIN = "gjgn71-z3.myshopify.com"
SHOPIFY_TOKEN = "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"

# Tool: Obtener el token de Syscom
def get_syscom_token():
    url = "https://developers.syscom.mx/oauth/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {
        "client_id": SYSCOM_CLIENT_ID,
        "client_secret": SYSCOM_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    r = requests.post(url, headers=headers, data=payload)
    r.raise_for_status()
    return r.json().get("access_token")

# Tool: Obtener categorías base
def get_syscom_categories(token):
    url = "https://developers.syscom.mx/api/v1/categorias"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()  # asume lista de {id, nombre,...}

# Tool: Obtener productos por categoría
def get_syscom_products_by_category(token, categoria_id):
    productos = []
    page = 1
    headers = {"Authorization": f"Bearer {token}"}
    while True:
        params = {"limit":50, "page":page, "categoria": categoria_id}
        r = requests.get("https://developers.syscom.mx/api/v1/productos", headers=headers, params=params)
        if r.status_code == 422:
            print("🚨 Error 422:", r.text)
            raise Exception("Parámetros inválidos o permisos insuficientes")
        r.raise_for_status()
        data = r.json().get("data", [])
        if not data:
            break
        productos.extend(data)
        page += 1
    return productos

# Tool: Buscar producto por SKU en Shopify
def shopify_get_product_by_sku(sku):
    url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/products.json?handle={sku}"
    headers = {"X-Shopify-Access-Token": SHOPIFY_TOKEN}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json().get("products", [])

# Tool: Crear o actualizar producto Shopify
def shopify_create_or_update(prod):
    sku = prod.get("codigo")
    payload = {"product":{
        "title": prod.get("nombre", sku),
        "body_html": prod.get("descripcion",""),
        "vendor":"Syscom",
        "handle":sku,
        "variants":[{"sku":sku,"price":str(prod.get("precio",0)),"inventory_quantity":int(prod.get("stock",0)),"inventory_management":"shopify"}],
        "images":[{"src":prod.get("imagen")}] if prod.get("imagen") else []
    }}
    headers = {"X-Shopify-Access-Token": SHOPIFY_TOKEN, "Content-Type": "application/json"}
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
    if r.status_code not in (200,201):
        print(f"⚠️ Error con {sku}: {r.status_code} {r.text}")

# === MAIN ===
def main():
    try:
        token = get_syscom_token()
        print("Token validado ✅")
        cats = get_syscom_categories(token)
        print("Categorías obtenidas:")
        for c in cats:
            print(f"  • {c['id']}: {c['nombre']}")
        # Aquí defines manualmente las categorías a usar o itera todas
        categorias_elegidas = [c['id'] for c in cats]  # o filtra solo algunas
        todos = 0
        for cat_id in categorias_elegidas:
            prods = get_syscom_products_by_category(token, cat_id)
            print(f"✔️ {len(prods)} productos en categoría {cat_id}")
            for p in prods:
                shopify_create_or_update(p)
            todos += len(prods)
        print(f"🎯 Total sincronizados: {todos}")
    except Exception as e:
        print("❌ Error:", str(e))

if __name__ == "__main__":
    main()

