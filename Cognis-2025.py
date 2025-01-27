from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QStackedWidget, QPushButton, QTextEdit, QProgressBar, QScrollArea, QFrame, QHBoxLayout, QLineEdit, QSpinBox, QComboBox, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtGui import QPixmap
import random  # For simulated score values
import os  # Necessário para manipular diretórios e caminhos
import csv  # Necessário para salvar arquivos CSV
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import QUrl
import serial.tools.list_ports
from serial.tools import list_ports
from datetime import datetime



class TrainingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.initUI()
        print(f"Conexão serial no treinamento: {self.serial_connection}")


    def initUI(self):
        layout = QVBoxLayout()

        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0,   43)
        layout.addWidget(QLabel("Treinamento em andamento..."))
        layout.addWidget(self.progress_bar)

        # Exibição de valores dos sensores
        self.sensor_values_label = QLabel("Valores dos Sensores:")
        layout.addWidget(self.sensor_values_label)

        # Campo para GSR e BPM
        self.gsr_label = QLabel("GSR: -")  # Inicializa o gsr_label
        self.bpm_label = QLabel("BPM: -")  # Inicializa o bpm_label
        layout.addWidget(self.gsr_label)
        layout.addWidget(self.bpm_label)

        # Exibição do sentimento associado
        self.sentiment_label = QLabel("Sentimento Atual: -")
        layout.addWidget(self.sentiment_label)

        # Botão para avançar manualmente
        self.skip_button = QPushButton("Avançar para Coleta Real")
        self.skip_button.clicked.connect(self.skip_training)
        layout.addWidget(self.skip_button)

        self.setLayout(layout)

        # Timer para a barra de progresso
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(1000)
        print("Timer de coleta real iniciado.")




    def start_training(self):
        training_video_path = "/home/igsr/Área de trabalho/NencTech/NeuroEQ/treinamento/treinamento.mp4"

        if not os.path.exists(training_video_path):
            QMessageBox.critical(self, "Erro", "Arquivo de treinamento não encontrado!")
            return
    
        # Configura o vídeo de treinamento
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(training_video_path)))
        self.media_player.play()

        self.status_label.setText("Treinamento em andamento...")

        # Timer para encerrar treinamento
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.end_training)
        self.timer.start(43000)  # 43 segundos

    def end_training(self):
        self.media_player.stop()
        self.timer.stop()

        QMessageBox.information(self, "Treinamento Concluído", "Treinamento finalizado!")

        # Transição para a coleta real
        self.parent.start_main_window(self.parent.training_params)



class SetupWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.dynamic_name_fields = []
        self.incentive_file = None
        self.collection_mode = None
        self.collection_time = None
        self.initUI()

    def refresh_ports(self):
        self.port_combo.clear()
        ports = list_ports.comports()
        for port in ports:
            self.port_combo.addItem(port.device)



    def initUI(self):
        layout = QVBoxLayout()

        # Número de Participantes
        self.num_people_label = QLabel("Número de Participantes:")
        self.num_people_spinbox = QSpinBox()
        self.num_people_spinbox.setRange(1, 8)
        self.num_people_spinbox.valueChanged.connect(self.update_name_fields)
        layout.addWidget(self.num_people_label)
        layout.addWidget(self.num_people_spinbox)

        # Nome dos Participantes
        self.name_fields_layout = QVBoxLayout()
        layout.addLayout(self.name_fields_layout)
        self.update_name_fields()

        # Seleção de Porta Serial
        self.port_label = QLabel("Selecionar Porta Serial:")
        self.port_combo = QComboBox()
        self.refresh_ports()  # Popula o combobox com as portas disponíveis
        layout.addWidget(self.port_label)
        layout.addWidget(self.port_combo)

        # Botão para atualizar portas
        self.refresh_button = QPushButton("Atualizar Portas")
        self.refresh_button.clicked.connect(self.refresh_ports)
        layout.addWidget(self.refresh_button)

        # Arquivo de Incentivo
        self.incentive_label = QLabel("Arquivo de Incentivo:")
        self.file_button = QPushButton("Selecionar Arquivo")
        self.file_button.clicked.connect(self.open_file_dialog)
        layout.addWidget(self.incentive_label)
        layout.addWidget(self.file_button)

        # Modo de Coleta
        self.mode_label = QLabel("Modo de Coleta:")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Livre", "Tempo Fixo"])
        self.mode_combo.currentIndexChanged.connect(self.toggle_time_input)
        layout.addWidget(self.mode_label)
        layout.addWidget(self.mode_combo)

        # Tempo de Coleta
        self.time_label = QLabel("Tempo de Coleta (segundos):")
        self.time_input = QLineEdit()
        self.time_input.setPlaceholderText("Digite o tempo em segundos")
        self.time_label.hide()
        self.time_input.hide()
        layout.addWidget(self.time_label)
        layout.addWidget(self.time_input)

        # Botão Iniciar
        self.start_button = QPushButton("Iniciar")
        self.start_button.clicked.connect(self.start)
        layout.addWidget(self.start_button)

        self.setLayout(layout)
        self.apply_styles()

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial, sans-serif;
            }
            QLabel {
                font-size: 14px;
                color: #333;
            }
            QLineEdit, QSpinBox, QComboBox {
                padding: 5px;
                font-size: 14px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)

    def update_name_fields(self):
        for field in self.dynamic_name_fields:
            field.deleteLater()
        self.dynamic_name_fields.clear()
        for i in range(self.num_people_spinbox.value()):
            name_field = QLineEdit()
            name_field.setPlaceholderText(f"Nome do Participante {i + 1}")
            self.dynamic_name_fields.append(name_field)
            self.name_fields_layout.addWidget(name_field)

    def toggle_time_input(self):
        if self.mode_combo.currentText() == "Tempo Fixo":
            self.time_label.show()
            self.time_input.show()
        else:
            self.time_label.hide()
            self.time_input.hide()

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Arquivo de Incentivo", "", "Imagens e Vídeos (*.png *.jpg *.mp4)")
        if file_path:
            self.incentive_file = file_path
            QMessageBox.information(self, "Arquivo Selecionado", f"{file_path}")

    def start(self):
        participant_names = [field.text() for field in self.dynamic_name_fields]
        num_people = self.num_people_spinbox.value()
        self.collection_mode = self.mode_combo.currentText()
        self.collection_time = self.time_input.text() if self.collection_mode == "Tempo Fixo" else None
        self.selected_port = self.port_combo.currentText()  # Porta serial selecionada

        if not self.incentive_file or not all(participant_names):
            QMessageBox.critical(self, "Erro", "Preencha todos os campos e selecione o incentivo.")
            return
        if self.collection_mode == "Tempo Fixo" and (not self.collection_time or not self.collection_time.isdigit()):
            QMessageBox.critical(self, "Erro", "Digite um tempo válido para coleta em segundos.")
            return
        if not self.selected_port:
            QMessageBox.critical(self, "Erro", "Selecione uma porta serial.")
            return

        # Passa para o MainApp
        self.parent.start_training_screen(
            num_people,
            participant_names,
            self.collection_mode,
            int(self.collection_time) if self.collection_time else None,
            self.selected_port  # Porta serial selecionada
        )



import subprocess  # Para abrir o vídeo no reprodutor padrão

class TrainingWidget(QWidget):
    def __init__(self, parent, num_people, names, mode, collection_time, serial_port):
        super().__init__(parent)
        self.parent = parent
        self.num_people = num_people
        self.names = names
        self.mode = mode
        self.collection_time = collection_time
        self.serial_port = serial_port
        self.elapsed_time = 0
        self.training_data = {
            "Alegria": {"GSR": [], "BPM": []},
            "Tristeza": {"GSR": [], "BPM": []},
            "Neutro": {"GSR": [], "BPM": []},
            "Terror": {"GSR": [], "BPM": []}
        }
        self.serial_connection = None  # Inicializa a conexão serial
        self.initUI()
        self.connect_to_serial()
        self.start_video()

    def connect_to_serial(self):
        try:
            self.serial_connection = serial.Serial(self.serial_port, 115200, timeout=1)
            QMessageBox.information(self, "Conexão Serial", f"Conectado à porta {self.serial_port}")
        except Exception as e:
            QMessageBox.critical(self, "Erro de Conexão", f"Não foi possível conectar à porta {self.serial_port}.\nErro: {e}")
            self.skip_training()

    def initUI(self):
        layout = QVBoxLayout()

        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 43)
        layout.addWidget(QLabel("Treinamento em andamento..."))
        layout.addWidget(self.progress_bar)

        # Exibição de valores dos sensores
        self.sensor_values_label = QLabel("Valores dos Sensores:")
        layout.addWidget(self.sensor_values_label)

        # Campo para GSR e BPM
        self.gsr_label = QLabel("GSR: -")
        self.bpm_label = QLabel("BPM: -")
        layout.addWidget(self.gsr_label)
        layout.addWidget(self.bpm_label)

        # Exibição do sentimento associado
        self.sentiment_label = QLabel("Sentimento Atual: -")
        layout.addWidget(self.sentiment_label)

        # Botão para avançar manualmente
        self.skip_button = QPushButton("Avançar para Coleta Real")
        self.skip_button.clicked.connect(self.skip_training)
        layout.addWidget(self.skip_button)

        self.setLayout(layout)

        # Timer para a barra de progresso
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(1000)
        print("Timer de coleta real iniciado.")


    def start_video(self):
        video_path = "treinamento/treinamento.mp4"
        if not os.path.exists(video_path):
            QMessageBox.critical(self, "Erro", "Vídeo de treinamento não encontrado.")
            self.skip_training()
            return

        try:
            subprocess.Popen(["xdg-open", video_path])  # Linux
        except FileNotFoundError:
            try:
                subprocess.Popen(["open", video_path])  # macOS
            except FileNotFoundError:
                try:
                    subprocess.Popen(["start", video_path], shell=True)  # Windows
                except Exception as e:
                    QMessageBox.critical(self, "Erro", f"Não foi possível abrir o vídeo: {e}")
                    self.skip_training()

    def update_progress(self):
        self.elapsed_time += 1
        self.progress_bar.setValue(self.elapsed_time)

        if self.serial_connection and self.serial_connection.in_waiting > 0:
            try:
                data = self.serial_connection.readline().decode('utf-8').strip()
                # Exemplo de dado: "Pessoa 1 - BPM: 75, GSR: 500"
                if data.startswith("Pessoa"):
                    parts = data.split("-")
                    person_id = int(parts[0].split()[1]) - 1  # Obtém o índice (ex.: 1 para "Pessoa 1")
                    bpm = float(parts[1].split(":")[1].strip().split(",")[0])
                    gsr = int(parts[1].split(":")[2].strip())

                    # Substituir "Pessoa X" pelo nome real do participante
                    participant_name = self.names[person_id] if person_id < len(self.names) else f"Pessoa {person_id + 1}"

                    self.gsr_label.setText(f"GSR: {gsr} ({participant_name})")
                    self.bpm_label.setText(f"BPM: {bpm} ({participant_name})")

                    # Determinar o sentimento
                    if self.elapsed_time <= 10:
                        sentimento = "Alegria"
                    elif self.elapsed_time <= 20:
                        sentimento = "Tristeza"
                    elif self.elapsed_time <= 30:
                        sentimento = "Neutro"
                    else:
                        sentimento = "Terror"

                    self.sentiment_label.setText(f"Sentimento Atual: {sentimento}")
                    self.training_data[sentimento]["GSR"].append(gsr)
                    self.training_data[sentimento]["BPM"].append(bpm)

            except Exception as e:
                print(f"Erro ao ler dados da serial: {e}")

        if self.elapsed_time >= 43:
            self.timer.stop()
            self.complete_training()


    def skip_training(self):
        self.timer.stop()
        self.complete_training()

    def complete_training(self):
        # Não feche a conexão serial aqui
        self.parent.training_data = self.training_data
        self.parent.start_main_window(
            self.num_people, self.names, self.mode, self.collection_time, self.serial_connection
        )






import serial  # Para comunicação serial

class RealTimeEmotionWidget(QWidget):
    def __init__(self, num_people, names, incentive_file, mode, collection_time, serial_connection, training_data):
        super().__init__()
        self.num_people = num_people
        self.names = names
        self.incentive_file = incentive_file
        self.mode = mode
        self.collection_time = collection_time
        self.serial_connection = serial_connection
        self.training_data = training_data  # Salva os dados de treinamento
        print(f"Conexão serial na coleta real: {self.serial_connection}")


        if not self.serial_connection or not self.serial_connection.is_open:
            print("Erro: Conexão serial não está aberta.")

        self.scores = {name: [] for name in self.names}
        self.gsr_ecg_values = []
        self.sentiment_counts = {name: {"Alegria": 0, "Tristeza": 0, "Neutro": 0, "Terror": 0} for name in self.names}
        self.consolidated_sentiments = {"Alegria": 0, "Tristeza": 0, "Neutro": 0, "Terror": 0}



        self.initUI()




    def initUI(self):
        main_layout = QVBoxLayout()

        # Incentivo Centralizado
        incentive_layout = QHBoxLayout()
        if self.incentive_file.endswith(('.png', '.jpg', '.jpeg')):
            incentive_label = QLabel()
            pixmap = QPixmap(self.incentive_file).scaled(400, 300, Qt.KeepAspectRatio)
            incentive_label.setPixmap(pixmap)
            incentive_layout.addWidget(incentive_label, alignment=Qt.AlignCenter)
        else:
            incentive_label = QLabel("Vídeo de Incentivo: Reproduza manualmente")
            incentive_layout.addWidget(incentive_label, alignment=Qt.AlignCenter)
        main_layout.addLayout(incentive_layout)

        # Logs
        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        self.logs.setPlaceholderText("Logs de Coleta")
        main_layout.addWidget(self.logs)

        # Gráficos de Índice Emocional
        self.figures = {}
        self.axes = {}
        graph_layout = QGridLayout()
        for i, name in enumerate(self.names):
            fig, ax = plt.subplots()
            canvas = FigureCanvas(fig)
            ax.set_title(f"{name} - Índice Emocional")
            ax.set_ylim(-1, 1)
            self.figures[name] = fig
            self.axes[name] = ax
            graph_layout.addWidget(canvas, i // 4, i % 4)
        main_layout.addLayout(graph_layout)

        # Score Individual e Consolidado
        self.score_labels = {}
        score_layout = QVBoxLayout()
        for name in self.names:
            label = QLabel(f"{name}: 0.00")
            self.score_labels[name] = label
            score_layout.addWidget(label)
        self.consolidated_score_label = QLabel("Score Consolidado: 0.00")
        score_layout.addWidget(self.consolidated_score_label)
        main_layout.addLayout(score_layout)

        # Menu Toggle
        self.menu_button = QPushButton("Menu")
        self.menu_button.clicked.connect(self.toggle_menu)
        self.menu_frame = self.create_menu()
        self.menu_frame.setVisible(False)
        menu_layout = QHBoxLayout()
        menu_layout.addWidget(self.menu_button, alignment=Qt.AlignTop | Qt.AlignRight)
        menu_layout.addWidget(self.menu_frame)
        main_layout.addLayout(menu_layout)

        self.setLayout(main_layout)
        self.setWindowTitle("Emoções em Tempo Real")
        self.apply_styles()

        # Timer para atualizar gráficos e scores
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_scores)
        self.timer.start(1000)
        print("Timer de coleta real iniciado.")


    
    def start_collection(self):
        self.timer.start(1000)
        self.elapsed_time = 0
        self.logs.clear()  # Limpa os logs anteriores
        self.logs.append("Coleta iniciada.")
        for name in self.names:
            self.scores[name].clear()  # Limpa os dados do gráfico
        self.gsr_ecg_values.clear()  # Limpa os dados salvos
        self.update_scores()

    def stop_collection(self):
        self.timer.stop()
        self.logs.append("Coleta interrompida.")


    from PyQt5.QtWidgets import QApplication  # Import necessário para fechar a aplicação

    def create_menu(self):
        menu_frame = QFrame()
        menu_frame.setStyleSheet("""
            QFrame {
                background-color: #ecf0f3;
                border: 1px solid #dce0e5;
                border-radius: 8px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 12px;
                font-size: 14px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                margin: 4px;
                transition: all 0.3s ease;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c6ea4;
                transform: scale(0.98);
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #ecf0f1;
            }
        """)

        menu_layout = QVBoxLayout()

        self.start_btn = QPushButton("Iniciar")
        self.start_btn.clicked.connect(self.start_collection)

        self.stop_btn = QPushButton("Parar")
        self.stop_btn.clicked.connect(self.stop_collection)

        self.export_csv_btn = QPushButton("Exportar CSV")
        self.export_csv_btn.clicked.connect(self.export_csv)

        self.export_graphics_btn = QPushButton("Exportar Gráficos")
        self.export_graphics_btn.clicked.connect(self.export_graphics)

        # Botão Voltar
        self.back_btn = QPushButton("Voltar")
        self.back_btn.clicked.connect(self.go_back)

        # Botão Fechar Aplicação
        self.close_btn = QPushButton("Fechar Aplicação")
        self.close_btn.clicked.connect(QApplication.quit)

        for btn in [self.start_btn, self.stop_btn, self.export_csv_btn, self.export_graphics_btn, self.back_btn, self.close_btn]:
            menu_layout.addWidget(btn)

        menu_frame.setLayout(menu_layout)
        return menu_frame


    def go_back(self):
        self.parent().setCurrentIndex(0)
    
    def export_csv(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        os.makedirs("Resultados", exist_ok=True)
        file_name = f"Resultados/logs_{timestamp}.csv"  # Nome do arquivo com data e hora
        with open(file_name, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Nome", "GSR", "ECG", "EI", "Sentimento"])
            writer.writerows(self.gsr_ecg_values)
        QMessageBox.information(self, "Exportação Concluída", f"Logs exportados para '{file_name}'.")


    def export_graphics(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        os.makedirs("Graficos", exist_ok=True)
        for name, fig in self.figures.items():
            file_name = f"Graficos/{name}_{timestamp}.png"  # Nome do arquivo com data e hora
            fig.savefig(file_name)
        QMessageBox.information(self, "Exportação Concluída", f"Gráficos exportados para a pasta 'Graficos'.")



    def toggle_menu(self):
        self.menu_frame.setVisible(not self.menu_frame.isVisible())

    def update_scores(self):
        if not self.serial_connection or not self.serial_connection.is_open:
            print("Conexão serial inativa durante a atualização dos scores.")
        else:
            print("Conexão serial ativa. Lendo dados...")


        try:
            serial_data = self.serial_connection.readline().decode("utf-8").strip()
            print(f"Dados recebidos da serial: {serial_data}")
        except Exception as e:
            print(f"Erro ao ler dados da serial: {e}")
            return

        # Dicionário para mapear os sentimentos aos valores numéricos
        sentiment_values = {
            "Alegria": 1.0,
            "Tristeza": -0.5,
            "Terror": -1.0,
            "Neutro": 0.0
        }

        try:
            # Lê uma linha da porta serial
            serial_data = self.serial_connection.readline().decode("utf-8").strip()
            if not serial_data:
                return

            # Processa cada linha de dados (exemplo de formato: "Pessoa 1 - BPM: 72, GSR: 500")
            for line in serial_data.split("\n"):
                if "Pessoa" in line:
                    # Extrai o índice da pessoa
                    person_index = int(line.split(" ")[1]) - 1
                    if person_index >= self.num_people:
                        continue  # Ignora se o índice for maior que o número de pessoas

                    # Substitui "Pessoa X" pelo nome do participante
                    name = self.names[person_index]
                    print(f"Processando dados para {name}")


                    # Extrai os valores de BPM e GSR
                    bpm = float(line.split("BPM:")[1].split(",")[0].strip())
                    gsr = float(line.split("GSR:")[1].strip())

                    # Determina o sentimento com base nos dados do treinamento
                    closest_sentiment = None
                    closest_difference = float('inf')

                    for sentimento, data in self.training_data.items():
                        avg_gsr = sum(data["GSR"]) / len(data["GSR"]) if data["GSR"] else 0
                        avg_bpm = sum(data["BPM"]) / len(data["BPM"]) if data["BPM"] else 0
                        difference = abs(avg_gsr - gsr) + abs(avg_bpm - bpm)
                        if difference < closest_difference:
                            closest_difference = difference
                            closest_sentiment = sentimento

                    # Atualiza os logs com os dados reais
                    self.logs.append(f"{name} | BPM: {bpm}, GSR: {gsr}, Sentimento: {closest_sentiment}")
                    self.gsr_ecg_values.append([name, bpm, gsr, closest_sentiment])

                    # Atualiza os gráficos com base nos valores do sentimento
                    sentiment_value = sentiment_values[closest_sentiment]
                    self.scores[name].append(sentiment_value)
                    ax = self.axes[name]
                    ax.clear()
                    ax.plot(self.scores[name], label=f"Sentimento: {closest_sentiment}")
                    ax.set_ylim(-1.1, 1.1)  # Ajusta o eixo Y para refletir os valores dos sentimentos
                    ax.legend()
                    self.figures[name].canvas.draw()
                    print(f"Atualizando gráficos para {name} com BPM: {bpm}, GSR: {gsr}, Sentimento: {closest_sentiment}")


                    # Atualiza contagens individuais e consolidadas
                    self.sentiment_counts[name][closest_sentiment] += 1
                    self.consolidated_sentiments[closest_sentiment] += 1

            # Atualiza a exibição dos sentimentos consolidados e individuais
            self.update_sentiment_display()

        except Exception as e:
            print(f"Erro ao processar dados da serial: {e}")

        def determine_sentiment(gsr, bpm):
            closest_sentiment = None
            closest_difference = float('inf')

            for sentimento, data in self.training_data.items():
                avg_gsr = sum(data["GSR"]) / len(data["GSR"]) if data["GSR"] else 0
                avg_bpm = sum(data["BPM"]) / len(data["BPM"]) if data["BPM"] else 0
                difference = abs(avg_gsr - gsr) + abs(avg_bpm - bpm)
                if difference < closest_difference:
                    closest_difference = difference
                    closest_sentiment = sentimento

            return closest_sentiment
        print(f"Dados atualizados para gráficos e logs: {self.gsr_ecg_values}")





    def update_sentiment_display(self):
        # Atualiza scores individuais
        for name, label in self.score_labels.items():
            counts = self.sentiment_counts[name]
            label.setText(
                f"{name} | Alegria: {counts['Alegria']} | Tristeza: {counts['Tristeza']} | Neutro: {counts['Neutro']} | Terror: {counts['Terror']}"
            )

        # Atualiza o score consolidado
        consolidated = self.consolidated_sentiments
        self.consolidated_score_label.setText(
            f"Consolidado | Alegria: {consolidated['Alegria']} | Tristeza: {consolidated['Tristeza']} | Neutro: {consolidated['Neutro']} | Terror: {consolidated['Terror']}"
        )




    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f7f9fc;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 14px;
                color: #2c3e50;
            }
            QLabel {
                font-size: 15px;
                color: #34495e;
                font-weight: bold;
            }
            QLineEdit, QSpinBox, QComboBox, QTextEdit {
                background-color: #ffffff;
                border: 1px solid #dce0e5;
                border-radius: 5px;
                padding: 6px;
                font-size: 14px;
                color: #2c3e50;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QTextEdit:focus {
                border: 1px solid #3498db;
            }
            QPushButton {
                background-color: #3498db;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 8px 12px;
                font-size: 14px;
                font-weight: bold;
                transition: background-color 0.3s ease;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #ecf0f1;
            }
            QFrame {
                background-color: #ecf0f3;
                border: 1px solid #dce0e5;
                border-radius: 5px;
            }
            QProgressBar {
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                color: #2c3e50;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                width: 10px;
            }
            QGridLayout {
                margin: 10px;
            }
        """)


class MainApp(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.setup_widget = SetupWidget(self)
        self.addWidget(self.setup_widget)
        self.setCurrentWidget(self.setup_widget)
        # Armazenar dados de treinamento associados a sentimentos
        self.training_data = {
            "Alegria": {"GSR": [], "BPM": []},
            "Tristeza": {"GSR": [], "BPM": []},
            "Neutro": {"GSR": [], "BPM": []},
            "Terror": {"GSR": [], "BPM": []}
        }

    def start_training_screen(self, num_people, names, mode, collection_time, serial_port):
        # Inicia a tela de treinamento
        self.training_widget = TrainingWidget(self, num_people, names, mode, collection_time, serial_port)
        self.addWidget(self.training_widget)
        self.setCurrentWidget(self.training_widget)


    def save_training_data(self, gsr, bpm, current_time):
        # Associa o intervalo de tempo ao sentimento correto
        if 0 <= current_time < 10:
            sentimento = "Alegria"
        elif 10 <= current_time < 20:
            sentimento = "Tristeza"
        elif 20 <= current_time < 30:
            sentimento = "Neutro"
        elif 30 <= current_time <= 41:
            sentimento = "Terror"
        else:
            return  # Ignorar dados fora do intervalo de treinamento

        # Armazena os dados de GSR e BPM no sentimento correspondente
        self.training_data[sentimento]["GSR"].append(gsr)
        self.training_data[sentimento]["BPM"].append(bpm)

    def start_main_window(self, num_people, names, mode, collection_time, serial_connection):
        self.serial_connection = serial_connection  # Salve a conexão no contexto principal
        self.realtime_emotion_widget = RealTimeEmotionWidget(
            num_people, names, self.setup_widget.incentive_file, mode, collection_time, self.serial_connection, self.training_data
        )
        self.addWidget(self.realtime_emotion_widget)
        self.setCurrentWidget(self.realtime_emotion_widget)

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()
    sys.exit(app.exec_())
