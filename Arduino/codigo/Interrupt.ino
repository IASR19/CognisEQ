// Interrupção configurada para múltiplos sensores

volatile int rate[8][10];          // Cada sensor terá um histórico de 10 valores de IBI
volatile unsigned long sampleCounter[8] = {0};  
volatile unsigned long lastBeatTime[8] = {0};   
volatile int P[8] = {512};          
volatile int T[8] = {512};          
volatile int thresh[8] = {530};     
volatile int amp[8] = {0};          
volatile boolean firstBeat[8] = {true};   
volatile boolean secondBeat[8] = {false};  

void interruptSetup(){  
  // Configuração do Timer 2 para interrupção a cada 2ms
  TCCR2A = 0x02;     
  TCCR2B = 0x06;     
  OCR2A = 0X7C;      
  TIMSK2 = 0x02;     
  sei();             
}

ISR(TIMER2_COMPA_vect){                         
  cli();                                      // Desativa interrupções

  for (int i = 0; i < 8; i++) {               
    if (!activeChannels[i]) { 
      continue; // Pula sensores inativos
    }

    Signal[i] = analogRead(pulsePins[i]);              
    sampleCounter[i] += 2;                        
    int N = sampleCounter[i] - lastBeatTime[i];  

    // Encontra pico e vale
    if (Signal[i] < thresh[i] && N > (IBI[i] / 5) * 3) {       
      if (Signal[i] < T[i]) {                        
        T[i] = Signal[i];                         
      }
    }

    if (Signal[i] > thresh[i] && Signal[i] > P[i]) {          
      P[i] = Signal[i];                            
    }                                        

    // Verifica se há um batimento
    if (N > 250) {                                   
      if ((Signal[i] > thresh[i]) && (!Pulse[i]) && (N > (IBI[i] / 5) * 3)) {
        Pulse[i] = true;                               
        digitalWrite(blinkPin, HIGH);                
        IBI[i] = sampleCounter[i] - lastBeatTime[i];         
        lastBeatTime[i] = sampleCounter[i];               

        if (secondBeat[i]) {                        
          secondBeat[i] = false;                  
          for (int j = 0; j <= 9; j++) {             
            rate[i][j] = IBI[i];
          }
        }

        if (firstBeat[i]) {                         
          firstBeat[i] = false;                   
          secondBeat[i] = true;                   
          sei();                               
          return;                              
        }

        // Média dos últimos 10 valores de IBI
        word runningTotal = 0;                  
        for (int j = 0; j <= 8; j++) {                
          rate[i][j] = rate[i][j + 1];                 
          runningTotal += rate[i][j];              
        }

        rate[i][9] = IBI[i];                         
        runningTotal += rate[i][9];                
        runningTotal /= 10;                     
        BPM[i] = 60000 / runningTotal;              
        QS[i] = true;                             
      }
    }

    if (Signal[i] < thresh[i] && Pulse[i]) {   
      digitalWrite(blinkPin, LOW);            
      Pulse[i] = false;                         
      amp[i] = P[i] - T[i];                           
      thresh[i] = amp[i] / 2 + T[i];                    
      P[i] = thresh[i];                            
      T[i] = thresh[i];
    }

    if (N > 2500) {                          
      thresh[i] = 530;                         
      P[i] = 512;                               
      T[i] = 512;                               
      lastBeatTime[i] = sampleCounter[i];          
      firstBeat[i] = true;                      
      secondBeat[i] = false;                    
    }
  }

  sei();                                   
}
