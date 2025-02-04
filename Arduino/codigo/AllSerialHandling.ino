//////////
/////////  All Serial Handling Code
/////////

void serialOutput(){  
  for (int i = 0; i < 8; i++) { 
    switch(outputType){
      case PROCESSING_VISUALIZER:
        sendDataToSerial('S', Signal[i]);     
        break;
      case SERIAL_PLOTTER:  
        Serial.print("Pessoa ");
        Serial.print(i + 1);
        Serial.print(" - BPM: ");
        Serial.print(BPM[i]);
        Serial.print(", GSR: ");
        Serial.println(analogRead(gsrPins[i])); // Leitura direta do GSR
        break;
      default:
        break;
    }
  }
}

//  Decides How To Output BPM and IBI Data
void serialOutputWhenBeatHappens(){
  for (int i = 0; i < 8; i++) {  
    switch(outputType){
      case PROCESSING_VISUALIZER:    
        sendDataToSerial('B', BPM[i]);  
        sendDataToSerial('Q', IBI[i]);  
        break;
      default:
        break;
    }
  }
}

//  Sends Data to Pulse Sensor Processing App
void sendDataToSerial(char symbol, int data ){
    Serial.print(symbol);
    Serial.println(data);
}
