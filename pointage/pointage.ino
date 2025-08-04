#include <SPI.h>
#include <MFRC522.h>

// Broches du module RC522 sur Arduino UNO
#define SS_PIN 10  // SDA du module RFID
#define RST_PIN 9  // RST du module RFID

MFRC522 rfid(SS_PIN, RST_PIN); // Crée un objet RFID

void setup() {
  Serial.begin(9600);
  while (!Serial); // Attente si nécessaire

  SPI.begin();       // Initialiser le bus SPI
  rfid.PCD_Init();   // Initialiser le module RC522
  Serial.println("📡 Scanner une carte RFID...");
}

void loop() {
  // Attendre qu'une carte soit présente
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
    return;
  }

  Serial.print("✅ UID détecté : ");
  for (byte i = 0; i < rfid.uid.size; i++) {
    Serial.print(rfid.uid.uidByte[i] < 0x10 ? "0" : "");
    Serial.print(rfid.uid.uidByte[i], HEX);
    Serial.print(i < rfid.uid.size - 1 ? ":" : "");
  }
  Serial.println();

  delay(1000); // Petite pause avant prochaine lecture
}
