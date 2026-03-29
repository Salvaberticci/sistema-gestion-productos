import customtkinter as ctk
import os
from PIL import Image
from database import get_db_connection
from utils import get_exchange_rate
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import sqlite3
import pandas as pd
import shutil
from ui_shared import COLOR_BG, COLOR_CARD, COLOR_ACCENT, COLOR_TEXT_MAIN, COLOR_TEXT_DIM, COLOR_GOLD, SharedStyles
import sync

class EditProductDialog(ctk.CTkToplevel):
    def __init__(self, master, product_data, on_save):
        super().__init__(master)
        self.title("Editar Producto")
        self.geometry("500x750")
        self.product_data = product_data # dict de la DB
        self.on_save = on_save
        self.new_image_path = None
        self.image_removed = False
        
        self.configure(fg_color=COLOR_BG)
        self.bring_to_front()
        
        self.setup_ui()
        
    def bring_to_front(self):
        self.attributes('-topmost', True)
        self.focus_force()

    def setup_ui(self):
        ctk.CTkLabel(self, text="Editar Información", font=("Inter", 24, "bold"), text_color=COLOR_ACCENT).pack(pady=15)
        
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.entries = {}
        # Campos solicitados para edición
        fields = [
            ("codigop", "Código de Barras"),
            ("referencia", "Referencia / Nombre"),
            ("exisact", "Existencia"),
            ("pventa", "Precio de Venta ($ USD)")
        ]
        
        for field, label in fields:
            ctk.CTkLabel(self.scroll, text=label, font=("Inter", 13), text_color=COLOR_TEXT_DIM).pack(anchor="w", pady=(10, 2))
            entry = ctk.CTkEntry(self.scroll, height=45, fg_color="#0D1117")
            val = self.product_data.get(field, "")
            entry.insert(0, str(val if val is not None else ""))
            entry.pack(fill="x")
            self.entries[field] = entry
            
        # Image Upload Section
        img_frame = ctk.CTkFrame(self.scroll, fg_color="#1C2128", corner_radius=8)
        img_frame.pack(fill="x", pady=20, padx=10)
        
        curr_img = self.product_data.get("image_path", "")
        img_txt = f"Actual: {os.path.basename(curr_img)}" if curr_img and os.path.exists(curr_img) else "No hay imagen asignada"
        
        self.img_lbl = ctk.CTkLabel(img_frame, text=img_txt, font=("Inter", 12), text_color=COLOR_TEXT_DIM)
        self.img_lbl.pack(pady=(10, 5))
        
        img_btn = ctk.CTkButton(img_frame, text="📸 Seleccionar Imagen", command=self.pick_image, fg_color="#30363D", hover_color="#8B949E")
        img_btn.pack(pady=(5, 5))
        
        self.remove_btn = ctk.CTkButton(img_frame, text="🗑️ Quitar Imagen", command=self.remove_image, fg_color="transparent", text_color="#F85149", hover_color="#30363D")
        if not curr_img or not os.path.exists(curr_img):
            self.remove_btn.pack_forget()
        else:
            self.remove_btn.pack(pady=(0, 10))

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20, fill="x", padx=40)
        
        save_btn = ctk.CTkButton(btn_frame, text="Guardar Cambios", height=50, command=self.save)
        SharedStyles.apply_accent_button(save_btn)
        save_btn.pack(side="left", expand=True, padx=(0, 10))
        
        cancel_btn = ctk.CTkButton(btn_frame, text="Cancelar", height=50, fg_color="#30363D", command=self.destroy)
        cancel_btn.pack(side="left", expand=True)
    def pick_image(self):
        self.attributes('-topmost', False)  # Temporalmente quitamos el topmost para que el explorador pueda subir
        filename = filedialog.askopenfilename(
            parent=self,
            title="Seleccionar Imagen",
            filetypes=[("Imágenes", "*.jpg *.png *.jpeg *.webp *.gif")]
        )
        self.attributes('-topmost', True)  # Restauramos topmost al cerrar el explorador
        self.focus_force()
        if filename:
            self.new_image_path = filename
            self.image_removed = False
            self.img_lbl.configure(text=f"Nueva: {os.path.basename(filename)}", text_color=COLOR_ACCENT)
            self.remove_btn.pack(pady=(0, 10))

    def remove_image(self):
        self.new_image_path = ""
        self.image_removed = True
        self.img_lbl.configure(text="Imagen será eliminada", text_color="#F85149")
        self.remove_btn.pack_forget()

    def save(self):
        updated = {}
        try:
            for field, entry in self.entries.items():
                val = entry.get().strip()
                if field in ["exisact", "pventa"]:
                    updated[field] = float(val) if val else 0.0
                else:
                    updated[field] = val
            
            # Lógica de persistencia y LIPIEZA de imágenes físicas
            final_image_path = self.product_data.get("image_path", "")
            old_image = final_image_path
            
            if self.image_removed:
                final_image_path = ""
                # Borrado físico si existe
                if old_image and os.path.exists(old_image):
                    try: os.remove(old_image)
                    except: pass
            elif self.new_image_path:
                # Asegurar que la carpeta local exista
                dest_dir = os.path.join("images", "products")
                os.makedirs(dest_dir, exist_ok=True)
                
                ext = os.path.splitext(self.new_image_path)[1]
                local_filename = f"{self.product_data['codigop']}{ext}"
                local_path = os.path.join(dest_dir, local_filename).replace("\\", "/") # Normalizar para DB/Excel
                
                # Borramos la anterior SI es distinta a la nueva ruta local (para no borrar lo que acabamos de copiar)
                if old_image and old_image != local_path and os.path.exists(old_image):
                    try: os.remove(old_image)
                    except: pass

                try:
                    shutil.copy2(self.new_image_path, local_path)
                    final_image_path = local_path
                except Exception as e:
                    print(f"Error copiando imagen: {e}")
                    final_image_path = self.new_image_path

            updated["image_path"] = final_image_path
                    
            if sync.update_db_and_excel(self.product_data['codigop'], updated):
                self.destroy()
                self.on_save()
                messagebox.showinfo("Éxito", "Producto actualizado correctamente.")
            else:
                messagebox.showerror("Error", "Error al actualizar producto.")
        except ValueError:
            messagebox.showerror("Error", "Los campos de precio y existencia deben ser numéricos.")

class AdminScreen(ctk.CTkFrame):
    def __init__(self, master, on_back_click):
        super().__init__(master, fg_color=COLOR_BG)
        self.master = master
        self.on_back_click = on_back_click
        self.is_logged_in = False
        self.apply_tree_style()
        self.setup_login_ui()
        
    def apply_tree_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=COLOR_CARD, foreground=COLOR_TEXT_MAIN, fieldbackground=COLOR_CARD, rowheight=40, font=("Inter", 11), borderwidth=0)
        style.configure("Treeview.Heading", background="#1C2128", foreground=COLOR_ACCENT, font=("Inter", 12, "bold"), borderwidth=0)
        style.map("Treeview", background=[('selected', COLOR_ACCENT)], foreground=[('selected', "white")])

    def setup_login_ui(self):
        for widget in self.winfo_children(): widget.destroy()
        self.login_card = ctk.CTkFrame(self, width=500, height=650)
        SharedStyles.apply_card_style(self.login_card)
        self.login_card.place(relx=0.5, rely=0.5, anchor="center")
        
        if os.path.exists("logo.png"):
            logo_img = Image.open("logo.png")
            new_w = 200
            new_h = int(logo_img.size[1] * (new_w / logo_img.size[0]))
            self.ctk_logo = ctk.CTkImage(logo_img, logo_img, size=(new_w, new_h))
            ctk.CTkLabel(self.login_card, image=self.ctk_logo, text="").pack(pady=(60, 30))
        else:
            ctk.CTkLabel(self.login_card, text="🛡️", font=("Inter", 60)).pack(pady=(60, 20))
            
        ctk.CTkLabel(self.login_card, text="Acceso Administrativo", font=("Inter", 26, "bold"), text_color=COLOR_TEXT_MAIN).pack(pady=(0, 50))
        f_frame = ctk.CTkFrame(self.login_card, fg_color="transparent")
        f_frame.pack(pady=20, padx=40)
        self.user_entry = ctk.CTkEntry(f_frame, width=350, height=55, placeholder_text="Usuario", fg_color="#0D1117", border_color="#30363D")
        self.user_entry.pack(pady=15)
        self.pass_entry = ctk.CTkEntry(f_frame, width=350, height=55, placeholder_text="Contraseña", show="*", fg_color="#0D1117", border_color="#30363D")
        self.pass_entry.pack(pady=15)
        self.pass_entry.bind("<Return>", self.attempt_login)
        self.login_btn = ctk.CTkButton(self.login_card, text="Ingresar", width=350, height=55, command=self.attempt_login)
        SharedStyles.apply_accent_button(self.login_btn)
        self.login_btn.pack(pady=(40, 20))
        ctk.CTkButton(self.login_card, text="← Volver", fg_color="transparent", command=self.on_back_click).pack(pady=(0, 30))

    def attempt_login(self, event=None):
        u, p = self.user_entry.get().strip(), self.pass_entry.get().strip()
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT value FROM configuracion WHERE key='admin_user'")
        su = c.fetchone()
        c.execute("SELECT value FROM configuracion WHERE key='admin_pass'")
        sp = c.fetchone()
        conn.close()
        
        su_val = su[0] if su else "admin"
        sp_val = sp[0] if sp else "12345"
        
        if u == su_val and p == sp_val:
            self.is_logged_in = True
            self.setup_admin_dashboard()
        else: messagebox.showerror("Error", "Credenciales incorrectas")

    def setup_admin_dashboard(self):
        for widget in self.winfo_children(): widget.destroy()
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color="#0D1117")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.sidebar, text="ADMIN PANEL", font=("Inter", 20, "bold"), text_color=COLOR_ACCENT).pack(pady=40)
        self.create_side_btn("📦 Inventario", self.show_products_tab).pack(pady=5, padx=20, fill="x")
        self.create_side_btn("📊 Estadísticas", self.show_stats_tab).pack(pady=5, padx=20, fill="x")
        self.create_side_btn("⚙️ Configuración", self.show_config_tab).pack(pady=5, padx=20, fill="x")
        self.create_side_btn("📁 Base de Datos", self.show_data_tab).pack(pady=20, padx=20, fill="x")
        ctk.CTkButton(self.sidebar, text="Cerrar Sesión", fg_color="transparent", text_color="#F85149", command=self.setup_login_ui).pack(side="bottom", pady=30)
        
        self.content_area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=40, pady=40)
        self.show_products_tab()

    def create_side_btn(self, text, command):
        return ctk.CTkButton(self.sidebar, text=text, height=45, anchor="w", fg_color="transparent", font=("Inter", 14), command=command)

    def show_products_tab(self):
        for widget in self.content_area.winfo_children(): widget.destroy()
        header = ctk.CTkFrame(self.content_area, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="Gestión de Inventario", font=("Inter", 32, "bold"), text_color=COLOR_TEXT_MAIN).pack(side="left")

        # Buscador dinámico
        self.search_entry = ctk.CTkEntry(header, width=350, height=40, placeholder_text="🔍 Buscar por código o referencia...", fg_color="#0D1117", border_color="#30363D")
        self.search_entry.pack(side="right", pady=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_product_list())

        # Main body: table + preview side panel
        body = ctk.CTkFrame(self.content_area, fg_color="transparent")
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=0)
        body.rowconfigure(0, weight=1)

        # --- Table Container (left) ---
        table_card = ctk.CTkFrame(body)
        SharedStyles.apply_card_style(table_card)
        table_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        table_card.grid_columnconfigure(0, weight=1)
        table_card.grid_rowconfigure(0, weight=1)

        columns = ("codigop", "referencia", "exisact", "pventa", "precio_bs", "imagen")
        self.tree = ttk.Treeview(table_card, columns=columns, show="headings", selectmode="browse")

        headings = [("codigop", "Código"), ("referencia", "Referencia"), ("exisact", "Existencia"), ("pventa", "Precio ($)"), ("precio_bs", "Precio (Bs)"), ("imagen", "Imagen")]
        for col, text in headings:
            self.tree.heading(col, text=text)
            self.tree.column(col, anchor="center", width=120 if col != "referencia" else 350)

        vsb = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_card, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.tree.bind("<Double-1>", lambda e: self.open_edit_dialog())
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

        # --- Image Preview Panel (right) ---
        self.preview_panel = ctk.CTkFrame(body, width=220)
        SharedStyles.apply_card_style(self.preview_panel)
        self.preview_panel.grid(row=0, column=1, sticky="nsew")
        self.preview_panel.pack_propagate(False)

        ctk.CTkLabel(self.preview_panel, text="Vista Previa", font=("Inter", 14, "bold"), text_color=COLOR_ACCENT).pack(pady=(20, 10))

        self.preview_img_label = ctk.CTkLabel(self.preview_panel, text="📦", font=("Inter", 60), width=180, height=180)
        self.preview_img_label.pack(padx=20, pady=10)

        self.preview_name_label = ctk.CTkLabel(self.preview_panel, text="Selecciona\nun producto", font=("Inter", 12), text_color=COLOR_TEXT_DIM, wraplength=180, justify="center")
        self.preview_name_label.pack(padx=10, pady=10)

        self.preview_status_label = ctk.CTkLabel(self.preview_panel, text="", font=("Inter", 11), text_color=COLOR_TEXT_DIM)
        self.preview_status_label.pack()

        ctk.CTkButton(self.preview_panel, text="✏️ Editar", height=40, command=self.open_edit_dialog).pack(padx=20, pady=(20, 5), fill="x")
        
        self.delete_btn = ctk.CTkButton(self.preview_panel, text="🗑️ Eliminar Producto", height=40, fg_color="#30363D", hover_color="#F85149", state="disabled", command=self.delete_selected_product)
        self.delete_btn.pack(padx=20, pady=5, fill="x")

        # --- Footer ---
        footer = ctk.CTkFrame(self.content_area, fg_color="transparent")
        footer.pack(fill="x", pady=(15, 0))
        ctk.CTkLabel(footer, text="Clic → previsualizar  •  Doble clic → editar", text_color=COLOR_TEXT_DIM, font=("Inter", 12)).pack(side="left")

        self.refresh_product_list()

    def on_row_select(self, event=None):
        """Actualiza el panel de previsualización al seleccionar una fila."""
        sel = self.tree.selection()
        if not sel:
            return
        cod = str(sel[0])
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT referencia, image_path FROM productos WHERE codigop = ?", (cod,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return

        name = row['referencia'] or "Sin nombre"
        img_path = row['image_path']

        self.preview_name_label.configure(text=name[:60] + ("..." if len(name) > 60 else ""))

        # Limpiar agresivamente para evitar "efecto fantasma" (destruir y recrear)
        self.preview_img_label.destroy()
        self.preview_img_label = ctk.CTkLabel(self.preview_panel, text="", width=180, height=180)
        self.preview_img_label.pack(padx=20, pady=10, before=self.preview_name_label)

        if img_path and os.path.exists(img_path):
            try:
                pil_img = Image.open(img_path).resize((180, 180), Image.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(180, 180))
                self.preview_img_label.configure(image=ctk_img, text="")
                self.preview_img_label._ctk_image = ctk_img 
                self.preview_status_label.configure(text="✅ Con imagen", text_color="#3FB950")
            except Exception:
                self.preview_img_label.configure(image=None, text="⚠️", font=("Inter", 60))
                self.preview_status_label.configure(text="Error al cargar", text_color="#F85149")
        else:
            self.preview_img_label.configure(image=None, text="📦", font=("Inter", 60))
            self.preview_status_label.configure(text="❌ Sin imagen asignada", text_color=COLOR_TEXT_DIM)
        
        self.delete_btn.configure(state="normal", fg_color="#30363D")

    def delete_selected_product(self):
        """Elimina el producto seleccionado tras confirmación, sincronizando con la DB y el Excel."""
        sel = self.tree.selection()
        if not sel: return
        cod = str(sel[0])
        if messagebox.askyesno("Eliminar Producto", f"¿Estás seguro de que deseas eliminar permanentemente el producto '{cod}'?"):
            if sync.delete_product(cod):
                messagebox.showinfo("Éxito", "Producto eliminado correctamente.")
                self.refresh_product_list()
                
                # Resetear la vista previa a su estado inicial
                self.preview_name_label.configure(text="Selecciona\nun producto", text_color=COLOR_TEXT_DIM)
                self.preview_status_label.configure(text="")
                if self.preview_img_label: self.preview_img_label.destroy()
                self.preview_img_label = ctk.CTkLabel(self.preview_panel, text="📦", font=("Inter", 60), width=180, height=180)
                self.preview_img_label.pack(padx=20, pady=10, before=self.preview_name_label)
                self.delete_btn.configure(state="disabled", fg_color="#30363D")
            else:
                messagebox.showerror("Error", "No se pudo eliminar el producto.")

    def refresh_product_list(self):
        """Refresca la tabla, opcionalmente filtrando por el buscador."""
        query = self.search_entry.get().strip() if hasattr(self, 'search_entry') else ""
        
        for item in self.tree.get_children(): self.tree.delete(item)
        rate = get_exchange_rate()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            if query:
                sql = "SELECT codigop, referencia, exisact, pventa, image_path FROM productos WHERE codigop LIKE ? OR referencia LIKE ?"
                cursor.execute(sql, (f"%{query}%", f"%{query}%"))
            else:
                cursor.execute("SELECT codigop, referencia, exisact, pventa, image_path FROM productos")
            
            for row in cursor.fetchall():
                bs_price = row['pventa'] * rate if row['pventa'] else 0.0
                has_img = "✅ Sí" if row['image_path'] and os.path.exists(row['image_path']) else "❌ No"
                vals = (
                    row['codigop'], 
                    row['referencia'], 
                    f"{row['exisact']:.0f}", 
                    f"$ {row['pventa']:.2f}",
                    f"Bs. {bs_price:,.2f}",
                    has_img
                )
                self.tree.insert("", "end", iid=row['codigop'], values=vals)
        except Exception as e:
            print(f"Error cargando db: {e}")
            
        conn.close()

    def open_edit_dialog(self):
        sel = self.tree.selection()
        if not sel: return
        
        # Obtenemos directamente el ID del registro que guardamos como `iid` sin que la tabla modifique los ceros
        cod = str(sel[0])
        print(f"Buscando producto: {cod}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM productos WHERE codigop = ?", (cod,))
        product = cursor.fetchone()
        conn.close()
        
        if product: 
            print("Producto encontrado, abriendo diálogo")
            EditProductDialog(self.master, dict(product), self.refresh_product_list)
        else:
            print(f"Producto {cod} no encontrado en base de datos")

    def show_config_tab(self):
        for widget in self.content_area.winfo_children(): widget.destroy()
        ctk.CTkLabel(self.content_area, text="Configuración del Sistema", font=("Inter", 32, "bold")).pack(anchor="w", pady=(0, 40))
        
        container = ctk.CTkFrame(self.content_area, fg_color="transparent")
        container.pack(fill="both", expand=True)
        
        # --- COLUMNA 1: TASA Y ESTADÍSTICAS ---
        left_col = ctk.CTkFrame(container, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 20))
        
        # Tarjeta 1: Tasa de Cambio
        card_rate = ctk.CTkFrame(left_col)
        SharedStyles.apply_card_style(card_rate)
        card_rate.pack(fill="x", pady=(0, 20))
        
        rate = get_exchange_rate()
        ctk.CTkLabel(card_rate, text="Tasa de Cambio (USD ➔ VES)", font=("Inter", 16, "bold"), text_color=COLOR_ACCENT).pack(pady=(20, 5))
        ctk.CTkLabel(card_rate, text=f"Bs. {rate:,.2f}", font=("Inter", 42, "bold"), text_color=COLOR_GOLD).pack(pady=10)
        
        self.rate_entry = ctk.CTkEntry(card_rate, width=200, height=40, placeholder_text="Nueva tasa...", fg_color="#0D1117")
        self.rate_entry.pack(pady=10)
        ctk.CTkButton(card_rate, text="Actualizar Tasa", height=40, command=self.update_rate).pack(pady=(0, 20), padx=30, fill="x")

        # Tarjeta 2: Estadísticas del Sistema
        card_stats = ctk.CTkFrame(left_col)
        SharedStyles.apply_card_style(card_stats)
        card_stats.pack(fill="x")
        
        conn = get_db_connection()
        total_p = conn.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
        total_stock = conn.execute("SELECT SUM(exisact) FROM productos").fetchone()[0] or 0
        total_imgs = conn.execute("SELECT COUNT(*) FROM productos WHERE image_path IS NOT NULL AND image_path != ''").fetchone()[0]
        conn.close()

        ctk.CTkLabel(card_stats, text="Informe del Sistema", font=("Inter", 16, "bold"), text_color=COLOR_ACCENT).pack(pady=(20, 10))
        
        stats_frame = ctk.CTkFrame(card_stats, fg_color="transparent")
        stats_frame.pack(fill="x", padx=30, pady=(0, 25))
        
        def add_statline(label, value):
            f = ctk.CTkFrame(stats_frame, fg_color="transparent")
            f.pack(fill="x", pady=5)
            ctk.CTkLabel(f, text=label, font=("Inter", 13), text_color=COLOR_TEXT_DIM).pack(side="left")
            ctk.CTkLabel(f, text=str(value), font=("Inter", 14, "bold")).pack(side="right")

        add_statline("Productos registrados:", total_p)
        add_statline("Stock total acumulado:", f"{total_stock:.0f} unid.")

        # --- COLUMNA 2: SEGURIDAD ---
        right_col = ctk.CTkFrame(container, fg_color="transparent")
        right_col.pack(side="left", fill="both", expand=True)

        card_sec = ctk.CTkFrame(right_col)
        SharedStyles.apply_card_style(card_sec)
        card_sec.pack(fill="both", expand=True)
        
        ctk.CTkLabel(card_sec, text="🛡️ Seguridad", font=("Inter", 22, "bold")).pack(pady=(40, 10))
        ctk.CTkLabel(card_sec, text="Cambiar Contraseña de Administrador", font=("Inter", 14), text_color=COLOR_TEXT_DIM).pack(pady=(0, 30))
        
        self.old_pass = ctk.CTkEntry(card_sec, width=300, height=45, placeholder_text="Contraseña Actual", show="*", fg_color="#0D1117")
        self.old_pass.pack(pady=10)
        
        self.new_pass_1 = ctk.CTkEntry(card_sec, width=300, height=45, placeholder_text="Nueva Contraseña", show="*", fg_color="#0D1117")
        self.new_pass_1.pack(pady=10)
        
        self.new_pass_2 = ctk.CTkEntry(card_sec, width=300, height=45, placeholder_text="Confirmar Nueva Contraseña", show="*", fg_color="#0D1117")
        self.new_pass_2.pack(pady=10)
        
        btn_pass = ctk.CTkButton(card_sec, text="Guardar Cambios", height=50, command=self.update_password)
        SharedStyles.apply_accent_button(btn_pass)
        btn_pass.pack(pady=30, padx=50, fill="x")

    def update_rate(self):
        try:
            val = float(self.rate_entry.get().strip())
            conn = get_db_connection()
            conn.cursor().execute("UPDATE configuracion SET value = ? WHERE key = 'tasa_cambio'", (str(val),))
            conn.commit()
            conn.close()
            messagebox.showinfo("Éxito", "Tasa actualizada correctamente.")
            self.show_config_tab()
        except ValueError: messagebox.showerror("Error", "Ingrese un número decimal válido.")

    def update_password(self):
        old = self.old_pass.get().strip()
        n1 = self.new_pass_1.get().strip()
        n2 = self.new_pass_2.get().strip()
        
        if not old or not n1 or not n2:
            return messagebox.showerror("Campos vacíos", "Por favor completa todos los campos de seguridad.")
            
        if n1 != n2:
            return messagebox.showerror("Error de Coincidencia", "Las nuevas contraseñas no coinciden entre sí.")
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM configuracion WHERE key='admin_pass'")
        current_db_pass = cursor.fetchone()[0]
        
        if old != current_db_pass:
            conn.close()
            return messagebox.showerror("Seguridad", "La contraseña actual suministrada es incorrecta.")
            
        cursor.execute("UPDATE configuracion SET value = ? WHERE key='admin_pass'", (n1,))
        conn.commit()
        conn.close()
        
        messagebox.showinfo("Éxito", "La contraseña de administrador ha sido actualizada correctamente.")
        self.show_config_tab()

    def show_stats_tab(self):
        for widget in self.content_area.winfo_children(): widget.destroy()
        ctk.CTkLabel(self.content_area, text="Estadísticas de Inventario", font=("Inter", 32, "bold")).pack(anchor="w", pady=(0, 40))
        
        container = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        container.pack(fill="both", expand=True)
        
        conn = get_db_connection()
        
        # 1. Consultas a la base de datos
        most_stock = conn.execute("SELECT referencia, exisact FROM productos ORDER BY exisact DESC LIMIT 1").fetchone()
        least_stock = conn.execute("SELECT referencia, exisact FROM productos WHERE exisact > 0 ORDER BY exisact ASC LIMIT 1").fetchone()
        highest_price = conn.execute("SELECT referencia, pventa FROM productos ORDER BY pventa DESC LIMIT 1").fetchone()
        lowest_price = conn.execute("SELECT referencia, pventa FROM productos WHERE pventa > 0 ORDER BY pventa ASC LIMIT 1").fetchone()
        top_searched = conn.execute("SELECT referencia, busquedas, image_path FROM productos WHERE busquedas > 0 ORDER BY busquedas DESC LIMIT 5").fetchall()
        
        conn.close()

        # Layout de tarjetas
        grid = ctk.CTkFrame(container, fg_color="transparent")
        grid.pack(fill="x", pady=10)
        grid.columnconfigure((0,1), weight=1)

        def create_stat_card(parent, title, value, subtext, icon, row, col, color=COLOR_ACCENT):
            c = ctk.CTkFrame(parent)
            SharedStyles.apply_card_style(c)
            c.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            ctk.CTkLabel(c, text=icon, font=("Inter", 32)).pack(pady=(20, 5))
            ctk.CTkLabel(c, text=title, font=("Inter", 14, "bold"), text_color=COLOR_TEXT_DIM).pack()
            ctk.CTkLabel(c, text=value, font=("Inter", 24, "bold"), text_color=color).pack(pady=5)
            ctk.CTkLabel(c, text=subtext, font=("Inter", 12), text_color=COLOR_TEXT_DIM, wraplength=200).pack(pady=(0, 20))

        # Fila 1: Stock
        s_max = f"{most_stock['exisact']:.0f} unid." if most_stock else "N/A"
        n_max = most_stock['referencia'][:40] if most_stock else "Sin datos"
        create_stat_card(grid, "Mayor Existencia", s_max, n_max, "📈", 0, 0, "#3FB950")

        s_min = f"{least_stock['exisact']:.0f} unid." if least_stock else "N/A"
        n_min = least_stock['referencia'][:40] if least_stock else "Sin datos"
        create_stat_card(grid, "Menor Existencia", s_min, n_min, "📉", 0, 1, "#F85149")

        # Fila 2: Precios
        p_max = f"$ {highest_price['pventa']:.2f}" if highest_price else "N/A"
        np_max = highest_price['referencia'][:40] if highest_price else "Sin datos"
        create_stat_card(grid, "Producto más Caro", p_max, np_max, "💎", 1, 0, COLOR_GOLD)

        p_min = f"$ {lowest_price['pventa']:.2f}" if lowest_price else "N/A"
        np_min = lowest_price['referencia'][:40] if lowest_price else "Sin datos"
        create_stat_card(grid, "Producto más Barato", p_min, np_min, "🏷️", 1, 1, "#3FB950")

        # Sección: Top Buscados (Ranking de Interés)
        ctk.CTkLabel(container, text="🔥 Top 5 - Los más Buscados por Clientes", font=("Inter", 20, "bold"), text_color=COLOR_ACCENT).pack(anchor="w", padx=10, pady=(30, 20))
        
        ranking_frame = ctk.CTkFrame(container, fg_color="transparent")
        ranking_frame.pack(fill="x", padx=10)
        
        if not top_searched:
            ctk.CTkLabel(ranking_frame, text="Aún no hay datos de búsquedas registrados.", font=("Inter", 14), text_color=COLOR_TEXT_DIM).pack(pady=20)
        else:
            for i, p in enumerate(top_searched):
                item = ctk.CTkFrame(ranking_frame)
                SharedStyles.apply_card_style(item)
                item.pack(fill="x", pady=5)
                
                ctk.CTkLabel(item, text=f"#{i+1}", font=("Inter", 18, "bold"), width=50).pack(side="left", padx=20)
                
                # Info
                info = ctk.CTkFrame(item, fg_color="transparent")
                info.pack(side="left", fill="both", expand=True, padx=10, pady=10)
                ctk.CTkLabel(info, text=p['referencia'], font=("Inter", 14, "bold"), anchor="w").pack(fill="x")
                ctk.CTkLabel(info, text=f"Total de consultas: {p['busquedas']}", font=("Inter", 12), text_color=COLOR_TEXT_DIM, anchor="w").pack(fill="x")
                
                # Badge de "Interés"
                ctk.CTkLabel(item, text="INTERÉS ALTO", font=("Inter", 10, "bold"), fg_color="#238636", text_color="white", corner_radius=10, width=100, height=25).pack(side="right", padx=20)

    def show_data_tab(self):
        for widget in self.content_area.winfo_children(): widget.destroy()
        ctk.CTkLabel(self.content_area, text="Sección de Exportación e Importación", font=("Inter", 32, "bold")).pack(anchor="w", pady=(0, 40))
        
        container = ctk.CTkFrame(self.content_area, fg_color="transparent")
        container.pack(fill="both", expand=True)
        
        # --- COLUMNA IZQUIERDA: IMPORTACIÓN ( ENTRADA ) ---
        ci = ctk.CTkFrame(container, width=380, height=550)
        SharedStyles.apply_card_style(ci)
        ci.pack(side="left", padx=(0, 20), fill="both", expand=True)
        ctk.CTkLabel(ci, text="📥", font=("Inter", 80)).pack(pady=(40, 20))
        ctk.CTkLabel(ci, text="Gestor de Entrada", font=("Inter", 18, "bold")).pack()
        ctk.CTkLabel(ci, text="Sube datos o imágenes al sistema para actualizar el inventario.", font=("Inter", 13), text_color=COLOR_TEXT_DIM, wraplength=280).pack(pady=20)
        
        # Botones Import
        ctk.CTkButton(ci, text="Actualizar Datos (Excel)", height=45, command=self.handle_smart_import).pack(pady=10, padx=40, fill="x")
        ctk.CTkButton(ci, text="Importar Carpeta de Fotos", height=45, fg_color="#30363D", command=self.handle_image_import).pack(pady=10, padx=40, fill="x")
        
        # --- COLUMNA DERECHA: EXPORTACIÓN ( SALIDA ) ---
        ce = ctk.CTkFrame(container, width=380, height=550)
        SharedStyles.apply_card_style(ce)
        ce.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(ce, text="📤", font=("Inter", 80)).pack(pady=(40, 20))
        ctk.CTkLabel(ce, text="Gestor de Salida", font=("Inter", 18, "bold")).pack()
        ctk.CTkLabel(ce, text="Crea respaldos de tus datos o genera copias para trabajar en Excel.", font=("Inter", 13), text_color=COLOR_TEXT_DIM, wraplength=280).pack(pady=20)
        
        # Botones Export
        ctk.CTkButton(ce, text="Respaldo Completo (Excel + Fotos)", height=45, fg_color="#238636", command=self.handle_full_backup).pack(pady=10, padx=40, fill="x")
        ctk.CTkButton(ce, text="Exportar Solo Excel", height=45, fg_color="#30363D", command=self.handle_excel_only_export).pack(pady=10, padx=40, fill="x")
        ctk.CTkButton(ce, text="📥 Exportar Plantilla Vacía", height=45, fg_color="#30363D", command=self.handle_template_export).pack(pady=10, padx=40, fill="x")

    def handle_template_export(self):
        path = filedialog.asksaveasfilename(
            title="Guardar Plantilla Vacía",
            defaultextension=".xlsx",
            initialfile="plantilla_nuevos_productos.xlsx",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if path:
            if sync.export_template(path):
                messagebox.showinfo("Éxito", f"Plantilla guardada en:\n{path}\n\nÚsala para agregar nuevos productos al sistema.")
            else:
                messagebox.showerror("Error", "No se pudo generar la plantilla.")

    def handle_full_backup(self):
        folder = filedialog.askdirectory(title="Selecciona dónde guardar el respaldo")
        if folder:
            if sync.create_full_backup(folder):
                messagebox.showinfo("Respaldo Exitoso", "Se ha creado el respaldo completo (Carpeta con Excel + Fotos).")
            else:
                messagebox.showerror("Error", "No se pudo crear el respaldo. Verifica permisos o si el archivo Excel está abierto.")

    def handle_excel_only_export(self):
        path = filedialog.asksaveasfilename(
            title="Guardar Excel",
            defaultextension=".xlsx",
            initialfile="respaldo_base_datos.xlsx",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if path:
            if sync.export_db_to_excel(path):
                messagebox.showinfo("Exportación Exitosa", f"Excel guardado en:\n{path}")
            else:
                messagebox.showerror("Error", "No se pudo exportar el archivo.")

    def handle_smart_import(self):
        path = filedialog.askopenfilename(title="Selecciona el Excel para actualizar", filetypes=[("Excel files", "*.xlsx *.xls")])
        if path:
            if sync.import_excel_to_db(path):
                messagebox.showinfo("Importación Exitosa", "Los productos se han actualizado correctamente respetando tus imágenes actuales.")
                self.refresh_product_list()
            else:
                messagebox.showerror("Error de Importación", "No se pudo procesar el archivo. Asegúrate de que tenga la estructura correcta.")

    def handle_image_import(self):
        folder = filedialog.askdirectory(title="Selecciona la carpeta que contiene las imágenes de tus productos")
        if folder:
            success, count = sync.import_images_from_folder(folder)
            if success:
                messagebox.showinfo("Importación Exitosa", f"Se han copiado {count} imágenes al sistema satisfactoriamente.")
            else:
                messagebox.showerror("Error", "Ocurrió un error al intentar copiar las fotos.")

    def run_data_op(self, op):
        if op(): messagebox.showinfo("Éxito", "Proceso de datos finalizado con éxito.")
        else: messagebox.showerror("Operación Denegada", "Hubo un error al ejecutar la orden.\nPor favor, verifica que si el excel está abierto por otro programa, lo modifiques y lo cierres antes de intentarlo.")
