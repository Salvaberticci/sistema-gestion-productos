import customtkinter as ctk

# Colores Tecnológicos Premium
COLOR_BG = "#0B0E14"          # Fondo ultra oscuro (espacial)
COLOR_CARD = "#161B22"        # Color de las tarjetas (estilo GitHub dark)
COLOR_ACCENT = "#58A6FF"      # Azul Cyan brillante (Tech)
COLOR_ACCENT_HOVER = "#1F6FEB"
COLOR_TEXT_MAIN = "#F0F6FC"
COLOR_TEXT_DIM = "#8B949E"
COLOR_SUCCESS = "#238636"
COLOR_GOLD = "#D1A054"        # Mantener un toque de dorado para "El Rebusque"

ctk.set_appearance_mode("dark")

class SharedStyles:
    FONT_TITLE = ("Inter", 32, "bold")
    FONT_SUBTITLE = ("Inter", 20, "bold")
    FONT_BODY = ("Inter", 14)
    FONT_PRICE_BIG = ("Inter", 48, "bold")
    FONT_PRICE_SM = ("Inter", 24, "bold")
    
    @staticmethod
    def apply_card_style(frame):
        frame.configure(
            fg_color=COLOR_CARD,
            corner_radius=15,
            border_width=1,
            border_color="#30363D"
        )

    @staticmethod
    def apply_accent_button(button):
        button.configure(
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            text_color="#FFFFFF",
            corner_radius=10,
            font=("Inter", 13, "bold")
        )

def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")
