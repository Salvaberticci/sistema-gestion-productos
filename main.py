import customtkinter as ctk
from ui_consulta import ConsultaScreen
from ui_admin import AdminScreen
from ui_shared import center_window, COLOR_BG
import os
import sync

class ProductSystemApp(ctk.CTk):
    def __init__(self):
        super().__init__(fg_color=COLOR_BG)
        
        # Sincronización inicial con Excel al arrancar
        sync.sync_excel_to_db()
        
        self.title("Sistema de Productos - El Rebusque")
        self.width = 1280
        self.height = 800
        center_window(self, self.width, self.height)
        
        # Contenedor principal para cambiar entre pantallas
        self.container = ctk.CTkFrame(self, fg_color=COLOR_BG)
        self.container.pack(fill="both", expand=True)
        
        self.show_consulta()
        
    def show_consulta(self):
        # Limpiar contenedor
        for widget in self.container.winfo_children():
            widget.destroy()
            
        self.consulta_screen = ConsultaScreen(self.container, self.show_admin)
        self.consulta_screen.pack(fill="both", expand=True)
        
    def show_admin(self):
        for widget in self.container.winfo_children():
            widget.destroy()
            
        self.admin_screen = AdminScreen(self.container, self.show_consulta)
        self.admin_screen.pack(fill="both", expand=True)

if __name__ == "__main__":
    # Asegurarse de que la base de datos existe y las carpetas están creadas
    from database import init_db
    init_db()
        
    app = ProductSystemApp()
    app.mainloop()
