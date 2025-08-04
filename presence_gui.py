import serial
import mysql.connector
import time
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from datetime import datetime, date
import threading
import os

PORT_SERIE = '/dev/ttyACM0'
BAUDRATE = 9600

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'controle_presence'
}

class PresencePage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent

        conteneur_centre = tk.Frame(self)
        conteneur_centre.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Infos étudiant
        self.nom_label = tk.Label(conteneur_centre, text="Nom: ", font=("Arial", 14))
        self.nom_label.grid(row=0, column=0, sticky="w")

        self.prenom_label = tk.Label(conteneur_centre, text="Prénom: ", font=("Arial", 14))
        self.prenom_label.grid(row=1, column=0, sticky="w")

        self.matricule_label = tk.Label(conteneur_centre, text="Matricule: ", font=("Arial", 14))
        self.matricule_label.grid(row=2, column=0, sticky="w")

        self.heure_label = tk.Label(conteneur_centre, text="Heure: ", font=("Arial", 14))
        self.heure_label.grid(row=3, column=0, sticky="w")

        self.photo_label = tk.Label(conteneur_centre)
        self.photo_label.grid(row=0, column=1, rowspan=4, padx=10)

        self.status_label = tk.Label(conteneur_centre, text="🕓 En attente de carte RFID...", fg="blue", font=("Arial", 12))
        self.status_label.grid(row=4, column=0, columnspan=2, pady=10)

        # Tableau des présences
        self.tree = ttk.Treeview(conteneur_centre, columns=("uid", "nom", "prenom", "matricule", "entree", "sortie", "status"), show="headings", height=10)
        for col, text in [("uid", "UID"), ("nom", "Nom"), ("prenom", "Prénom"), ("matricule", "Matricule"), ("entree", "Entrée"), ("sortie", "Sortie"), ("status", "Status")]:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=120)

        self.tree.grid(row=5, column=0, columnspan=2, pady=10, padx=10, sticky="nsew")

        conteneur_centre.grid_columnconfigure(0, weight=1)
        conteneur_centre.grid_columnconfigure(1, weight=1)

        self.charger_presences_du_jour()

        threading.Thread(target=self.lire_uid_en_temps_reel, daemon=True).start()

    def charger_presences_du_jour(self):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            today = date.today().strftime('%Y-%m-%d')
            cursor.execute("""
                SELECT p.uid, e.nom, e.prenom, e.matricule, p.entree, p.sortie, p.status
                FROM presences p 
                JOIN etudiants e ON e.uid = p.uid
                WHERE DATE(p.entree) = %s
                ORDER BY p.entree DESC
            """, (today,))
            rows = cursor.fetchall()
            conn.close()

            self.tree.delete(*self.tree.get_children())
            for uid, nom, prenom, matricule, entree, sortie, status in rows:
                entree_str = entree.strftime('%H:%M:%S') if entree else ""
                sortie_str = sortie.strftime('%H:%M:%S') if sortie else ""
                self.tree.insert("", "end", values=(uid, nom, prenom, matricule, entree_str, sortie_str, status))
        except mysql.connector.Error as err:
            self.status_label.config(text=f"Erreur MySQL : {err}", fg="red")

    def afficher_infos_etudiant(self, nom, prenom, matricule, photo_path):
        self.nom_label.config(text=f"Nom: {nom}")
        self.prenom_label.config(text=f"Prénom: {prenom}")
        self.matricule_label.config(text=f"Matricule: {matricule}")
        self.heure_label.config(text=f"Heure: {datetime.now().strftime('%H:%M:%S')}")
        self.status_label.config(text="✅ Présence enregistrée", fg="green")

        if photo_path and os.path.exists(photo_path):
            try:
                image = Image.open(photo_path)
                image.thumbnail((120, 120))
                photo = ImageTk.PhotoImage(image)
                self.photo_label.config(image=photo)
                self.photo_label.image = photo
            except:
                self.photo_label.config(image="", text="📷 Erreur chargement photo")
        else:
            self.photo_label.config(image="", text="📷 Aucune photo")

    def enregistrer_presence(self, uid):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()

            cursor.execute("SELECT nom, prenom, matricule, photo_path FROM etudiants WHERE uid = %s", (uid,))
            result = cursor.fetchone()

            if not result:
                self.status_label.config(text=f"❌ UID inconnu : {uid}", fg="red")
                self.nom_label.config(text="Nom: ")
                self.prenom_label.config(text="Prénom: ")
                self.matricule_label.config(text="Matricule: ")
                self.heure_label.config(text="Heure: ")
                self.photo_label.config(image="")
                return

            nom, prenom, matricule, photo_path = result
            now = datetime.now()

            cursor.execute("""
                SELECT id, entree, sortie FROM presences 
                WHERE uid = %s AND DATE(entree) = CURDATE()
            """, (uid,))
            presence = cursor.fetchone()

            if presence:
                id_presence, entree, sortie = presence
                if not sortie:
                    if (now - entree).total_seconds() >= 120:  # 20 minutes
                        cursor.execute("UPDATE presences SET sortie = %s, status = %s WHERE id = %s",
                                       (now, "Présence terminée", id_presence))
                        conn.commit()
                        self.status_label.config(text="✅ Sortie enregistrée", fg="orange")
                    else:
                        self.status_label.config(text="⏱️ Attendez au moins 20 min avant de ressortir", fg="gray")
                else:
                    self.status_label.config(text="📌 Présence déjà complète aujourd'hui", fg="blue")
            else:
                cursor.execute("INSERT INTO presences (uid, entree, status) VALUES (%s, %s, %s)",
                               (uid, now, "Présent"))
                conn.commit()
                self.status_label.config(text="✅ Entrée enregistrée", fg="green")

            self.afficher_infos_etudiant(nom, prenom, matricule, photo_path)
            self.charger_presences_du_jour()
            conn.close()

        except mysql.connector.Error as err:
            self.status_label.config(text=f"Erreur MySQL : {err}", fg="red")

    def lire_uid_en_temps_reel(self):
        try:
            arduino = serial.Serial(PORT_SERIE, BAUDRATE, timeout=1)
            time.sleep(2)
            while True:
                if arduino.in_waiting:
                    ligne = arduino.readline().decode('utf-8').strip()
                    if ligne.startswith("✅ UID détecté") and ":" in ligne:
                        uid = ligne.split(":")[1].strip().upper()
                        self.after(0, lambda: self.enregistrer_presence(uid))
        except serial.SerialException:
            self.after(0, lambda: self.status_label.config(
                text="❌ Problème de communication avec l'Arduino", fg="red"))

if __name__ == '__main__':
    root = tk.Tk()
    root.title("Système de Pointage - Présence")
    root.geometry("1000x600")
    app = PresencePage(root)
    app.pack(fill="both", expand=True)
    root.mainloop()
