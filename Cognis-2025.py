from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QStackedWidget, QPushButton, QTextEdit, QProgressBar, QScrollArea, QFrame, QHBoxLayout, QLineEdit, QSpinBox, QComboBox, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
import matplotlib.pyplot as plt
import re
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
import subprocess  # Para abrir o vídeo no reprodutor padrão
import serial  # Para comunicação serial
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtGui import QPainter


def calcular_coeficiente_emocional(bpm, gsr):
    """
    Calcula o coeficiente emocional e classifica em níveis de positivo, neutro e negativo.
    """

    # Normalização do BPM (faixa esperada: 60 a 120)
    bpm_normalizado = min(max((bpm - 60) / 60, -1), 1)  # Transforma a faixa [60, 120] para [-1, 1]

    # Normalização do GSR (faixa esperada: 4.5 a 6.5)
    gsr_normalizado = min(max((gsr - 5.5) / 1, -1), 1)  # Transforma a faixa [4.5, 6.5] para [-1, 1]

    # Coeficiente emocional considerando peso maior para BPM
    coeficiente = (0.7 * bpm_normalizado) + (0.3 * gsr_normalizado)

    # Classificação do sentimento em níveis
    if coeficiente >= 0.75:
        return coeficiente, "Muito Positivo"
    elif coeficiente >= 0.5:
        return coeficiente, "Médio Positivo"
    elif coeficiente >= 0.25:
        return coeficiente, "Pouco Positivo"
    elif -0.25 < coeficiente < 0.25:
        return coeficiente, "Neutro"
    elif coeficiente <= -0.75:
        return coeficiente, "Muito Negativo"
    elif coeficiente <= -0.5:
        return coeficiente, "Médio Negativo"
    elif coeficiente <= -0.25:
        return coeficiente, "Pouco Negativo"

    return coeficiente, "Neutro"



'''
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
        """ Finaliza o treinamento e inicia a coleta real. """
        self.timer.stop()

        QMessageBox.information(self, "Treinamento Concluído", "Treinamento finalizado!")

        # Garantir que a conexão serial esteja aberta corretamente antes de passar
        try:
            serial_connection = serial.Serial(self.serial_port, 115200, timeout=1)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível abrir a conexão serial.\nErro: {e}")
            return

        # Passar para a tela de coleta real com a conexão serial aberta
        self.parent.start_main_window(
            self.num_people,
            self.names,
            self.mode,
            self.collection_time,
            serial_connection  # ✅ Agora passamos um objeto válido de `serial.Serial`
        )



    def resizeEvent(self, event):
        """ Redimensionamento na TrainingWidget não precisa tratar imagens """
        super().resizeEvent(event)
        
        
    
    def update_image(self):
        """ Atualiza a imagem para se ajustar proporcionalmente à tela """
        if not self.original_pixmap or self.original_pixmap.isNull():
            return  # Evita erro caso a imagem não tenha sido carregada corretamente

        screen_rect = self.screen().availableGeometry()
        screen_width, screen_height = screen_rect.width(), screen_rect.height()

        pixmap_width = self.original_pixmap.width()
        pixmap_height = self.original_pixmap.height()

        if pixmap_width == 0 or pixmap_height == 0:
            return  # Evita divisão por zero

        scale_factor = min(screen_width / pixmap_width, screen_height / pixmap_height, 1.0)
        new_width = int(pixmap_width * scale_factor)
        new_height = int(pixmap_height * scale_factor)

        resized_pixmap = self.original_pixmap.scaled(new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.stimulus_label.setPixmap(resized_pixmap)
        self.stimulus_label.setAlignment(Qt.AlignCenter)

        
    def closeEvent(self, event):
        """ Para o vídeo ao fechar a janela """
        if hasattr(self, 'media_player') and self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.stop()
        event.accept()
'''



class SetupWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.stimuli = []  # Lista de estímulos (arquivos + tempo)
        self.dynamic_name_fields = []  # Inicializa como uma lista vazia
        self.incentive_file = None  # Inicializa como None para evitar erro
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
        self.num_people_spinbox.setRange(1, 2)
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
        
                # Número de estímulos
        self.num_stimuli_label = QLabel("Quantos estímulos deseja apresentar?")
        self.num_stimuli_spinbox = QSpinBox()
        self.num_stimuli_spinbox.setRange(0, 10)  # Máximo de 10 estímulos
        self.num_stimuli_spinbox.valueChanged.connect(self.create_stimuli_fields)
        layout.addWidget(self.num_stimuli_label)
        layout.addWidget(self.num_stimuli_spinbox)

        # Área onde os campos de estímulos serão adicionados
        self.stimuli_layout = QVBoxLayout()
        layout.addLayout(self.stimuli_layout)


        self.setLayout(layout)

        def create_stimuli_fields(self):
            """ Cria dinamicamente os campos para upload e tempo de cada estímulo. """
            # Remove os campos anteriores, se existirem
            while self.stimuli_layout.count():
                item = self.stimuli_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            self.stimuli = []  # Reseta a lista de estímulos

            # Criar novos campos
            for i in range(self.num_stimuli_spinbox.value()):
                file_button = QPushButton(f"Selecionar Estímulo {i+1}")
                file_button.clicked.connect(lambda _, idx=i: self.select_stimulus(idx))
                time_input = QLineEdit()
                time_input.setPlaceholderText("Tempo de exibição (segundos)")

                self.stimuli_layout.addWidget(file_button)
                self.stimuli_layout.addWidget(time_input)
                self.stimuli.append({"file": None, "time_input": time_input, "button": file_button})

        def select_stimulus(self, index):
            """ Permite selecionar um arquivo de estímulo. """
            file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Estímulo", "", "Imagens e Vídeos (*.png *.jpg *.mp4)")
            if file_path:
                self.stimuli[index]["file"] = file_path
                self.stimuli[index]["button"].setText(f"Selecionado: {file_path.split('/')[-1]}")
                print(f"Arquivo selecionado para estímulo {index + 1}: {file_path}")  # 🔍 Debug


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
            
    def create_stimuli_fields(self):
        """ Cria dinamicamente os campos para upload e tempo de cada estímulo. """
        # Remove os campos anteriores, se existirem
        while self.stimuli_layout.count():
            item = self.stimuli_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.stimuli = []  # Reseta a lista de estímulos

        # Criar novos campos
        for i in range(self.num_stimuli_spinbox.value()):
            file_button = QPushButton(f"Selecionar Estímulo {i+1}")
            file_button.clicked.connect(lambda _, idx=i: self.select_stimulus(idx))
            time_input = QLineEdit()
            time_input.setPlaceholderText("Tempo de exibição (segundos)")

            self.stimuli_layout.addWidget(file_button)
            self.stimuli_layout.addWidget(time_input)
            self.stimuli.append({"file": None, "time_input": time_input, "button": file_button})
            
    def start_presentation(self):
        """ Inicia a apresentação dos estímulos em sequência. """
        stimuli_sequence = []
        for stim in self.stimuli:
            file_path = stim["file"]
            time_value = stim["time_input"].text()

            if not file_path or not time_value.isdigit():
                QMessageBox.critical(self, "Erro", "Todos os estímulos precisam de um arquivo e tempo válido.")
                return

            stimuli_sequence.append((file_path, int(time_value)))

        
        
    def select_stimulus(self, index):
        """ Permite selecionar um arquivo de estímulo. """
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Estímulo", "", "Imagens e Vídeos (*.png *.jpg *.mp4)")
        if file_path:
            self.stimuli[index]["file"] = file_path
            self.stimuli[index]["button"].setText(f"Selecionado: {file_path.split('/')[-1]}")




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

        # Criar a sequência de estímulos corretamente
        self.parent.stimuli_sequence = []
        for stim in self.stimuli:
            file_path = stim["file"]
            time_value = stim["time_input"].text()

            if not file_path or not time_value.isdigit():
                QMessageBox.critical(self, "Erro", "Todos os estímulos precisam de um arquivo e tempo válido.")
                return

            self.parent.stimuli_sequence.append((file_path, int(time_value)))

        print(f"Estímulos armazenados na SetupWidget: {self.parent.stimuli_sequence}")  # 🔍 Debug

        if not self.parent.stimuli_sequence:
            QMessageBox.critical(self, "Erro", "Nenhum estímulo foi armazenado!")
            return

        # Passa para o MainApp
        try :
            serial_connection = serial.Serial(self.selected_port, 115200, timeout=1)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível abrir a conexão serial.\nErro: {e}")
            return  # Impede que prossiga se der erro
        self.parent.start_main_window(
            num_people,
            participant_names,
            self.collection_mode,
            int(self.collection_time) if self.collection_time else None,
            serial_connection  # Passando o objeto de conexão serial
        )



class StimulusWindow(QWidget):
    def __init__(self, stimuli_sequence):
        super().__init__()
        self.stimuli_sequence = stimuli_sequence if stimuli_sequence else []
        self.current_index = 0
        self.pixmap = None  # Armazena a imagem atual
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Estímulo")
        self.showFullScreen()  # Abrir em tela cheia para evitar problemas de escala

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.show_next_stimulus)

        self.show_next_stimulus()  # Exibir o primeiro estímulo

    def show_next_stimulus(self):
        """ Exibe o próximo estímulo da lista. """
        if not self.stimuli_sequence or self.current_index >= len(self.stimuli_sequence):
            print("Todos os estímulos foram apresentados. Fechando janela.")
            self.close()
            return

        file_path, duration = self.stimuli_sequence[self.current_index]
        print(f"Tentando exibir: {file_path} por {duration} segundos")

        if not os.path.exists(file_path):
            print(f"Erro: O arquivo {file_path} não existe!")
            return

        self.current_index += 1  # Avança para o próximo estímulo

        if file_path.endswith(('.png', '.jpg', '.jpeg')):
            self.pixmap = QPixmap(file_path)
            if self.pixmap.isNull():
                print(f"Erro ao carregar a imagem: {file_path}")
                return

            print(f"Imagem carregada com sucesso: {file_path}")

            self.update()  # Força a atualização do widget para desenhar a imagem

        self.timer.start(duration * 1000)  # Trocar para o próximo estímulo

    def paintEvent(self, event):
        """ Desenha a imagem na tela. """
        if self.pixmap:
            painter = QPainter(self)
            scaled_pixmap = self.pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)









class RealTimeEmotionWidget(QWidget):
    def __init__(self, num_people, names, incentive_file, mode, collection_time, serial_connection, training_data, stimuli_sequence):
        super().__init__()
        self.num_people = num_people
        self.names = names
        self.incentive_file = incentive_file
        self.mode = mode
        self.collection_time = collection_time
        self.serial_connection = serial_connection
        self.training_data = training_data  # Salva os dados de treinamento
        self.stimuli_sequence = stimuli_sequence
        print(f"Conexão serial na coleta real: {self.serial_connection}")


        if not self.serial_connection or not self.serial_connection.is_open:
            print("Erro: Conexão serial não está aberta.")

        self.scores = {name: [] for name in self.names[:2]}
        self.gsr_ecg_values = []
        # Inicializa os contadores de sentimentos individuais
        self.sentiment_counts = {
            name: {
                "Muito Positivo": 0, "Médio Positivo": 0, "Pouco Positivo": 0,
                "Neutro": 0,
                "Pouco Negativo": 0, "Médio Negativo": 0, "Muito Negativo": 0
            }
            for name in self.names
        }

        # Inicializa os contadores de sentimentos consolidados
        self.consolidated_sentiments = {
            "Muito Positivo": 0, "Médio Positivo": 0, "Pouco Positivo": 0,
            "Neutro": 0,
            "Pouco Negativo": 0, "Médio Negativo": 0, "Muito Negativo": 0
        }



        self.initUI()




    def initUI(self):
        main_layout = QVBoxLayout()

        # Logs
        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        self.logs.setPlaceholderText("Logs de Coleta")
        main_layout.addWidget(self.logs)
        
        # Criar uma cópia da sequência de estímulos para evitar modificações inesperadas
        self.stimuli_sequence = self.stimuli_sequence if self.stimuli_sequence else []
        
        print(f"Passando sequência de estímulos para StimulusWindow: {self.stimuli_sequence}")  # 🔍 Debug
        
        if self.stimuli_sequence:
            self.stimulus_window = StimulusWindow(self.stimuli_sequence)
            self.stimulus_window.show()
        else:
            QMessageBox.critical(self, "Erro", "Nenhum estímulo foi armazenado corretamente!")


        # Criar a janela de estímulos corretamente
        self.stimulus_window = StimulusWindow(self.stimuli_sequence)
        self.stimulus_window.show()

        # Gráficos de Índice Emocional
        # Gráficos de Índice Emocional
        self.figures = {}
        self.axes = {}
        self.canvases = {}  # Adicionando os canvases para serem atualizados corretamente

        graph_layout = QGridLayout()
        for i, name in enumerate(self.names[:self.num_people]):  # Garantir que todos os participantes tenham gráficos
            fig, ax = plt.subplots()
            canvas = FigureCanvas(fig)
            self.figures[name] = fig
            self.axes[name] = ax
            self.canvases[name] = canvas  # Guardar o canvas para ser atualizado depois
            ax.set_title(f"{name} - Índice Emocional")
            ax.set_ylim(-1, 1)  # Definir limites para os valores de índice emocional
            ax.set_xlim(0, 30)  # Definir limite do tempo para 30 segundos
            ax.set_xlabel("Tempo")
            ax.set_ylabel("Índice Emocional")
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

            # Cabeçalhos do CSV
            writer.writerow(["Nome", "BPM", "GSR", "EI", "Sentimento"])

            # Escrever cada linha com sentimento incluído
            for entry in self.gsr_ecg_values:
                name, bpm, gsr = entry
                coeficiente, sentimento = calcular_coeficiente_emocional(bpm, gsr)
                writer.writerow([name, bpm, gsr, coeficiente, sentimento])

        QMessageBox.information(self, "Exportação Concluída", f"Logs exportados para '{file_name}'.")



    def export_graphics(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        os.makedirs("Graficos", exist_ok=True)
        for name, fig in self.figures.items():
            file_name = f"Graficos/{name}_{timestamp}.png"  
            fig.savefig(file_name)
        QMessageBox.information(self, "Exportação Concluída", f"Gráficos exportados para a pasta 'Graficos'.")



    def toggle_menu(self):
        self.menu_frame.setVisible(not self.menu_frame.isVisible())




    def update_scores(self):
        if not self.serial_connection or not self.serial_connection.is_open:
            print("Conexão serial inativa.")
            return

        try:
            # Lê todos os dados disponíveis na serial
            serial_data = self.serial_connection.read(self.serial_connection.in_waiting).decode("utf-8").strip()
            if not serial_data:
                return

            # Processa cada linha recebida
            for line in serial_data.split("\n"):
                if "Pessoa" in line:
                    try:
                        person_index = int(line.split(" ")[1]) - 1
                        if person_index < 0 or person_index >= self.num_people:
                            continue  # Ignora se o índice for inválido

                        name = self.names[person_index]

                        # Extrai BPM e GSR com regex
                        bpm_match = re.search(r"BPM:\s*([\d.]+)", line)
                        gsr_match = re.search(r"GSR:\s*([\d.]+)", line)

                        if bpm_match and gsr_match:
                            bpm = float(bpm_match.group(1))
                            gsr = float(gsr_match.group(1)) / 100  # Converte para microSiemens

                            # **Descartar leituras absurdas**
                            if bpm < 30 or bpm > 200:  
                                print(f"⚠️ BPM inválido detectado ({bpm}), descartando leitura...")
                                continue  

                            # Normaliza BPM alto (acima de 100)
                            if bpm > 100:
                                bpm = 100 + (bpm - 100) * 0.5  
                                bpm = min(bpm, 120)

                            # Atualiza os logs e gráficos
                            # Calcula o coeficiente emocional e classifica o sentimento
                            coeficiente, sentimento = calcular_coeficiente_emocional(bpm, gsr)
                            # Atualiza a contagem do sentimento individual
                            if name in self.sentiment_counts:
                                self.sentiment_counts[name][sentimento] += 1
                            else:
                                self.sentiment_counts[name] = {"Muito Positivo": 0, "Médio Positivo": 0, "Pouco Positivo": 0,
                                                            "Neutro": 0, "Pouco Negativo": 0, "Médio Negativo": 0, "Muito Negativo": 0}
                                self.sentiment_counts[name][sentimento] += 1

                            # Atualiza a contagem consolidada
                            self.consolidated_sentiments[sentimento] += 1


                            # Adiciona ao log o BPM, GSR e o sentimento identificado
                            self.logs.append(f"{name} | BPM: {bpm}, GSR: {gsr*100:.4f}, Sentimento: {sentimento}")
                            self.logs.ensureCursorVisible()


                            self.gsr_ecg_values.append([name, bpm, gsr])
                            
                            # Atualiza os gráficos
                            ax = self.axes[name]
                            # Atualiza os gráficos com BPM, GSR e o Índice Emocional
                            ax.clear()
                            # Lista de índices emocionais para o gráfico
                            indices_emocionais = [
                                calcular_coeficiente_emocional(v[1], v[2])[0] for v in self.gsr_ecg_values if v[0] == name
                            ]

                            # Se houver dados, plota o gráfico
                            if indices_emocionais:
                                ax.plot(range(len(indices_emocionais)), indices_emocionais, label="Índice Emocional", color="green")

                            ax.set_ylim(-1, 1)  # Mantém a escala de -1 a 1
                            ax.set_xlim(max(0, len(indices_emocionais) - 30), len(indices_emocionais))  # Mantém 30 pontos visíveis
                            ax.legend()
                            ax.set_title(f"{name} - Índice Emocional")
                            ax.set_xlabel("Tempo")
                            ax.set_ylabel("Índice Emocional")
                            self.canvases[name].draw_idle()

                            # Adiciona a curva do índice emocional
                            ax.plot(
                                range(len(self.gsr_ecg_values)),
                                [calcular_coeficiente_emocional(v[1], v[2])[0] for v in self.gsr_ecg_values if v[0] == name],
                                label="Índice Emocional",
                                color="green"
                            )

                            ax.set_ylim(-1, 1)  # Mantém a escala de -1 a 1
                            ax.legend()
                            ax.set_title(f"{name} - Índice Emocional")
                            ax.set_xlabel("Tempo")
                            ax.set_ylabel("Índice Emocional")
                            self.canvases[name].draw_idle()


                    except Exception as e:
                        print(f"❌ Erro ao processar linha da serial: {line}, erro: {e}")
                        continue  
                    
                    

        except Exception as e:
            print(f"❌ Erro na leitura da serial: {e}")
        self.update_sentiment_display()








    def update_sentiment_display(self):
        # Atualiza scores individuais
        for name, label in self.score_labels.items():
            if name in self.sentiment_counts:
                scores = " | ".join([f"{key}: {value}" for key, value in self.sentiment_counts[name].items()])
                label.setText(f"{name} | {scores}")

        # Atualiza o score consolidado
        consolidated_scores = " | ".join([f"{key}: {value}" for key, value in self.consolidated_sentiments.items()])
        self.consolidated_score_label.setText(f"Consolidado | {consolidated_scores}")





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
        self.stimuli_sequence = []
        # Armazenar dados de treinamento associados a sentimentos
        self.training_data = {
            "Alegria": {"GSR": [], "BPM": []},
            "Tristeza": {"GSR": [], "BPM": []},
            "Neutro": {"GSR": [], "BPM": []},
            "Terror": {"GSR": [], "BPM": []}
        }

    def start_main_window(self, num_people, names, mode, collection_time, serial_connection):
        """ Inicia a tela de coleta real diretamente, sem passar pelo treinamento. """
        if not serial_connection or not serial_connection.is_open:
            QMessageBox.critical(self, "Erro", "A conexão serial não está aberta corretamente.")
            return


        self.serial_connection = serial_connection

        if not self.stimuli_sequence:
            QMessageBox.critical(self, "Erro", "Nenhum estímulo foi armazenado!")
            return

        self.realtime_emotion_widget = RealTimeEmotionWidget(
            num_people, names, self.setup_widget.incentive_file, mode, collection_time, 
            self.serial_connection, {}, self.stimuli_sequence  # Removendo dados de treinamento
        )
        self.addWidget(self.realtime_emotion_widget)
        self.setCurrentWidget(self.realtime_emotion_widget)



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
        """ Inicia a tela de coleta real após o treinamento. """
        if not isinstance(serial_connection, serial.Serial):
            QMessageBox.critical(self, "Erro", "A conexão serial não foi aberta corretamente.")
            return

        self.serial_connection = serial_connection  # ✅ Agora garantimos que a conexão serial é válida
        print(f"Passando sequência de estímulos para RealTimeEmotionWidget: {self.stimuli_sequence}")  # 🔍 Debug

        if not self.stimuli_sequence:
            print("Erro: Nenhum estímulo foi armazenado antes da coleta real!")  # 🔍 Debug
            QMessageBox.critical(self, "Erro", "Nenhum estímulo foi armazenado!")
            return

        self.realtime_emotion_widget = RealTimeEmotionWidget(
            num_people, names, self.setup_widget.incentive_file, mode, collection_time, self.serial_connection, self.training_data, self.stimuli_sequence
        )
        self.addWidget(self.realtime_emotion_widget)
        self.setCurrentWidget(self.realtime_emotion_widget)



    def start_stimulus_presentation(self, stimuli_sequence):
        print(f"Iniciando apresentação de estímulos: {stimuli_sequence}")  # 🔍 Debug: Verifica os arquivos recebidos

        # Criar uma cópia segura dos estímulos
        stimuli_sequence = list(stimuli_sequence)

        # Verificar se a lista está vazia
        if not stimuli_sequence:
            print("Erro: Nenhum estímulo foi recebido!")  # 🔍 Debug
            return

        # Verificar se os arquivos existem
        for file_path, _ in stimuli_sequence:
            if not os.path.exists(file_path):
                print(f"Erro: O arquivo {file_path} não existe!")  # 🔍 Debug
                return

        self.stimulus_window = StimulusWindow(stimuli_sequence)
        self.stimulus_window.show()



if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    main_window = MainApp()
    main_window.show()
    sys.exit(app.exec_())
