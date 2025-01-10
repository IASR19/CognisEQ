# NeuroEQ - Monitoramento Emocional em Tempo Real

NeuroEQ é uma aplicação de monitoramento emocional em tempo real, projetada para capturar e exibir os estados emocionais de várias pessoas simultaneamente. Usando sensores de frequência cardíaca (BPM) e condutância da pele (GSR), a aplicação classifica emoções e exibe gráficos em tempo real, ideal para estudos em ambientes de marketing ou experimentos de psicologia.

## Funcionalidades

- **Monitoramento em Tempo Real**: Coleta dados de BPM e GSR de até 8 pessoas e exibe os resultados ao vivo.
- **Classificação de Emoções**: Usa um modelo de Machine Learning (KNN) para classificar emoções como `Alegria`, `Calma`, `Medo` e `Tristeza`.
- **Cálculo de Índices Emocionais**:
  - `EI (Emotional Index)`: Índice que representa o estado emocional detectado.
- **Exportação de Dados**: Exporta os dados coletados para um arquivo CSV para análise posterior.

## Requisitos

- **Python 3.x**
- **Bibliotecas Python**:
  - `pandas`
  - `serial`
  - `PyQt5`
  - `joblib`
  - `sklearn`
  - `numpy`
  - `matplotlib`
  - `opencv`

## Como Usar

1. **Configuração Inicial**:
   - Conecte os sensores de BPM e GSR às portas seriais do sistema.
   - Inicie a aplicação executando:

```bash
python3 -m venv venv # Criar ambiente virtual
source venv/bin/activate  # No Windows use `venv\Scripts\activate`
pip install -r requirements.txt # Baixar dependencias
python3 arquivo_nome.py
```

2. **Selecione o Número de Pessoas**:
   - Escolha o número de pessoas a serem monitoradas (de 1 a 8).
   - Clique em "Avançar" para iniciar a tela de monitoramento.

3. **Selecione a Porta Serial e Inicie a Coleta**:
   - Escolha a porta serial ativa para a comunicação com os sensores.
   - Clique em "Iniciar Coleta e Previsões" para começar a análise em tempo real.

4. **Visualize os Gráficos**:
   - Para cada pessoa monitorada, um gráfico exibe o valor de GSR e o coeficiente emocional calculado.

5. **Exportação dos Dados**:
   - Após clicar em "Parar Coleta", o botão "Exportar CSV" estará disponível.
   - Clique em "Exportar CSV" para salvar os dados coletados para cada pessoa em um arquivo CSV.

## Estrutura do Projeto

- `RealTimeEmotionThread`: Coleta os dados dos sensores e os processa.
- `InitialSelectionWidget`: Tela inicial para selecionar o número de pessoas monitoradas.
- `RealTimeEmotionWidget`: Tela de monitoramento que exibe os gráficos e índices emocionais.
- `MainApp`: Classe principal que gerencia a navegação entre as telas e o monitoramento em tela cheia.

## Lógica de Classificação e Índices

- **Modelo KNN**: Um modelo K-Nearest Neighbors (KNN) treinado com um dataset (`dados_base.csv`) classifica os estados emocionais.
- **Índice Emocional (EI)**: Calculado com base nos valores normalizados de BPM e GSR.
- **Índice de Excitação/Atenção (AW)**: Calculado com base em uma combinação ponderada de BPM e GSR.

## Formato do CSV Exportado

O arquivo CSV exportado após a coleta contém os seguintes campos para cada pessoa monitorada:
- `BPM`: Batimentos por minuto.
- `GSR`: Condutância da pele.
- `EI`: Índice emocional.

Cada linha do CSV corresponde a uma amostra de leitura, permitindo uma análise detalhada dos dados de cada pessoa ao longo do tempo.

## Licença
Este projeto está sob a licença GNU. Consulte o arquivo `LICENSE` para mais detalhes.
