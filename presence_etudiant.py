import serial
import mysql.connector
import time
from datetime import datetime

# ------------------- Configuration -------------------
PORT_SERIE = '/dev/ttyACM0' # ⚠️ Sous Windows : 'COM3' par exemple
BAUDRATE = 9600

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'controle_presence'
}
# ------------------------------------------------------



def enregistrer_presence(uid):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Vérifie si l'étudiant existe
        cursor.execute("SELECT nom, prenom FROM etudiants WHERE uid = %s", (uid,))
        result = cursor.fetchone()

        if result:
            nom, prenom = result
            cursor.execute("INSERT INTO presences (uid) VALUES (%s)", (uid,))
            conn.commit()
            print(f"✅ Présence enregistrée pour {prenom} {nom} à {datetime.now().strftime('%H:%M:%S')}")
        else:
            print(f"❌ UID inconnu : {uid}")

        conn.close()

    except mysql.connector.Error as err:
        print(f"Erreur MySQL : {err}")

def ecouter_rfid():
    try:
        arduino = serial.Serial(PORT_SERIE, BAUDRATE, timeout=1)
        print("🟢 En attente de cartes RFID...")

        time.sleep(2)  # Temps pour stabiliser le port série

        while True:
            if arduino.in_waiting:
                ligne = arduino.readline().decode('utf-8').strip()
                if ligne.startswith("✅ UID détecté"):
                    uid = ligne.split(":")[1].strip().upper()
                    enregistrer_presence(uid)

    except serial.SerialException:
        print("❌ Erreur de communication avec l'Arduino.")

if __name__ == '__main__':
    ecouter_rfid()
