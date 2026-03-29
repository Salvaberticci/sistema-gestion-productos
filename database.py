import sqlite3
import os

DB_NAME = "el_rebusque.db"

def init_db():
    # Asegurar que la carpeta de imágenes local exista
    os.makedirs(os.path.join("images", "products"), exist_ok=True)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabla de productos basada exactamente en el archivo master: base_datos_inventario.xlsx
    # Se agrega únicamente la columna image_path al final
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS productos (
        codigop TEXT PRIMARY KEY,
        referencia TEXT,
        exisact REAL,
        pcosto REAL,
        pventa REAL,
        precio_almacen REAL,
        precio_venta REAL,
        REBUSQUE REAL,
        image_path TEXT,
        busquedas INTEGER DEFAULT 0
    )
    ''')
    
    # MIGRACIÓN: Intentar añadir la columna si la tabla ya existía sin ella
    try:
        cursor.execute("ALTER TABLE productos ADD COLUMN busquedas INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        # La columna ya existe, ignoramos el error
        pass
    
    # Tabla de configuración para tasa de cambio y credenciales
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS configuracion (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE,
        value TEXT
    )
    ''')
    
    # Valores por defecto para configuración principal
    cursor.execute("INSERT OR IGNORE INTO configuracion (key, value) VALUES ('tasa_cambio', '1.0')")
    cursor.execute("INSERT OR IGNORE INTO configuracion (key, value) VALUES ('admin_pass', '12345')")
    cursor.execute("INSERT OR IGNORE INTO configuracion (key, value) VALUES ('admin_user', 'admin')")
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

if __name__ == "__main__":
    init_db()
    print("Base de datos adaptada para base_datos_inventario.xlsx")
