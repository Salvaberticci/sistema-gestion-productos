import customtkinter as ctk
from PIL import Image, ImageTk
import os
import time
import winsound  # Alertas sonoras en Windows
from utils import get_exchange_rate, calculate_prices, format_currency, search_product
from database import get_db_connection
from ui_shared import COLOR_BG, COLOR_CARD, COLOR_ACCENT, COLOR_TEXT_MAIN, COLOR_TEXT_DIM, COLOR_GOLD, SharedStyles
import tkinter as tk
import random

class FloatingBackground(tk.Canvas):
    """Lienzo animado ligero con iconos flotantes sutiles."""
    def __init__(self, master, **kwargs):
        super().__init__(master, borderwidth=0, highlightthickness=0, **kwargs)
        self.particles = []
        self.icons = ["📦", "🏷️", "💰", "🛒", "🛍️", "💳"]
        self.running = False
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        self._create_particles()

    def _create_particles(self):
        self.delete("all")
        self.particles = []
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10 or h < 10: return
        
        for _ in range(25): # Más partículas para pantalla completa
            x, y = random.randint(0, w), random.randint(0, h)
            vx, vy = random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5)
            icon = random.choice(self.icons)
            size = random.randint(20, 45)
            # Color muy tenue (azul oscuro/grisáceo)
            p_id = self.create_text(x, y, text=icon, font=("Inter", size), fill="#1C2128")
            self.particles.append({"id": p_id, "x": x, "y": y, "vx": vx, "vy": vy})

    def start(self):
        if not self.running:
            self.running = True
            self._animate()

    def stop(self):
        self.running = False

    def _animate(self):
        if not self.running: return
        w, h = self.winfo_width(), self.winfo_height()
        if w < 10 or h < 10: 
            self.after(100, self._animate)
            return

        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            
            # Rebotar en bordes
            if p["x"] < 0 or p["x"] > w: p["vx"] *= -1
            if p["y"] < 0 or p["y"] > h: p["vy"] *= -1
            
            self.coords(p["id"], p["x"], p["y"])
        
        self.after(40, self._animate) # ~25 FPS suficiente para fluidez sutil

class ProductCard(ctk.CTkFrame):
    def __init__(self, master, product, on_click):
        super().__init__(master)
        SharedStyles.apply_card_style(self)
        self.product = product
        self.on_click = on_click
        self.setup_ui()
        self.bind("<Button-1>", lambda e: self.on_click(self.product['codigop']))

    def setup_ui(self):
        # Cargar imagen si existe
        img_p = self.product['image_path']
        if img_p and os.path.exists(img_p):
            try:
                pil_img = Image.open(img_p).resize((130, 100), Image.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(130, 100))
                self.img_label = ctk.CTkLabel(self, image=ctk_img, text="", width=150, height=120)
                self.img_label._ctk_image = ctk_img
            except:
                self.img_label = ctk.CTkLabel(self, text="📦", font=("Inter", 40), width=150, height=120)
        else:
            self.img_label = ctk.CTkLabel(self, text="📦", font=("Inter", 40), width=150, height=120)
            
        self.img_label.pack(pady=(15, 5))
        self.title_label = ctk.CTkLabel(self, text=self.product['referencia'][:40]+"...", font=("Inter", 13, "bold"), text_color=COLOR_TEXT_MAIN, wraplength=160)
        self.title_label.pack(padx=10)
        rate = get_exchange_rate()
        _, ves = calculate_prices(self.product['pventa'], rate)
        self.price_label = ctk.CTkLabel(self, text=format_currency(ves, "Bs."), font=("Inter", 16, "bold"), text_color=COLOR_ACCENT)
        self.price_label.pack(pady=(5, 15))

class ConsultaScreen(ctk.CTkFrame):
    def __init__(self, master, on_admin_click):
        super().__init__(master, fg_color=COLOR_BG)
        self.master = master
        self.on_admin_click = on_admin_click
        self.last_activity = time.time()
        self.setup_ui()
        self.load_featured_products()
        self.check_inactivity()
        
    def setup_ui(self):
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(20, 10))
        if os.path.exists("logo.png"):
            logo_img = Image.open("logo.png")
            new_w = 250
            new_h = int(logo_img.size[1] * (new_w / logo_img.size[0]))
            self.ctk_logo = ctk.CTkImage(light_image=logo_img, dark_image=logo_img, size=(new_w, new_h))
            ctk.CTkLabel(self.header_frame, image=self.ctk_logo, text="").pack(pady=(10, 0))
        else:
            ctk.CTkLabel(self.header_frame, text="EL REBUSQUE", font=("Inter", 48, "bold"), text_color=COLOR_GOLD).pack()
        
        ctk.CTkLabel(self.header_frame, text="Escanea tu código de barras o busca un producto", font=("Inter", 18), text_color=COLOR_ACCENT).pack(pady=5)
        
        self.search_container = ctk.CTkFrame(self, fg_color="transparent")
        self.search_container.pack(pady=20)
        self.search_entry = ctk.CTkEntry(self.search_container, width=700, height=60, placeholder_text="🔍 Ingrese código o nombre...", font=("Inter", 20), border_color=COLOR_ACCENT, border_width=2, corner_radius=30, fg_color="#1C2128")
        self.search_entry.pack()
        self.search_entry.bind("<Return>", self.on_search)
        self.search_entry.focus_set()
        
        self.result_overlay = ctk.CTkFrame(self, fg_color=COLOR_BG)
        self.result_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.result_overlay.lower()
        
        # Fondo animado integrado
        self.bg_animation = FloatingBackground(self.result_overlay, bg="#0D1117")
        self.bg_animation.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        self.setup_result_view()
        
        ctk.CTkLabel(self, text="Catálogo de Productos", font=("Inter", 22, "bold"), text_color=COLOR_TEXT_MAIN).pack(anchor="w", padx=60, pady=(20, 5))
        self.scroll_frame = ctk.CTkScrollableFrame(self, orientation="horizontal", fg_color="transparent", height=280)
        self.scroll_frame.pack(fill="x", padx=50)
        # Ocultar la barra de desplazamiento física
        try: self.scroll_frame._scrollbar.grid_forget()
        except: pass
        
        self.scroll_pos = 0
        self.animate_scroll()
        
        self.admin_btn = ctk.CTkButton(self, text="⚙️ Panel Admin", width=160, height=45, fg_color=COLOR_CARD, border_width=1, border_color=COLOR_ACCENT, text_color=COLOR_ACCENT, hover_color="#1C2128", corner_radius=25, font=("Inter", 13, "bold"), command=self.on_admin_click)
        self.admin_btn.place(relx=0.98, rely=0.96, anchor="se")

    def animate_scroll(self):
        """Animación suave de desplazamiento infinito para el catálogo."""
        try:
            canvas = self.scroll_frame._parent_canvas
            self.scroll_pos += 0.0007 # Velocidad ligeramente aumentada para mayor fluidez
            
            # Si llegamos al final del scroll, resetear a 0
            if self.scroll_pos >= 1.0:
                self.scroll_pos = 0
                
            canvas.xview_moveto(self.scroll_pos)
        except: pass
        self.after(50, self.animate_scroll)

    def setup_result_view(self):
        self.result_card = ctk.CTkFrame(self.result_overlay)
        SharedStyles.apply_card_style(self.result_card)
        self.result_card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.85, relheight=0.7)
        ctk.CTkButton(self.result_card, text="✕", width=40, height=40, fg_color="transparent", text_color=COLOR_TEXT_DIM, hover_color="#30363D", command=self.hide_results).place(relx=0.98, rely=0.02, anchor="ne")
        
        # Grid config
        self.result_card.grid_columnconfigure(1, weight=1)
        
        self.res_img = ctk.CTkLabel(self.result_card, text="📦", font=("Inter", 120), width=350, height=350)
        self.res_img.grid(row=0, column=0, rowspan=2, padx=40, pady=40)
        
        # Nombre responsivo y con mejor ajuste
        self.res_desc = ctk.CTkLabel(self.result_card, text="NOMBRE_PRODUCTO", font=("Inter", 38, "bold"), text_color=COLOR_TEXT_MAIN, wraplength=800, anchor="w", justify="left")
        self.res_desc.grid(row=0, column=1, sticky="nw", pady=(60, 0), padx=(0, 40))
        
        # Frame para precio (Solo Bs.)
        self.price_frame = ctk.CTkFrame(self.result_card, fg_color="transparent")
        self.price_frame.grid(row=1, column=1, sticky="sw", pady=(0, 60), padx=(0, 40))
        
        self.res_price_ves = ctk.CTkLabel(self.price_frame, text="Bs. 0.00", font=("Inter", 90, "bold"), text_color=COLOR_ACCENT)
        self.res_price_ves.pack(anchor="w")

    def load_featured_products(self):
        for widget in self.scroll_frame.winfo_children(): widget.destroy()
        conn = get_db_connection()
        products = conn.execute("SELECT * FROM productos LIMIT 15").fetchall()
        conn.close()
        for p in products:
            card = ProductCard(self.scroll_frame, p, self.on_card_click)
            card.pack(side="left", padx=10, pady=10)

    def on_card_click(self, id_art):
        p = search_product(id_art)
        if p: self.show_product(p)

    def on_search(self, event=None):
        query = self.search_entry.get().strip()
        self.search_entry.delete(0, 'end')
        if not query: return
        self.last_activity = time.time()
        p = search_product(query)
        if p:
            winsound.Beep(800, 150) # Éxito
            self.show_product(p)
        else:
            winsound.Beep(400, 400) # Error
            self.hide_results()
        self.search_entry.focus_set()

    def show_product(self, product):
        self.last_activity = time.time()
        rate = get_exchange_rate()
        _, ves = calculate_prices(product['pventa'], rate)
        
        # Ajuste dinámico de fuente para nombres muy largos
        desc = product['referencia']
        font_size = 38 if len(desc) < 60 else 30 if len(desc) < 100 else 24
        self.res_desc.configure(text=desc, font=("Inter", font_size, "bold"))
        
        self.res_price_ves.configure(text=format_currency(ves, "Bs."))
        
        if product['image_path'] and os.path.exists(product['image_path']):
            img = Image.open(product['image_path']).resize((350, 350), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.res_img.configure(image=photo, text="")
            self.res_img.image = photo
        else: self.res_img.configure(text="📦", image=None)
        
        self.result_overlay.lift()
        self.bg_animation.start()

    def hide_results(self):
        self.bg_animation.stop()
        self.result_overlay.lower()
        self.search_entry.focus_set()

    def check_inactivity(self):
        if time.time() - self.last_activity > 15: self.hide_results()
        self.after(1000, self.check_inactivity)
