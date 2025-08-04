#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN 10     // Pin SDA du module RFID
#define RST_PIN 9     // Pin RST du module RFID
MFRC522 rfid(SS_PIN, RST_PIN);

// LED
#define LED_VERTE 6
#define LED_ROUGE 7

// UIDs autorisés (à écrire en MAJUSCULES sans espace)
String uids_autorises[] = {
  "63F5F3E3" ,"C3E932A8"
 // Ta carte
};

// Initialisation
void setup() {
  Serial.begin(9600);  // Communication avec le PC
  SPI.begin();         // Initialisation SPI
  rfid.PCD_Init();     // Initialisation du module RFID

  pinMode(LED_VERTE, OUTPUT);
  pinMode(LED_ROUGE, OUTPUT);

  digitalWrite(LED_VERTE, LOW);
  digitalWrite(LED_ROUGE, LOW);

  Serial.println("🎯 Système de pointage prêt. Approchez une carte...");
}

// Boucle principale
void loop() {
  // Attendre une carte
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
    return;
  }

  // Lire l’UID
  String uid = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10) uid += "0";  // Ajouter un 0 si nécessaire
    uid += String(rfid.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();  // Convertir en majuscules

  Serial.print("✅ UID détecté : ");
  Serial.println(uid);

  // Vérification d’autorisation
  if (estAutorise(uid)) {
    Serial.println("🟢 Accès autorisé !");
    digitalWrite(LED_VERTE, HIGH);
    digitalWrite(LED_ROUGE, LOW);
  } else {
    Serial.println("🔴 Accès refusé !");
    digitalWrite(LED_VERTE, LOW);
    digitalWrite(LED_ROUGE, HIGH);
  }

  // Attente avant de réinitialiser les LEDs
  delay(1500);
  digitalWrite(LED_VERTE, LOW);
  digitalWrite(LED_ROUGE, LOW);

  // Arrêt de la communication avec la carte
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
}

// Vérifie si l’UID est autorisé
bool estAutorise(String uid) {
  for (String autorise : uids_autorises) {
    if (uid == autorise) return true;
  }
  return false;
}