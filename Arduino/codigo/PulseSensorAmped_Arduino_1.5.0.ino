/*  Pulse Sensor Amped 1.5 - Adaptado para 8 sensores de pulso e 8 sensores GSR */
/*  Agora isolando os canais ativos e imprimindo 0 para os inativos */

#define PROCESSING_VISUALIZER 1
#define SERIAL_PLOTTER 2

// Definição de pinos para 8 sensores de pulso e 8 sensores GSR
const int pulsePins[8] = {A2, A3};  
const int gsrPins[8] = {A0, A1};    

// Variáveis dos sensores de pulso
int blinkPin = 13;                
int fadePin = 5;                  
int fadeRate = 0;                 

// Variáveis globais para armazenar dados dos 8 sensores
volatile int BPM[8] = {0};         
volatile int Signal[8] = {0};      
volatile int IBI[8] = {600};       
volatile boolean Pulse[8] = {false};
volatile boolean QS[8] = {false}; 

// Flag para canais ativos (ajuste para ativar/desativar canais)
bool activeChannels[8] = {true, true, false, false, false, false, false, false};  

// Configuração da saída no Serial
static int outputType = SERIAL_PLOTTER;

void setup(){
  pinMode(blinkPin, OUTPUT);         
  pinMode(fadePin, OUTPUT);          
  Serial.begin(115200);             
  interruptSetup();                 // Configura a interrupção para o Pulse Sensor

  Serial.println("Monitoramento de 8 pessoas iniciado!");
}

void loop(){
  for (int i = 0; i < 8; i++) {
    if (activeChannels[i]) {
      // Leitura do sensor de pulso
      Signal[i] = analogRead(pulsePins[i]);  

      // Se detectar um batimento, calcula BPM
      if (Signal[i] > 550 && millis() - IBI[i] > 300) { 
        long delta = millis() - IBI[i];
        IBI[i] = millis();
        BPM[i] = 60000 / delta;
        BPM[i] = constrain(BPM[i], 20, 255);  
        Pulse[i] = true;
        QS[i] = true;
      }

      // Leitura do sensor GSR
      double gsrValue = (1000*3.0/analogRead(gsrPins[i]));

      // Exibir BPM e GSR no Serial
      Serial.print("Pessoa ");
      Serial.print(i + 1);
      Serial.print(" - BPM: ");
      Serial.print(BPM[i]);
      Serial.print(", GSR: ");
      Serial.println(gsrValue, 4);
    } else {
      // Se o canal não estiver ativo, exibe valores zerados
      Serial.print("Pessoa ");
      Serial.print(i + 1);
      Serial.print(" - BPM: 0, GSR: 0\n");
    }
  }

  ledFadeToBeat();  // Aplica o efeito de fade no LED
  delay(20);
}

// Função para fazer fade no LED
void ledFadeToBeat(){
  fadeRate -= 15;                         
  fadeRate = constrain(fadeRate, 0, 255);   
  analogWrite(fadePin, fadeRate);          
}
