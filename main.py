import tkinter as tk
from inscription_etudiant import EtudiantPage
from presence_gui import PresencePage
from PIL import Image, ImageTk

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Système de Pointage")
        self.geometry("1250x650")  # Adapter selon tes préférences
        self.resizable(False, False)
        self.configure(bg="#1592DB")

        # Boutons de navigation
        bouton_frame = tk.Frame(self,bg="blue")
        bouton_frame.pack(side="top", fill="x")

        btn_enregistrer = tk.Button(bouton_frame, text="📘 Enregistrer", font=("Arial", 14), command=self.afficher_page_etudiant)
        btn_enregistrer.pack(side="left", padx=20)

        btn_presence = tk.Button(bouton_frame, text="✅ Présence", font=("Arial", 14), command=self.afficher_page_presence)
        btn_presence.pack(side="right",  padx=20)

        # Conteneur pour les pages
        self.container = tk.Frame(self,bg="#1592DB")
        self.container.pack(fill="both", expand=True)

        self.page_actuelle = None
        
        logo_image = Image.open("logo.jpg")
        logo_image = logo_image.resize((100, 50))  # Redimensionne si nécessaire
        self.logo = ImageTk.PhotoImage(logo_image)

        logo_label = tk.Label(self, image=self.logo)
        logo_label.pack(pady=10)

    def afficher_page_etudiant(self):
        if self.page_actuelle:
            self.page_actuelle.destroy()
        self.page_actuelle = EtudiantPage(self.container)
        self.page_actuelle.pack(fill="both", expand=True)

    def afficher_page_presence(self):
        if self.page_actuelle:
            self.page_actuelle.destroy()
        self.page_actuelle = PresencePage(self.container)
        self.page_actuelle.pack(fill="both", expand=True)

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
