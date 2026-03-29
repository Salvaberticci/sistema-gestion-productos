# 📦 Sistema de Gestión e Inventario - El Rebusque

Sistema moderno de consulta de precios y gestión administrativa diseñado específicamente para facilitar el control de inventarios locales con una experiencia de usuario rápida y profesional.

## ✨ Características Principales

### 🔍 Pantalla de Consulta (Modo Cliente)
- **Buscador Inmersivo**: Interfaz preparada para escanear códigos de barras o buscar por nombre.
- **Fondo Animado**: Lienzo con animaciones fluidas y carrusel de catálogo infinito.
- **Auto-cierre**: Se limpia automáticamente tras un periodo de inactividad para mayor privacidad y seguridad.

### 🏢 Panel Administrativo (Seguro)
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
