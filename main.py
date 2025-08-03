import requests
import json

# === CONFIGURACIÓN MANUAL ===
SYSCOM_CLIENT_ID = "TU_CLIENT_ID"
SYSCOM_CLIENT_SECRET = "TU_CLIENT_SECRET"
SHOPIFY_DOMAIN = "gjgn71-z3.myshopify.com"
SHOPIFY_TOKEN = "shpat_..."

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
    r = requests.get(url, headers=header
