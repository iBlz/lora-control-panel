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

const long frequency = 868E6;

const int csPin = 10;
const int resetPin = 4;
const int irqPin = 2;
const int relay = 3;

void setup()
{
  Serial.begin(9600);
  while (!Serial);
  LoRa.setPins(csPin, resetPin, irqPin);
  if (!LoRa.begin(frequency))
  {
    Serial.println("[!] LoRa init failed. Check your connections.");
    while (true);
  }
  Serial.println("[*] LoRa Node ( Not stationary )");
  Serial.println("[*] Only receive messages from gateways");
  Serial.println("[*] Tx: invertIQ disable");
  Serial.println("[*] Rx: invertIQ enable");
  Serial.println();
  //-----------------------------
  LoRa.onReceive(onReceive);
  LoRa.onTxDone(onTxDone);
  LoRa_rxMode();
  pinMode(relay, OUTPUT);
}

void fire()
{
  digitalWrite(relay, LOW);
  delay(50000); // ????????????????????
  digitalWrite(relay, HIGH);
  delay(50000); // ????????????????
}

void relay_on()
{
  digitalWrite(relay, HIGH);
}

void relay_off()
{
  digitalWrite(relay, LOW);
}

void LoRa_rxMode()
{
  Serial.println("[*] Rx mode started...");
  LoRa.enableInvertIQ();                // Active invert I and Q signals
  LoRa.receive();                       // Set receive mode
}

void LoRa_txMode()
{
  Serial.println("[*] Tx mode started...");
  LoRa.idle();                          // Set standby mode
  LoRa.disableInvertIQ();               // Normal mode
}

void LoRa_sendMessage(String message)
{
  LoRa_txMode();   //Set LoRa to transmitt mode                        // Set tx mode
  LoRa.beginPacket();                   // Start packet
  LoRa.print(message);                  // Add payload
  LoRa.endPacket(true);                 // Finish packet and send it
}

void onReceive(int packetSize) 	//Callback on receive data
{
  //-----------------------------
  String message = "";
  while (LoRa.available())  //Read from incoming buffer
  {
    message += (char)LoRa.read();
  }
  Serial.println("-----------------------------");
  Serial.print("Node Receive: ");
  Serial.println(message);
  //-----------------------------
  if(message.indexOf("{\"request\": \"ping\"}") >= 0)
  {
    String inforesponse = "{\"response\": \"ok\", \"node_info\": {\"rssi\": \"";
    inforesponse = inforesponse + LoRa.rssi();
    inforesponse = inforesponse + "\", \"packetSnr\": \"";
    inforesponse = inforesponse + LoRa.packetSnr();
    inforesponse = inforesponse + "\",\"packetFrequencyError\": \"";
    inforesponse = inforesponse + LoRa.packetFrequencyError();
    inforesponse = inforesponse + "\"}";
    Serial.println(inforesponse);
    LoRa_sendMessage(inforesponse);
  }
  if(message.indexOf("{\"command\": \"fire\"}") >= 0)
  {
    String inforesponse = "{\"command_status\": \"fired\"}";
    fire();
    LoRa_sendMessage(inforesponse);
  }
  if(message.indexOf("{\"command\": \"relay_on\"}") >= 0)
  {
    String inforesponse = "{\"command_status\": \"relay_turned_on\"}";
    relay_on();
    LoRa_sendMessage(inforesponse);
  }
  if(message.indexOf("{\"command\": \"relay_off\"}") >= 0)
  {
    String inforesponse = "{\"command_status\": \"relay_turned_off\"}";
    relay_off();
    LoRa_sendMessage(inforesponse);
  }
  //-----------------------------
}

void onTxDone() //Callback on transmission done
{
  LoRa_rxMode();   //Set LoRa to receive mode
}

