from database import get_db_connection
import sys
import os
from fpdf import FPDF

# Soporte de impresión nativa en Windows (requiere pywin32 instalado)
try:
    import win32print
    import win32ui
    import win32con
    WIN32_PRINT_ENABLED = True
except ImportError:
    WIN32_PRINT_ENABLED = False

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

def get_installed_printers():
    """Devuelve una lista de los nombres de impresoras instaladas en Windows."""
    if not WIN32_PRINT_ENABLED:
        return []
    try:
        # Enumerar impresoras locales y conectadas
        printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
        # printers es una tupla de tuplas: (flags, description, name, comment)
        return [printer[2] for printer in printers]
    except Exception as e:
        print(f"Error enumerando impresoras: {e}")
        return []

def print_thermal_ticket(printer_name, product_name, price_bs):
    """
    Envía una orden directa a la impresora de Windows usando GDI (win32ui).
    Dibuja el Nombre y Precio en un bloque de texto que se ajusta a impresoras térmicas (58mm/80mm).
    """
    if not WIN32_PRINT_ENABLED:
        return False, "El módulo de impresión (pywin32) no está instalado o falló la importación."
        
    try:
        # Abrir referencia a impresora
        hPrinter = win32print.OpenPrinter(printer_name)
    except Exception as e:
        return False, f"No se pudo conectar a la impresora '{printer_name}'.\nDetalle: {e}"
        
    try:
        # Iniciar documento de impresión en el contexto de dispositivo (DC)
        hDC = win32ui.CreateDC()
        hDC.CreatePrinterDC(printer_name)
        hDC.StartDoc("Ticket_Precio")
        hDC.StartPage()
        
        # Configuración de ancho máximo para papel de 57mm (aprox. 400-430 unidades lógicas)
        MAX_TEXT_WIDTH = 420 
        
        # Algoritmo de ESCALADO DINÁMICO para el NOMBRE
        current_height = 55 # Empezamos con un tamaño generoso
        min_height = 20    # Tamaño mínimo legible
        
        while current_height >= min_height:
            font_name = win32ui.CreateFont({
                "name": "Arial",
                "height": current_height,
                "weight": 700, # Negrita
            })
            hDC.SelectObject(font_name)
            # Medir cuánto ocupa el nombre con este tamaño de fuente
            text_width, text_height = hDC.GetTextExtent(product_name)
            
            if text_width <= MAX_TEXT_WIDTH or current_height == min_height:
                break
            
            current_height -= 5 # Reducir y volver a probar
            
        # Dibujar el Nombre (centrado o con margen izquierdo de 10px)
        hDC.TextOut(10, 20, product_name)
        
        # Opciones de fuente para el PRECIO (Arial, siempre grande y claro)
        price_height = 70
        font_price = win32ui.CreateFont({
            "name": "Arial",
            "height": price_height, 
            "weight": 800, # Extra negrita
        })
        hDC.SelectObject(font_price)
        
        formated_price = format_currency(price_bs, "Bs.")
        hDC.TextOut(10, 25 + text_height + 10, formated_price)
        
        # Cerrar y enviar job
        hDC.EndPage()
        hDC.EndDoc()
        hDC.DeleteDC()
        return True, "Ticket enviado a la cola de impresión exitosamente."
        
    except Exception as e:
        return False, f"Error durante la impresión:\n{e}"
    finally:
        win32print.ClosePrinter(hPrinter)

def generate_ticket_pdf(product_name, price_bs, output_path="vista_previa_ticket.pdf"):
    """
    Genera un archivo PDF con el formato exacto de un ticket térmico de 57mm x 80mm.
    Se utiliza para previsualizar antes de imprimir físicamente.
    """
    try:
        # Definir tamaño de página: 57mm de ancho por 80mm de alto (formato ticket)
        pdf = FPDF(unit="mm", format=(57, 80))
        pdf.add_page()
        pdf.set_margins(left=5, top=5, right=5)
        
        # Algoritmo de escalado de fuente para el NOMBRE (similar al de GDI)
        font_size = 14
        pdf.set_font("Helvetica", "B", font_size)
        
        # Reducir tamaño de fuente si el texto es muy largo para el ancho de 57mm
        while pdf.get_string_width(product_name) > 47 and font_size > 7:
            font_size -= 0.5
            pdf.set_font("Helvetica", "B", font_size)
            
        pdf.set_y(8)
        # Usamos multi_cell para permitir que el nombre ocupe hasta 2 líneas si es necesario
        pdf.multi_cell(w=47, h=5, text=product_name, align='L')
        
        # Dibujar el PRECIO
        pdf.set_y(pdf.get_y() + 4)
        pdf.set_font("Helvetica", "B", 18)
        formated_price = format_currency(price_bs, "Bs.")
        pdf.cell(w=47, h=10, text=formated_price, align='L')
        
        # Guardar archivo
        pdf.output(output_path)
        
        # Abrir el PDF automáticamente en Windows
        if os.name == 'nt' and os.path.exists(output_path):
            os.startfile(output_path)
            
        return True, f"Vista previa generada en: {output_path}"
    except Exception as e:
        return False, f"Error al generar vista previa PDF: {e}"
