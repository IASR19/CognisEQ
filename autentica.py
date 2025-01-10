import os
import sys
import uuid
import hashlib
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QGuiApplication

class Authenticator(QWidget):
    def __init__(self):
        super().__init__()
        self.hardware_id = self.get_hardware_id()
        self.key_file = "license.key"
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Display the hardware ID
        self.info_label = QLabel("Contacte o responsável para validação da chave")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)

        self.hardware_label = QLabel(f"Seu Hardware ID: {self.hardware_id}")
        self.hardware_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.hardware_label)

        # Button to copy Hardware ID to clipboard
        self.copy_button = QPushButton("Copiar Hardware ID", self)
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        layout.addWidget(self.copy_button)

        # Key input field
        self.key_input = QLineEdit(self)
        self.key_input.setPlaceholderText("Digite a chave de acesso...")
        layout.addWidget(self.key_input)

        # Submit button
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

    def encrypt_key(self, hardware_id):
        """Gera a chave esperada com base no Hardware ID."""
        secret_suffix = "X9A3Z7B6Q2T5L8C1"
        raw_key = hardware_id + secret_suffix
        hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()
        return hashed_key

    def validate_key(self):
        """Valida a chave inserida."""
        entered_key = self.key_input.text().strip()
        expected_key = self.encrypt_key(self.hardware_id)

        if entered_key == expected_key:
            # Salva a ativação
            with open(self.key_file, "w") as file:
                file.write(expected_key)
            QMessageBox.information(self, "Sucesso", "Chave válida! O sistema está ativado.")
            self.close()  # Fecha a janela
        else:
            QMessageBox.critical(self, "Erro", "Chave inválida! Contacte o responsável.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Authenticator()
    window.show()
    sys.exit(app.exec_())
