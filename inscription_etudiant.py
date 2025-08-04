import serial
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import mysql.connector
import threading
import time
import os
import shutil

PORT_SERIE = '/dev/ttyACM0'  # Adapter si besoin
BAUDRATE = 9600

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'controle_presence'
}

class EtudiantPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.uid = tk.StringVar()
        self.nom = tk.StringVar()
        self.prenom = tk.StringVar()
        self.photo_path = ""
        self.matricule = tk.StringVar()

        # Interface graphique
        tk.Label(self, text="Nom", font=("Lato", 20, "bold")).place(x=450, y=35)
        tk.Entry(self, textvariable=self.nom, width=30).place(x=590, y=40, height=35)

        tk.Label(self, text="Prénom", font=("Lato", 20, "bold")).place(x=450, y=105)
        tk.Entry(self, textvariable=self.prenom, width=30).place(x=590, y=105, height=35)

        tk.Label(self, text="Matricule", font=("Lato", 20, "bold")).place(x=450, y=180)
        tk.Entry(self, textvariable=self.matricule, width=30).place(x=590, y=180, height=35)

        tk.Label(self, text="UID Carte", font=("Lato", 20, "bold")).place(x=450, y=240)
        tk.Label(self, textvariable=self.uid, fg="blue", font=("Lato", 20, "bold")).place(x=650, y=240)

        tk.Button(self, text="📷 Choisir une photo", command=self.choisir_photo, width=22, bg="blue", fg="white", font=("Lato", 15, "bold")).place(x=450, y=300)

        self.label_photo = tk.Label(self)
        self.label_photo.place(x=1000, y=210)

        tk.Button(self, text="✅ Enregistrer", command=self.enregistrer_etudiant, width=22, bg="blue", fg="white", font=("Lato", 15, "bold")).place(x=450, y=350)

        threading.Thread(target=self.lire_uid_en_temps_reel, daemon=True).start()

    def choisir_photo(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.png *.jpeg")])
        if path:
            image = Image.open(path)
            image.thumbnail((150, 150))
            photo = ImageTk.PhotoImage(image)
            self.label_photo.configure(image=photo)
            self.label_photo.image = photo
            self.photo_path = path  # temp, utilisé avant copie

    def enregistrer_etudiant(self):
        if not all([self.nom.get(), self.prenom.get(), self.matricule.get(), self.uid.get(), self.photo_path]):
            messagebox.showwarning("Champs manquants", "Veuillez remplir tous les champs.")
            return

        # Crée un dossier s’il n’existe pas
        os.makedirs("photos", exist_ok=True)
        photo_nom = os.path.basename(self.photo_path)
        destination = os.path.join("photos", photo_nom)

        try:
            shutil.copy(self.photo_path, destination)
        except Exception as e:
            messagebox.showerror("Erreur photo", f"Erreur de copie de la photo : {e}")
            return

        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO etudiants (uid, nom, prenom, matricule, photo_path) VALUES (%s, %s, %s, %s, %s)",
                (self.uid.get(), self.nom.get(), self.prenom.get(), self.matricule.get(), destination)
            )
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Succès", "Étudiant enregistré avec succès.")
            self.reset_formulaire()
        except mysql.connector.Error as err:
            messagebox.showerror("Erreur MySQL", f"{err}")

    def reset_formulaire(self):
        self.nom.set("")
        self.prenom.set("")
        self.uid.set("")
        self.label_photo.configure(image="")
        self.label_photo.image = None
        self.photo_path = ""
        self.matricule.set("")

    def lire_uid_en_temps_reel(self):
        try:
            arduino = serial.Serial(PORT_SERIE, BAUDRATE, timeout=1)
            time.sleep(2)
            while True:
                if arduino.in_waiting:
                    ligne = arduino.readline().decode('utf-8').strip()
                    if ligne.startswith("✅ UID détecté") and ":" in ligne:
                        uid_val = ligne.split(":")[1].strip()
                        self.uid.set(uid_val.upper())
        except serial.SerialException:
            print("Erreur de communication avec l'Arduino.")
        except Exception as e:
            print(f"Erreur inattendue : {e}")

# Test local
if __name__ == '__main__':
    root = tk.Tk()
    root.title("Inscription Étudiant")
    root.geometry("1300x600")  # tu peux ajuster
    app = EtudiantPage(root)
    app.pack(fill="both", expand=True)
    root.mainloop()
