import os
import sys
import uuid
import hashlib
import pandas as pd
import serial
import serial.tools.list_ports
import time
import re
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, QTextEdit,
    QStackedWidget, QFileDialog, QGridLayout, QProgressBar, QLineEdit, QMessageBox
)
from PyQt5.QtCore import QUrl, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QGuiApplication, QPixmap
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from sklearn.neighbors import KNeighborsClassifier

LICENSE_FILE = "license.key"

### **Funções de ativação e verificação**

def is_system_activated():
    """
    Verifica se o sistema está ativado lendo o arquivo 'license.key'.
    """
    if os.path.exists(LICENSE_FILE):
        with open(LICENSE_FILE, "r") as file:
            activation_key = file.read().strip()
        return bool(activation_key)  # Verifica se há conteúdo
    return False

def encrypt_key(hardware_id):
    """Gera a chave esperada com base no Hardware ID."""
    secret_suffix = "X9A3Z7B6Q2T5L8C1"
    raw_key = hardware_id + secret_suffix
    hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()
    return hashed_key

### **Classe de Autenticação**

class Authenticator(QWidget):
    def __init__(self):
        super().__init__()
        self.hardware_id = self.get_hardware_id()
        self.key_file = LICENSE_FILE
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Exibe o Hardware ID
        self.info_label = QLabel("Contacte o responsável para validação da chave")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)

        self.hardware_label = QLabel(f"Seu Hardware ID: {self.hardware_id}")
        self.hardware_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.hardware_label)

        # Botão para copiar o Hardware ID
        self.copy_button = QPushButton("Copiar Hardware ID", self)
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        layout.addWidget(self.copy_button)

        # Campo para inserir a chave
        self.key_input = QLineEdit(self)
        self.key_input.setPlaceholderText("Digite a chave de acesso...")
        layout.addWidget(self.key_input)

        # Botão para validar a chave
        self.submit_button = QPushButton("Validar Chave", self)
        self.submit_button.clicked.connect(self.validate_key)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)
        self.setWindowTitle("Autenticação - NeuroEQ")
        self.setFixedSize(400, 250)

    def get_hardware_id(self):
        """Gera o Hardware ID baseado no MAC Address."""
        return str(uuid.getnode())

    def copy_to_clipboard(self):
        """Copia o Hardware ID para a área de transferência."""
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.hardware_id)
        QMessageBox.information(self, "Copiado", "Hardware ID copiado para a área de transferência.")

    def validate_key(self):
        """Valida a chave inserida."""
        entered_key = self.key_input.text().strip()
        expected_key = encrypt_key(self.hardware_id)

        if entered_key == expected_key:
            # Salva a ativação
            with open(self.key_file, "w") as file:
                file.write(expected_key)
            QMessageBox.information(self, "Sucesso", "Chave válida! O sistema está ativado.")
            self.close()  # Fecha a janela
        else:
            QMessageBox.critical(self, "Erro", "Chave inválida! Contacte o responsável.")

### **Classe da Aplicação Principal**

class MainApp(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('NeuroEQ')
        self.showFullScreen()

        # Verifica se o sistema está ativado
        if not is_system_activated():
            self.authenticator = Authenticator()
            self.authenticator.show()
            self.authenticator.activateWindow()  # Garante foco na janela
            self.authenticator.setWindowModality(Qt.ApplicationModal)  # Bloqueia interação com outras janelas
            self.wait_for_authentication()  # Aguarda ativação
            if not is_system_activated():
                QMessageBox.critical(None, "Erro", "O sistema não está ativado. Saindo...")
                sys.exit(1)

        # Configuração do primeiro widget (Seleção inicial)
        self.selection_widget = SelectionWidget()
        self.addWidget(self.selection_widget)
        self.realtime_emotion_widget = None

    def set_num_people(self, num_people, collect_mode, collection_time):
        """
        Configura o número de pessoas, o modo de coleta e o tempo de coleta para o widget principal.
        """
        self.realtime_emotion_widget = RealTimeEmotionWidget(num_people, collect_mode, collection_time)
        if self.count() < 2:
            self.addWidget(self.realtime_emotion_widget)
        else:
            self.widget(1).deleteLater()
            self.insertWidget(1, self.realtime_emotion_widget)

    def wait_for_authentication(self):
        """
        Aguarda até que o processo de autenticação esteja concluído.
        """
        while not is_system_activated():
            QGuiApplication.processEvents()  # Processa eventos da GUI para evitar travamentos
            time.sleep(0.1)


### **Classe de Seleção Inicial**

from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

class SelectionWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.num_people = 1
        self.collect_mode = None
        self.collection_time = 0
        self.incentive_file = None  # Caminho do arquivo de incentivo
        self.incentive_type = None  # Tipo: "Imagem" ou "Vídeo"
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Configuração padrão
        self.title_label = QLabel("Configuração de Monitoramento")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.title_label)

        # Seleção do número de pessoas
        self.info_label = QLabel("Selecione o número de pessoas para monitorar (1 a 8):")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)
        self.people_selector = QComboBox()
        self.people_selector.addItems([str(i) for i in range(1, 9)])
        layout.addWidget(self.people_selector)

        # Escolha do tipo de incentivo
        self.incentive_label = QLabel("Selecione o tipo de incentivo:")
        layout.addWidget(self.incentive_label)
        self.incentive_selector = QComboBox()
        self.incentive_selector.addItems(["Nenhum", "Imagem", "Vídeo"])
        self.incentive_selector.currentIndexChanged.connect(self.toggle_incentive_options)
        layout.addWidget(self.incentive_selector)

        # Campo para carregar o arquivo
        self.file_input_label = QLabel("Selecione o arquivo de incentivo:")
        self.file_input_label.setVisible(False)
        layout.addWidget(self.file_input_label)

        self.file_button = QPushButton("Carregar Arquivo")
        self.file_button.setVisible(False)
        self.file_button.clicked.connect(self.load_incentive_file)
        layout.addWidget(self.file_button)

        # Campo para tempo de coleta
        self.time_input = QLabel("Tempo de coleta (em segundos, ex: 12.50):")
        self.time_input_edit = QLineEdit()
        self.time_input_edit.setPlaceholderText("Digite o tempo em segundos...")
        self.time_input_edit.setVisible(False)
        layout.addWidget(self.time_input)
        layout.addWidget(self.time_input_edit)

        # Botão para avançar
        self.next_button = QPushButton("Próximo", self)
        self.next_button.clicked.connect(self.proceed_to_monitoring)
        layout.addWidget(self.next_button, alignment=Qt.AlignCenter)

        self.setLayout(layout)
        self.setWindowTitle('Configuração de Monitoramento')

    def toggle_incentive_options(self, index):
        """Habilita os campos dependendo do tipo de incentivo."""
        incentive_type = self.incentive_selector.currentText()
        self.file_input_label.setVisible(incentive_type != "Nenhum")
        self.file_button.setVisible(incentive_type != "Nenhum")
        self.time_input.setVisible(incentive_type == "Imagem")
        self.time_input_edit.setVisible(incentive_type == "Imagem")

    def load_incentive_file(self):
        """Abre um diálogo para carregar o arquivo de incentivo."""
        file_filter = "Imagens (*.png *.jpg *.jpeg);;Vídeos (*.mp4 *.avi *.mov)" if self.incentive_selector.currentText() == "Vídeo" else "Imagens (*.png *.jpg *.jpeg)"
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecione o arquivo de incentivo", "", file_filter)
        if file_path:
            self.incentive_file = file_path
            QMessageBox.information(self, "Arquivo Carregado", f"Arquivo selecionado: {file_path}")

    def proceed_to_monitoring(self):
        """Avança para a próxima etapa."""
        self.num_people = int(self.people_selector.currentText())
        self.incentive_type = self.incentive_selector.currentText()

        if self.incentive_type == "Imagem":
            try:
                self.collection_time = float(self.time_input_edit.text())
            except ValueError:
                QMessageBox.critical(self, "Erro", "Insira um tempo válido.")
                return
        elif self.incentive_type == "Vídeo" and self.incentive_file:
            # Obter duração do vídeo
            media = QMediaContent(QUrl.fromLocalFile(self.incentive_file))
            player = QMediaPlayer()
            player.setMedia(media)
            self.collection_time = player.duration() / 1000  # Duração em segundos

        main_app = self.parentWidget()
        main_app.set_num_people(self.num_people, self.collect_mode, self.collection_time, self.incentive_file, self.incentive_type)
        main_app.setCurrentIndex(1)


### **Classe do Widget de Emoções em Tempo Real**

class RealTimeEmotionWidget(QWidget):
    def __init__(self, num_people, collect_mode, collection_time):
        super().__init__()
        self.num_people = num_people
        self.collect_mode = collect_mode
        self.collection_time = collection_time
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Seleção de Porta Serial
        self.port_label = QLabel("Selecione a Porta Serial:")
        layout.addWidget(self.port_label)

        self.port_combo = QComboBox(self)
        self.update_serial_ports()
        layout.addWidget(self.port_combo)

        # Exibição de incentivo
        self.incentive_label = QLabel("Selecione um incentivo (Imagem ou Vídeo):")
        layout.addWidget(self.incentive_label)

        self.incentive_file_button = QPushButton('Selecionar Incentivo')
        self.incentive_file_button.clicked.connect(self.select_incentive)
        layout.addWidget(self.incentive_file_button)

        self.incentive_path_label = QLabel("Nenhum arquivo selecionado")
        layout.addWidget(self.incentive_path_label)

        # Tempo de exibição (caso seja imagem)
        self.incentive_time_label = QLabel("Tempo de exibição (somente para imagem, em segundos):")
        layout.addWidget(self.incentive_time_label)

        self.incentive_time_input = QLineEdit(self)
        self.incentive_time_input.setPlaceholderText("Ex: 10.0")
        layout.addWidget(self.incentive_time_input)

        # Output
        self.output = QTextEdit(self)
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

        # Barra de progresso
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Botões
        self.start_button = QPushButton('Iniciar Coleta e Previsões', self)
        self.start_button.clicked.connect(self.start_collection)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton('Parar Coleta', self)
        self.stop_button.clicked.connect(self.stop_collection)
        self.stop_button.setEnabled(False)
        layout.addWidget(self.stop_button)

        self.clear_button = QPushButton('Limpar Dados', self)
        self.clear_button.clicked.connect(self.clear_data)
        self.clear_button.setEnabled(False)
        layout.addWidget(self.clear_button)

        self.export_button = QPushButton('Exportar CSV', self)
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.export_csv)
        layout.addWidget(self.export_button)

        # Botão para exportar gráficos
        self.export_graphics_button = QPushButton('Exportar Gráficos')
        self.export_graphics_button.setEnabled(False)  # Ativado apenas após a coleta
        self.export_graphics_button.clicked.connect(self.export_graphics)
        layout.addWidget(self.export_graphics_button)

        # Área de exibição de gráficos
        self.plot_widget = EmotionPlotWidget(self.num_people)
        layout.addWidget(self.plot_widget)

        # Widget para exibir scores emocionais
        self.scores_output = QTextEdit(self)
        self.scores_output.setReadOnly(True)
        self.scores_output.setPlaceholderText("Scores emocionais aparecerão aqui...")
        layout.addWidget(self.scores_output)

        self.setLayout(layout)
        self.setWindowTitle('Emoções em Tempo Real')

    def select_incentive(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecione um incentivo", "", 
                                                "Arquivos de mídia (*.jpg *.png *.mp4);;Todos os Arquivos (*)")
        if file_path:
            self.incentive_path_label.setText(f"Selecionado: {file_path}")
            self.incentive_path = file_path

            # Validar se é imagem ou vídeo
            if file_path.endswith(('.jpg', '.png')):
                self.collect_mode = "Imagem"
                self.incentive_time_label.setVisible(True)
                self.incentive_time_input.setVisible(True)
            elif file_path.endswith('.mp4'):
                self.collect_mode = "Vídeo"
                self.incentive_time_label.setVisible(False)
                self.incentive_time_input.setVisible(False)
            else:
                QMessageBox.warning(self, "Formato Inválido", "Por favor, selecione uma imagem (.jpg, .png) ou vídeo (.mp4).")
                self.incentive_path = None

    def show_incentive(self):
        if self.collect_mode == "Imagem":
            pixmap = QPixmap(self.incentive_path)
            image_label = QLabel(self)
            image_label.setPixmap(pixmap)
            image_label.show()
        elif self.collect_mode == "Vídeo":
            cap = cv2.VideoCapture(self.incentive_path)
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                cv2.imshow('Vídeo Incentivo', frame)
                if cv2.waitKey(30) & 0xFF == ord('q'):  # Pressione 'q' para sair
                    break
            cap.release()
            cv2.destroyAllWindows()


    def export_graphics(self):
        """Abre o diálogo para selecionar diretório e exportar gráficos."""
        directory = QFileDialog.getExistingDirectory(self, "Selecione o Diretório")
        if directory:
            try:
                self.plot_widget.export_plots(directory)
                self.output.append(f"Gráficos exportados para o diretório: {directory}")
            except RuntimeError as e:
                self.output.append(str(e))

    def update_serial_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        active_ports = [port.device for port in ports]
        if active_ports:
            self.port_combo.addItems(active_ports)
        else:
            self.port_combo.addItem("Nenhuma porta ativa encontrada")

    def start_collection(self):
    
        if hasattr(self, 'incentive_path') and self.incentive_path:
            if self.collect_mode == "Imagem":
                try:
                    self.collection_time = float(self.incentive_time_input.text())
                except ValueError:
                    QMessageBox.critical(self, "Erro", "Por favor, insira um tempo válido para a imagem.")
                    return
        elif self.collect_mode == "Vídeo":
            
            cap = cv2.VideoCapture(self.incentive_path)
            self.collection_time = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS))
            cap.release()

        self.output.append(f"Iniciando coleta para {self.num_people} pessoa(s) com incentivo: {self.incentive_path}")
        self.progress_bar.setValue(0)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
    
        self.output.append(f"Iniciando coleta e previsões para {self.num_people} pessoa(s)...")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.clear_button.setEnabled(False)
        self.export_button.setEnabled(False)
        self.progress_bar.setValue(0)

        df_base = pd.read_csv('dados_base.csv')
        X_base = df_base[['beatsPerMinute', 'GSR']]
        y_base = df_base['Emotion']
        self.model = KNeighborsClassifier(n_neighbors=3)
        self.model.fit(X_base, y_base)

        self.port = self.port_combo.currentText()

        self.data_collection_thread = RealTimeEmotionThread(
            self.port, self.model, self.num_people, self.collect_mode, self.collection_time
        )
        self.data_collection_thread.log_signal.connect(self.log_output)
        self.data_collection_thread.emotion_signal.connect(self.plot_widget.update_plot)
        self.data_collection_thread.progress_signal.connect(self.update_progress)
        self.data_collection_thread.score_signal.connect(self.update_scores_output)
        self.data_collection_thread.finished.connect(self.collection_finished)
        self.data_collection_thread.start()

    def update_scores_output(self, scores):
        """Atualiza os scores emocionais exibidos na interface."""
        individual_scores = scores["individual"]
        general_scores = scores["general"]

        self.scores_output.clear()
        self.scores_output.append("Scores Individuais:\n")
        for person, emotions in individual_scores.items():
            self.scores_output.append(f"{person}: {emotions}")

        self.scores_output.append("\nScores Consolidados:\n")
        self.scores_output.append(str(general_scores))

    def stop_collection(self):
        self.output.append("Parando coleta e previsões...")
        self.data_collection_thread.collecting = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.clear_button.setEnabled(True)
        self.export_button.setEnabled(True)
        self.export_graphics_button.setEnabled(True)

    def clear_data(self):
        self.output.clear()
        self.plot_widget.clear_plots()
        self.scores_output.clear()
        self.output.append("Dados e gráficos limpos.")

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def collection_finished(self):
        self.output.append("Coleta finalizada.")
        self.export_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self.export_graphics_button.setEnabled(True)
        restart = QMessageBox.question(
            self, "Reiniciar Coleta", "Deseja reiniciar a coleta com as mesmas configurações?",
            QMessageBox.Yes | QMessageBox.No
        )
        if restart == QMessageBox.Yes:
            self.start_collection()

    def log_output(self, message):
        self.output.append(message)

    def export_csv(self):
        try:
            file_path, _ = QFileDialog.getSaveFileName(self, "Salvar CSV", "", "CSV Files (*.csv);;All Files (*)")
            if file_path:
                all_data = []
                for person, entries in self.data_collection_thread.log_data.items():
                    for entry in entries:
                        all_data.append({
                            'Pessoa': person,
                            'BPM': entry.get('BPM'),
                            'GSR': entry.get('GSR'),
                            'Emoção': entry.get('Emoção'),
                            'EI': entry.get('EI')
                        })

                df = pd.DataFrame(all_data)
                df.to_csv(file_path, index=False)
                self.output.append(f"Dados exportados para {file_path}")
        except Exception as e:
            self.output.append(f"Erro ao exportar dados: {e}")

### **Classe para Plotar as Emoções**

class EmotionPlotWidget(QWidget):
    def __init__(self, num_people):
        super().__init__()
        self.num_people = num_people
        self.plots = {}
        self.initUI()

    def initUI(self):
        layout = QGridLayout()
        self.figures = []
        for i in range(self.num_people):
            person_id = f"Pessoa {i + 1}"
            figure, ax = plt.subplots()
            ax.set_title(person_id)
            ax.set_xlabel("Tempo")
            ax.set_ylabel("Índice Emocional (EI)")
            ax.set_ylim(-1, 1)
            canvas = FigureCanvas(figure)
            layout.addWidget(canvas, i // 4, i % 4)
            self.plots[person_id] = ax
            self.figures.append(figure)

        self.setLayout(layout)

    def update_plot(self, data):
        for person, emotion in data.items():
            ax = self.plots[person]
            if not ax.lines:
                # Inicializa uma linha vazia
                line, = ax.plot([], [], '-o', label='EI')
            else:
                line = ax.lines[0]
            x_data = list(range(len(line.get_ydata()) + 1))
            y_data = list(line.get_ydata()) + [emotion]
            line.set_data(x_data, y_data)
            ax.relim()
            ax.autoscale_view()
            ax.figure.canvas.draw()

    def clear_plots(self):
        """Limpa todos os gráficos."""
        for ax in self.plots.values():
            ax.clear()
            ax.set_title("Índice Emocional (EI)")
            ax.set_xlabel("Tempo")
            ax.set_ylabel("Índice Emocional (EI)")
            ax.set_ylim(-1, 1)
            ax.figure.canvas.draw()

    def export_plots(self, directory):
        """Exporta os gráficos para arquivos PNG no diretório especificado."""
        try:
            for person_id, ax in self.plots.items():
                figure = ax.figure
                file_path = os.path.join(directory, f"{person_id}.png")
                figure.savefig(file_path)
        except Exception as e:
            raise RuntimeError(f"Erro ao exportar gráficos: {e}")

### **Thread para Coleta de Emoções em Tempo Real**

class RealTimeEmotionThread(QThread):
    log_signal = pyqtSignal(str)
    emotion_signal = pyqtSignal(dict)
    progress_signal = pyqtSignal(int)
    score_signal = pyqtSignal(dict)  # Envia os scores emocionais em tempo real

    def __init__(self, port, model, num_people, collect_mode, collection_time=0):
        super().__init__()
        self.port = port
        self.model = model
        self.num_people = num_people
        self.collect_mode = collect_mode
        self.collection_time = collection_time
        self.collecting = True
        self.log_data = {f"Pessoa {i+1}": [] for i in range(num_people)}
        self.emotion_scores = {f"Pessoa {i+1}": {} for i in range(num_people)}  # Scores individuais
        self.general_scores = {}  # Score consolidado

    def calculate_emotional_index(self, bpm, gsr):
        """Calcula o índice emocional (EI) normalizado no intervalo de -1 a 1."""
        hr_baseline = 60
        hr_std = 15
        gsr_baseline = 500
        gsr_std = 100

        hr_z = (bpm - hr_baseline) / hr_std
        gsr_z = (gsr - gsr_baseline) / gsr_std

        theta = np.arctan2(gsr_z, hr_z)
        if gsr_z >= 0 and hr_z >= 0:
            beta = (3 * np.pi / 2) - theta
        else:
            beta = (np.pi / 2) - theta

        emotional_index = 1 - (beta / np.pi)
        return np.clip(emotional_index, -1, 1)

    def update_scores(self, person, emotion):
        """Atualiza os scores emocionais individuais e gerais."""
        # Atualizar contagem individual
        if emotion not in self.emotion_scores[person]:
            self.emotion_scores[person][emotion] = 0
        self.emotion_scores[person][emotion] += 1

        # Atualizar contagem geral
        if emotion not in self.general_scores:
            self.general_scores[emotion] = 0
        self.general_scores[emotion] += 1

        # Enviar scores atualizados
        self.score_signal.emit({
            "individual": self.emotion_scores,
            "general": self.general_scores
        })

    def run(self):
        try:
            ser = serial.Serial(self.port, 115200)
            start_time = time.time()
            while self.collecting:
                elapsed_time = time.time() - start_time
                if self.collect_mode == "Tempo Fixo":
                    progress = int((elapsed_time / self.collection_time) * 100)
                    self.progress_signal.emit(min(progress, 100))

                data = ser.readline().decode('utf-8').strip()
                match = re.match(r"(Pessoa \d+) - BPM: ([\d.]+), GSR: (\d+)", data)
                if match:
                    person = match.group(1)
                    bpm = float(match.group(2))
                    gsr = float(match.group(3))
                    emotional_index = self.calculate_emotional_index(bpm, gsr)
                    df = pd.DataFrame([[bpm, gsr]], columns=['beatsPerMinute', 'GSR'])
                    prediction = self.model.predict(df)[0]

                    self.log_data[person].append({'BPM': bpm, 'GSR': gsr, 'Emoção': prediction, 'EI': emotional_index})

                    # Atualizar scores emocionais
                    self.update_scores(person, prediction)

                    self.log_signal.emit(f"{person} - BPM: {bpm}, GSR: {gsr}, Emoção: {prediction}, EI: {emotional_index}")
                    self.emotion_signal.emit({person: emotional_index})

                if self.collect_mode == "Tempo Fixo" and elapsed_time >= self.collection_time:
                    self.collecting = False

            ser.close()
        except Exception as e:
            self.log_signal.emit(f"Erro durante a coleta de dados: {str(e)}")

### **Execução Principal**

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())
