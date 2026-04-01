import sqlite3
import pandas as pd
import os
import shutil
from database import DB_NAME, get_db_connection

EXCEL_FILE = "base_datos_inventario.xlsx"

# Mapeo de columnas internas de base de datos a nombres humanizados para Excel
COLUMN_MAP = {
    "codigop": "Código",
    "referencia": "Referencia",
    "exisact": "Existencia",
    "pventa": "Precio en Dólares",
    "image_path": "Imagen"
}
# Mapeo inverso para importación
REVERSE_MAP = {v: k for k, v in COLUMN_MAP.items()}

def import_excel_to_db(file_path=None):
    """
    Importa datos desde un Excel con nombres humanizados.
    Actualiza la DB SQLite local y el archivo maestro.
    Mantiene la protección de imágenes si no se provee una nueva.
    """
    target = file_path if file_path else EXCEL_FILE
    if not os.path.exists(target):
        print(f"Error: No se encontró {target}")
        return False
    
    try:
        df = pd.read_excel(target)
        # Limpiar espacios en blanco de los nombres de columnas
        df.columns = [str(c).strip() for c in df.columns]
        
        # Filtrar posibles filas de basura
        if "Código" in df.columns:
            df = df[df['Código'].astype(str).str.lower() != 'código']
        
        # Convertir columnas numéricas humanizadas
        if "Existencia" in df.columns:
            df["Existencia"] = pd.to_numeric(df["Existencia"], errors='coerce').fillna(0)
        if "Precio en Dólares" in df.columns:
            df["Precio en Dólares"] = pd.to_numeric(df["Precio en Dólares"], errors='coerce').fillna(0)

        conn = get_db_connection()
        cursor = conn.cursor()
        
        count = 0
        for _, row in df.iterrows():
            # Extraer datos usando nombres humanizados
            cod = str(row.get('Código', '')).strip()
            if not cod or cod.lower() == 'nan': continue
            
            ref = str(row.get('Referencia', ''))
            exis = float(row.get('Existencia', 0))
            pv = float(row.get('Precio en Dólares', 0))
            
            # Buscar imagen actual para protegerla
            cursor.execute("SELECT image_path FROM productos WHERE codigop = ?", (cod,))
            existing = cursor.fetchone()
            
            excel_img = str(row.get('Imagen', '')).strip()
            final_img = excel_img if excel_img and excel_img.lower() != 'nan' else (existing['image_path'] if existing else "")

            # Solo actualizamos las 4 columnas principales y la imagen (las otras se mantienen o quedan en 0)
            cursor.execute('''
                INSERT OR REPLACE INTO productos 
                (codigop, referencia, exisact, pventa, image_path, pcosto, precio_almacen, precio_venta, REBUSQUE)
                VALUES (?, ?, ?, ?, ?, 
                        (SELECT pcosto FROM productos WHERE codigop = ?),
                        (SELECT precio_almacen FROM productos WHERE codigop = ?),
                        (SELECT precio_venta FROM productos WHERE codigop = ?),
                        (SELECT REBUSQUE FROM productos WHERE codigop = ?))
            ''', (cod, ref, exis, pv, final_img, cod, cod, cod, cod))
            count += 1
            
        conn.commit()
        conn.close()
        
        # Guardar cambios de vuelta al maestro local con el nuevo formato
        export_db_to_excel()
        return True
    except Exception as e:
        print(f"Error en importación humanizada: {e}")
        return False

def sync_excel_to_db():
    """Alias para compatibilidad inicial."""
    return import_excel_to_db()

def export_db_to_excel(custom_path=None):
    """
    Exporta la base de datos local a Excel con nombres humanizados.
    Incluye la columna 'Precio en Bolívares' vacía.
    """
    target = custom_path if custom_path else EXCEL_FILE
    try:
        conn = get_db_connection()
        # Seleccionamos las columnas en el orden solicitado por el usuario
        cursor = conn.cursor()
        cursor.execute("SELECT codigop, referencia, exisact, pventa, image_path FROM productos")
        data = cursor.fetchall()
        conn.close()
        
        # Crear DataFrame con nombres bonitos
        rows = []
        for d in data:
            rows.append({
                "Código": d['codigop'],
                "Referencia": d['referencia'],
                "Existencia": d['exisact'],
                "Precio en Dólares": d['pventa'],
                "Imagen": d['image_path']
            })
            
        df = pd.DataFrame(rows)
        # Reordenar columnas para asegurar el orden exacto
        df = df[["Código", "Referencia", "Existencia", "Precio en Dólares", "Imagen"]]
        
        df.to_excel(target, index=False)
        return True
    except Exception as e:
        print(f"Error al exportar humanizado: {e}")
        return False

def create_full_backup(parent_folder):
    """Genera un respaldo completo (Excel + Fotos) dentro de una nueva carpeta temporal con fecha."""
    from datetime import datetime
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_folder_name = f"Respaldo_Sistema_Productos_{timestamp}"
        dest_folder = os.path.join(parent_folder, backup_folder_name)
        
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)
        
        # 1. Exportar Excel humanizado con el nuevo nombre
        excel_backup_path = os.path.join(dest_folder, "respaldo_base_datos.xlsx")
        export_db_to_excel(excel_backup_path)
        
        # 2. Copiar carpeta de imágenes
        src_imgs = os.path.join("images", "products")
        dest_imgs = os.path.join(dest_folder, "product_images")
        
        if os.path.exists(src_imgs):
            shutil.copytree(src_imgs, dest_imgs)
            
        return True
    except Exception as e:
        print(f"Error creando respaldo: {e}")
        return False

def update_db_and_excel(codigop, updated_data):
    """Actualiza producto específico y rebota al maestro."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = "UPDATE productos SET "
        fields = [f"{key} = ?" for key in updated_data.keys()]
        query += ", ".join(fields) + " WHERE codigop = ?"
        values = list(updated_data.values()) + [codigop]
        cursor.execute(query, tuple(values))
        conn.commit()
        conn.close()
        return export_db_to_excel()
    except Exception as e:
        print(f"Error: {e}")
        return False

def import_images_from_folder(src_folder):
    """Copia todas las imágenes de una carpeta a la ubicación interna del sistema."""
    try:
        dest_dir = os.path.join("images", "products")
        os.makedirs(dest_dir, exist_ok=True)
        
        count = 0
        formats = ('.jpg', '.jpeg', '.png', '.webp', '.gif')
        for filename in os.listdir(src_folder):
            if filename.lower().endswith(formats):
                src_path = os.path.join(src_folder, filename)
                dest_path = os.path.join(dest_dir, filename)
                shutil.copy2(src_path, dest_path)
                count += 1
        return True, count
    except Exception as e:
        print(f"Error importando fotos: {e}")
        return False, 0

def delete_product(codigop):
    """Elimina un producto de la DB, su imagen física y sincroniza con el Excel maestro."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Obtener ruta de imagen antes de borrar
        cursor.execute("SELECT image_path FROM productos WHERE codigop = ?", (codigop,))
        row = cursor.fetchone()
        if row and row['image_path']:
            img_path = row['image_path']
            if os.path.exists(img_path):
                try: os.remove(img_path)
                except: pass
        
        # 2. Borrar registro
        cursor.execute("DELETE FROM productos WHERE codigop = ?", (codigop,))
        conn.commit()
        conn.close()
        
        # 3. Sincronizar Excel
        return export_db_to_excel()
    except Exception as e:
        print(f"Error al eliminar producto: {e}")
        return False

def export_template(path):
    """Genera un archivo Excel vacío con los encabezados correctos para carga de nuevos productos."""
    try:
        headers = ["Código", "Referencia", "Existencia", "Precio en Dólares", "Imagen"]
        df = pd.DataFrame(columns=headers)
        df.to_excel(path, index=False)
        return True
    except Exception as e:
        print(f"Error al exportar plantilla: {e}")
        return False
