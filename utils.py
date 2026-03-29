from database import get_db_connection

def get_exchange_rate():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM configuracion WHERE key = 'tasa_cambio'")
    res = cursor.fetchone()
    conn.close()
    return float(res[0]) if res else 1.0

def calculate_prices(usd_price, rate):
    ves_price = usd_price * rate
    return usd_price, ves_price

def format_currency(value, symbol="$"):
    return f"{symbol} {value:,.2f}"

def search_product(query):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Busqueda por ID Artículo (que también es el código de barras)
    cursor.execute("SELECT * FROM productos WHERE codigop = ?", (query,))
    product = cursor.fetchone()
    
    if product:
        # Incrementar contador de búsquedas (interés del cliente)
        conn.execute("UPDATE productos SET busquedas = busquedas + 1 WHERE codigop = ?", (product['codigop'],))
        conn.commit()
        
    conn.close()
    return product
