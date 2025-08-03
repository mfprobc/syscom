import requests

SYSCOM_CLIENT_ID = "pPKGzLKN5JZx7035pzGikbYycC5uD4JR"
SYSCOM_CLIENT_SECRET = "pImuEy4l9M6CNroyoW2wip4CywDmG9xYSTehFpri"
SHOPIFY_DOMAIN = "gjgn71-z3.myshopify.com"
SHOPIFY_TOKEN = "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"


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


def get_syscom_brands(token):
    url = "https://developers.syscom.mx/api/v1/marcas"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()


def get_syscom_categories(token):
    url = "https://developers.syscom.mx/api/v1/categorias"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()


def get_products(token, brand_id, category_id):
    productos = []
    page = 1
    headers = {"Authorization": f"Bearer {token}"}
    while True:
        params = {"limit": 50, "page": page, "marca": brand_id, "categoria": category_id}
        r = requests.get("https://developers.syscom.mx/api/v1/productos", headers=headers, params=params)
        if r.status_code == 422:
            break  # combinación inválida o sin resultados
        r.raise_for_status()
        data = r.json().get("data", [])
        if not data:
            break
        productos.extend(data)
        page += 1
    return productos


def shopify_get_product_by_sku(sku):
    url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/products.json?handle={sku}"
    headers = {"X-Shopify-Access-Token": SHOPIFY_TOKEN}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json().get("products", [])


def shopify_create_or_update(p):
    sku = p.get("codigo")
    payload = {"product": {
        "title": p.get("nombre", sku),
        "body_html": p.get("descripcion", ""),
        "vendor": "Syscom",
        "handle": sku,
        "variants": [{
            "sku": sku,
            "price": str(p.get("precio", 0)),
            "inventory_quantity": int(p.get("stock", 0)),
            "inventory_management": "shopify"
        }],
        "images": ([{"src": p["imagen"]}] if p.get("imagen") else [])
    }}
    headers = {"X-Shopify-Access-Token": SHOPIFY_TOKEN, "Content-Type": "application/json"}
    existing = shopify_get_product_by_sku(sku)
    if existing:
        pid = existing[0]["id"]
        r = requests.put(f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/products/{pid}.json", headers=headers, json=payload)
        print(f"🔁 Actualizado: {sku}")
    else:
        r = requests.post(f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/products.json", headers=headers, json=payload)
        print(f"✅ Creado: {sku}")
    if r.status_code not in (200, 201):
        print("⚠️ Error con", sku, r.status_code, r.text)


def main():
    try:
        token = get_syscom_token()
        print("🔐 Token OK")
        marcas = get_syscom_brands(token)
        categorias = get_syscom_categories(token)
        total = 0
        for marca in marcas:
            for categoria in categorias:
                try:
                    prods = get_products(token, marca["id"], categoria["id"])
                    if prods:
                        print(f"📦 {len(prods)} productos - Marca: {marca['nombre']}, Categoría: {categoria['nombre']}")
                        for p in prods:
                            shopify_create_or_update(p)
                            total += 1
                except Exception as e:
                    continue  # salta combinaciones inválidas sin detener ejecución
        print(f"✅ Total sincronizados: {total}")
    except Exception as e:
        print("❌ Error general:", str(e))


if __name__ == "__main__":
    main()

