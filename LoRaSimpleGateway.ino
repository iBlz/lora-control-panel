///                 Arduino      RFM95/96/97/98
///                 GND----------GND   (ground in)
///                 3V3----------3.3V  (3.3V in)
///             pin D4-----------RESET  (RESET)
/// interrupt 0 pin D2-----------DIO0  (interrupt request out)
///          SS pin D10----------NSS   (CS chip select in)
///         SCK pin D13----------SCK   (SPI clock in)
///        MOSI pin D11----------MOSI  (SPI Data in)
///        MISO pin D12----------MISO  (SPI Data out)

#define LORA
#include <SPI.h>
#include "LoRa-SOLDERED.h"
#include <ArduinoJson.h>

const int csPin = 10;
const int resetPin = 4;
const int irqPin = 2;

const long frequency = 868E6;

String request_ping = "{\"request\": \"ping\"}";
String send_string = "";

void setup()
{
  //--------------------------------------------------------------------
  Serial.begin(9600);
  while (!Serial);
  LoRa.setPins(csPin, resetPin, irqPin);
  if (!LoRa.begin(frequency))
  {
    Serial.println("[!] LoRa init failed. Check your connections.");
    while (true);                       // If failed, do nothing
  }
  //--------------------------------------------------------------------
  Serial.println("[*] LoRa Gateway ( Stationary )");
  Serial.println("[*] Only receive messages from nodes");
  Serial.println("[*] Tx: invertIQ enable");
  Serial.println("[*] Rx: invertIQ disable");
  Serial.println();
  //--------------------------------------------------------------------
  LoRa.onReceive(onReceive);
  LoRa.onTxDone(onTxDone);
  LoRa_rxMode();
}

void loop()
{
  long currentMillis = millis(); // Track time
  Serial.println("===============");
  delay(2000);
  send_string = request_ping;
  LoRa_sendMessage(send_string);
  Serial.println("[*] Sent ping request.");
  Serial.print("[*] Time running ( Minutes ) : ");
  Serial.println(currentMillis / 1000 / 60);
  search_for_commands();
  delay(100);
}

void search_for_commands()
{
  if (Serial.available()) // look for serial input
  {
    String read_serial = Serial.readString();
    if(read_serial.indexOf("fire") >= 0)
    {
      fire();
    }
    if(read_serial.indexOf("relay_on") >= 0)
    {
      relay_on();
    }
    if(read_serial.indexOf("relay_off") >= 0)
    {
      relay_off();
    }
  }
}

void fire()
{
  send_string = "{\"command\": \"fire\"}";
  LoRa_sendMessage(send_string);
  Serial.println("[*] Sent fire command.");
}

void relay_on()
{
  send_string = "{\"command\": \"relay_on\"}";
  LoRa_sendMessage(send_string);
  Serial.println("[*] Sent relay on command.");
}

void relay_off()
{
  send_string = "{\"command\": \"relay_off\"}";
  LoRa_sendMessage(send_string);
  Serial.println("[*] Sent relay off command.");
}

void LoRa_rxMode()
{
  Serial.println("[*] Rx mode started...");
  LoRa.disableInvertIQ();               // Normal mode
  LoRa.receive();                       // Set receive mode
}

void LoRa_txMode()
{
  Serial.println("[*] Tx mode started...");
  LoRa.idle();                          // Set standby mode
  LoRa.enableInvertIQ();                // Active invert I and Q signals
}

void LoRa_sendMessage(String send_string)
{
  LoRa_txMode();   //Set LoRa to transmitt mode                        // Set tx mode
  LoRa.beginPacket();                   // Start packet
  LoRa.print(send_string);                  // Add payload
  LoRa.endPacket(true);                 // Finish packet and send it
}

void search_for_ping(String message)
{
  String test_json = message + "}";
  StaticJsonDocument<128> doc;
  DeserializationError error = deserializeJson(doc, test_json);
  const char* response = doc["response"]; // "ok"
  JsonObject info = doc["info"];
  const char* info_rssi = info["rssi"]; // "-20"
  const char* info_packetSnr = info["packetSnr"]; // "8"
  const char* info_packetFrequencyError = info["packetFrequencyError"]; // "-300"
  String test_error = error.f_str();
  Serial.print("[*] Json status : ");
  Serial.println(test_error);
  if(test_error.indexOf("Ok") >= 0)
  {
    Serial.print("[*] Json ping : ");
    Serial.print(message);
    Serial.print(", \"gateway_info\" : {\"rssi\": \"" + String(LoRa.rssi()) + "");
    Serial.print("\", \"packetSnr\": \"" + String(LoRa.packetSnr()) + "");
    Serial.print("\",\"packetFrequencyError\": \"" + String(LoRa.packetFrequencyError()) + "\"}}\n");
  }
}

void search_for_lora_commands(String message)
{
  StaticJsonDocument<128> doc;
  DeserializationError error = deserializeJson(doc, message);
  const char* response = doc["command_status"]; // "fire"
  String test_error = error.f_str();
  Serial.print("[*] Json status : ");
  Serial.println(test_error);
  if(test_error.indexOf("Ok") >= 0)
  {
    Serial.print("[*] Json command : ");
    Serial.println(message);
    Serial.print("[*] Relay command sucessfull!\n");
  }
}

void onReceive(int packetSize, int currentMillis)	//Callback on receive data
{
  String message = "";
  while (LoRa.available())
  {
    message += (char)LoRa.read();
  }
  if(message.indexOf("response") >= 0)
  {
    Serial.println("[*] Gateway received packet");
    Serial.println("[*] Adding local info to json");
    search_for_ping(message);
  }
  if(message.indexOf("command_status") >= 0)
  {
    Serial.println("[*] Gateway received packet");
    search_for_lora_commands(message);
  }
}

void onTxDone()	//Callback on transmission done
{
  LoRa_rxMode();   //Set LoRa to receive mode 
}
