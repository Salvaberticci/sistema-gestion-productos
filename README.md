# 📦 Sistema de Gestión e Inventario - El Rebusque

Sistema moderno de consulta de precios y gestión administrativa diseñado específicamente para facilitar el control de inventarios locales con una experiencia de usuario rápida y profesional.

<div align="center">
  <a href="https://github.com/Salvaberticci/sistema-gestion-productos/releases/download/v1.0/El_Rebusque_Portable_v1.0.zip">
    <img src="https://img.shields.io/badge/⬇️_Descargar_Versión_Portable-(64--bits)-0B0E14?style=for-the-badge&logo=windows&logoColor=58A6FF&color=58A6FF&labelColor=161B22" alt="Descargar Portable" />
  </a>
</div>

## 🛠️ Guía Rápida de Uso (Portable)
1. Descarga el archivo `.zip` usando el botón de arriba.
2. Descomprime la carpeta `El_Rebusque_Portable_v1.0` en tu computadora o pendrive.
3. Asegúrate de nunca borrar la carpeta `images/` ni el archivo `logo.png` que acompañan al ejecutable.
4. Haz doble clic en `Sistema_El_Rebusque.exe`. (La base de datos se creará sola en el primer inicio).

## ✨ Características Principales

### 🔍 Terminal de Consulta (Modo Cliente)
- **Búsqueda Dual**: Uso de Escáner de código de barras o teclado (por nombre de producto).
- **Control de Privacidad (15s)**: Si la pantalla queda inactiva, la información del producto desaparece y regresa el fondo animado ('Drift').
- **Carrusel Inmersivo**: Las tarjetas rotan infinitamente cargando las imágenes desde el disco local.

### 🏢 Gestión de Inventario (Panel Admin)
- **Borrado Físico Inteligente**: Al eliminar un producto, su foto también se borra de tu disco duro para evitar archivos "basura".
- **Edición en Tiempo Real**: Doble clic sobre cualquier registro en la tabla para actualizar precios e imágenes.
- **Impresión de Tickets Térmicos**: Funcionalidad de impresión de código y precio compatibles nativamente con colas USB de Windows (`pywin32`) para rollos de 58mm y 80mm. 

### 📁 Flujo de Carga Masiva (Smart Import)
1. Haz clic en **"Exportar Plantilla Vacía"** en el Panel de Base de datos.
2. Llena el Excel resultante con los datos de tu nueva mercancía.
3. Importa el archivo usando **"Actualizar Datos"**. El sistema protegerá las fotos de tus productos viejos mientras actualiza precios y stock masivamente.

### 📊 Inteligencia de Negocios
- **Ranking de Interés:** El sistema rastrea cada vez que un cliente busca un producto para crear tu 'Top 5' de demanda.
- Monitoreo en vivo de artículos en "Zona Crítica" de bajo stock.
- **Gestión de Productos**: Tabla avanzada con previsualización lateral de imágenes.
- **Buscador Dinámico**: Filtrado instantáneo por código o referencia.
- **Editor Integral**: Actualización de precios (USD/VES), stock e imágenes con un clic.
- **Estadísticas de Negocio**: Identificación de productos con mayor/menor stock, variaciones de precio y **Ranking de Productos más Buscados** por clientes.

### ⚙️ Herramientas de Sistema
- **Sincronización Inteligente**: Importación binaria desde Excel que protege tus fotos actuales.
- **Gestión de Tasa (VES/USD)**: Actualización global de la tasa cambiaria.
- **Seguridad**: Cambio de contraseña administrativa con validación obligatoria.
- **Respaldos Atómicos**: Creación de copias completas del sistema (Excel + Fotos) con sellos de tiempo.

## 🚀 Instalación y Configuración

Siga estos pasos para ejecutar el sistema en su entorno local:

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/Salvaberticci/sistema-gestion-productos.git
   cd sistema-gestion-productos
   ```

2. **Crear y activar un entorno virtual**:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/Mac:
   source .venv/bin/activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la aplicación**:
   ```bash
   python main.py
   ```

## 📂 Estructura del Proyecto

- `main.py`: Punto de entrada de la aplicación.
- `ui_consulta.py`: Interfaz de usuario para clientes (Buscador).
- `ui_admin.py`: Interfaz de administración y gestión.
- `sync.py`: Núcleo de sincronización de datos con Excel.
- `database.py`: Gestión de la base de datos SQLite persistente.
- `utils.py`: Funciones de utilidad y lógica compartida.
- `images/products/`: Directorio local para almacenamiento de fotos de inventario.

---
© 2026 Modernizado por El Rebusque
