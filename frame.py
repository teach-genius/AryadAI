from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QRectF
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, 
                              QHBoxLayout, QPushButton, QTextEdit, QFileDialog, QMessageBox,
                              QScrollArea, QSizePolicy, QCheckBox, QComboBox, QStackedWidget, QDialog)
from PySide6.QtGui import QPixmap, QIcon, QColor, QPainter, QFontMetrics, QLinearGradient
import sys
import math
from gemini_agent import GeminiAgent
from audio_handler import AudioHandler

class MessageWidget(QWidget):
    def __init__(self, text, is_user=True, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        message = QLabel(text)
        message.setWordWrap(True)
        message.setStyleSheet(f"""
            QLabel {{
                background-color: {'#2B2D42' if is_user else '#1E1F2B'};
                color: {'#E2E8F0' if is_user else '#F8FAFC'};
                padding: 12px 16px;
                border-radius: 12px;
                font-size: 14px;
                max-width: 700px;
                border: 1px solid {'#3B3D52' if is_user else '#2A2B3A'};
            }}
        """)
        
        # Align the message to the left or right
        alignment = Qt.AlignRight if is_user else Qt.AlignLeft
        container = QWidget()
        container_layout = QHBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container.setLayout(container_layout)

        if is_user:
            container_layout.addStretch()
            container_layout.addWidget(message)
        else:
            container_layout.addWidget(message)
            container_layout.addStretch()

        layout.addWidget(container)

class TypingIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 30)
        self._dots = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self._animate_dots)
        self.timer.start(500)
        self.dot_color = QColor(200, 200, 200)

    def _animate_dots(self):
        self._dots = (self._dots + 1) % 4
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self.dot_color)
        painter.setPen(Qt.NoPen)

        dot_radius = 4
        spacing = 8
        start_x = (self.width() - (3 * dot_radius * 2 + 2 * spacing)) // 2 + dot_radius
        center_y = self.height() // 2

        for i in range(3):
            if i < self._dots:
                x = start_x + i * (dot_radius * 2 + spacing)
                painter.drawEllipse(x - dot_radius, center_y - dot_radius, dot_radius * 2, dot_radius * 2)
        painter.end()

class TypingLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self._full_text = text
        self._displayed_text = ""
        self._index = 0
        self._timer = QTimer()
        self._timer.timeout.connect(self._add_character)
        self.setWordWrap(True)
        self.setStyleSheet("color: white; font-size: 14px;")
        self.setText("")

    def start_typing(self, interval=50):
        self._index = 0
        self._displayed_text = ""
        self._timer.start(interval)

    def _add_character(self):
        if self._index < len(self._full_text):
            self._displayed_text += self._full_text[self._index]
            self.setText(self._displayed_text)
            self._index += 1
        else:
            self._timer.stop()

class RecordingAnimation(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 80)  # Augmenté la taille pour un meilleur effet
        self.time = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.bar_color = QColor(100, 149, 237)  # Couleur bleu clair
        self.background_color = QColor(52, 53, 65)
        self.audio_handler = None
        
        # Effet de gradient pour les barres
        self.gradient = QLinearGradient(0, 0, 0, self.height())
        self.gradient.setColorAt(0, QColor(100, 149, 237))  # Bleu clair en haut
        self.gradient.setColorAt(1, QColor(70, 130, 180))   # Bleu plus foncé en bas
        
    def set_audio_handler(self, handler):
        self.audio_handler = handler
        
    def start(self):
        self.time = 0
        self.timer.start(30)  # Mise à jour plus rapide pour une animation plus fluide
        self.show()
        
    def stop(self):
        self.timer.stop()
        self.hide()
        
    def update_animation(self):
        self.time += 1
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Dessiner le fond avec un léger dégradé
        bg_gradient = QLinearGradient(0, 0, 0, self.height())
        bg_gradient.setColorAt(0, QColor(52, 53, 65))
        bg_gradient.setColorAt(1, QColor(45, 46, 58))
        painter.fillRect(self.rect(), bg_gradient)
        
        # Paramètres des ondes
        num_bars = 40  # Plus de barres pour un effet plus détaillé
        bar_spacing = 3
        bar_width = (self.width() - (num_bars - 1) * bar_spacing) // num_bars
        if bar_width <= 0: bar_width = 1
        
        max_height = self.height() * 0.7
        center_y = self.height() // 2
        
        painter.setPen(Qt.NoPen)
        
        for i in range(num_bars):
            x_pos = i * (bar_width + bar_spacing)
            
            if self.audio_handler and self.audio_handler.recording:
                # Utiliser le niveau audio réel avec une courbe plus naturelle
                audio_level = self.audio_handler.get_audio_level()
                # Appliquer une courbe d'easing pour un mouvement plus naturel
                bar_height = max_height * (audio_level ** 0.5)
            else:
                # Animation par défaut plus sophistiquée
                t = self.time * 0.05
                phase = i * 0.2
                amplitude1 = max_height * 0.4
                amplitude2 = max_height * 0.2
                h1 = amplitude1 * math.sin(t + phase)
                h2 = amplitude2 * math.sin(t * 1.5 + phase * 1.2)
                bar_height = abs(h1 + h2)
                bar_height = min(bar_height, max_height)

            # Créer un effet de barre arrondie
            bar_rect = QRectF(x_pos, center_y - bar_height / 2, bar_width, bar_height)
            
            # Appliquer le gradient
            painter.setBrush(self.gradient)
            
            # Dessiner la barre avec des coins arrondis
            painter.drawRoundedRect(bar_rect, bar_width / 2, bar_width / 2)
            
            # Ajouter un effet de brillance
            highlight = QLinearGradient(0, bar_rect.top(), 0, bar_rect.bottom())
            highlight.setColorAt(0, QColor(255, 255, 255, 30))
            highlight.setColorAt(1, QColor(255, 255, 255, 0))
            painter.setBrush(highlight)
            painter.drawRoundedRect(bar_rect, bar_width / 2, bar_width / 2)

        painter.end()

class AccountSettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Titre
        title = QLabel("Paramètres du compte")
        title.setStyleSheet("""
            QLabel {
                color: #E2E8F0;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        layout.addWidget(title)
        
        # Message de confirmation (initialement caché)
        self.confirmation_label = QLabel()
        self.confirmation_label.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-size: 18px;
                padding: 15px;
                background-color: #1E1F2B;
                border-radius: 8px;
                border: 2px solid #4CAF50;
                margin: 10px;
            }
        """)
        self.confirmation_label.setAlignment(Qt.AlignCenter)
        self.confirmation_label.setMinimumHeight(80)  # Hauteur minimale pour le message
        self.confirmation_label.hide()
        layout.addWidget(self.confirmation_label)
        
        # Section Interprète
        interpreter_section = QWidget()
        interpreter_layout = QVBoxLayout()
        interpreter_layout.setSpacing(15)
        
        # Checkbox pour activer l'interprète
        self.interpreter_checkbox = QCheckBox("Interprète AryadAI")
        self.interpreter_checkbox.setStyleSheet("""
            QCheckBox {
                color: #E2E8F0;
                font-size: 16px;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #3B3D52;
                background-color: #2B2D42;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #C6C7F8;
                background-color: #C6C7F8;
                border-radius: 4px;
            }
        """)
        interpreter_layout.addWidget(self.interpreter_checkbox)
        
        # Combobox pour la langue
        self.language_combo = QComboBox()
        self.language_combo.addItems([
            "Français", "Anglais", "Espagnol", "Russe", "Arabe"
        ])
        self.language_combo.setStyleSheet("""
            QComboBox {
                background-color: #2B2D42;
                color: #E2E8F0;
                border: 1px solid #3B3D52;
                border-radius: 8px;
                padding: 8px;
                min-width: 200px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #2B2D42;
                color: #E2E8F0;
                selection-background-color: #3B3D52;
                border: 1px solid #3B3D52;
            }
        """)
        interpreter_layout.addWidget(self.language_combo)
        
        interpreter_section.setLayout(interpreter_layout)
        layout.addWidget(interpreter_section)
        
        # Bouton Enregistrer
        self.save_button = QPushButton("Enregistrer les modifications")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #C6C7F8;
                color: black;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-weight: bold;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #B5B6E8;
            }
        """)
        self.save_button.clicked.connect(self.on_save_clicked)
        layout.addWidget(self.save_button, alignment=Qt.AlignCenter)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def show_confirmation_message(self, message):
        """Affiche un message de confirmation pendant 3 secondes"""
        print("Affichage du message de confirmation")  # Debug
        self.confirmation_label.setText(message)
        self.confirmation_label.show()
        self.confirmation_label.raise_()
        # Forcer la mise à jour de l'interface
        QApplication.processEvents()
        # Cacher le message après 3 secondes
        QTimer.singleShot(3000, self.hide_confirmation_message)
        
    def hide_confirmation_message(self):
        """Cache le message de confirmation"""
        print("Masquage du message de confirmation")  # Debug
        self.confirmation_label.hide()
        # Forcer la mise à jour de l'interface
        QApplication.processEvents()
        
    def on_save_clicked(self):
        print("Bouton Enregistrer cliqué")  # Debug
        try:
            is_interpreter = self.interpreter_checkbox.isChecked()
            selected_language = self.language_combo.currentText()
            print(f"Interprète: {is_interpreter}, Langue: {selected_language}")  # Debug
            
            # Obtenir la fenêtre principale (instance de frame)
            main_window = None
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, frame):
                    main_window = widget
                    break
            
            if main_window:
                print("Fenêtre principale trouvée")  # Debug
                
                # Afficher d'abord le message de confirmation
                message = f"Le mode interprète a été activé.\nLangue cible : {selected_language}" if is_interpreter else "Le mode conversationnel a été activé."
                self.show_confirmation_message(message)
                
                # Attendre 1 seconde avant de continuer
                def continue_operations():
                    # Mettre à jour l'agent
                    main_window.update_agent_mode(is_interpreter, selected_language)
                    print("Agent mis à jour")  # Debug
                    
                    # Effacer les conversations
                    main_window.clear_conversations()
                    print("Conversations effacées")  # Debug
                    
                    # Retourner à la vue principale
                    main_window.stacked_widget.setCurrentWidget(main_window.scroll_area)
                    print("Retour à la vue principale")  # Debug
                
                QTimer.singleShot(3000, continue_operations)
            else:
                print("Fenêtre principale non trouvée")  # Debug
                self.show_confirmation_message("Erreur : Impossible de trouver la fenêtre principale")
                
        except Exception as e:
            print(f"Erreur: {str(e)}")  # Debug
            # Afficher le message d'erreur
            self.show_confirmation_message(f"Une erreur est survenue : {str(e)}")

class CustomMessageWindow(QWidget):
    def __init__(self, parent=None, title="", message=""):
        super().__init__(parent, Qt.Window | Qt.FramelessWindowHint)
        self.setWindowTitle(title)
        self.setFixedSize(400, 200)
        self.setStyleSheet("""
            QWidget {
                background-color: #1A1B26;
                border: 2px solid #3B3D52;
                border-radius: 10px;
            }
            QLabel {
                color: #E2E8F0;
                font-size: 14px;
            }
            QPushButton {
                background-color: #C6C7F8;
                color: black;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #B5B6E8;
            }
        """)
        
        # Layout principal
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Titre
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(message_label)
        
        # Bouton OK
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.close)
        layout.addWidget(ok_button, alignment=Qt.AlignCenter)
        
        self.setLayout(layout)
        
        # Centrer la fenêtre par rapport à son parent
        if parent:
            self.move(parent.x() + (parent.width() - self.width()) // 2,
                     parent.y() + (parent.height() - self.height()) // 2)

    def save_settings(self):
        print("Méthode save_settings appelée")  # Debug
        try:
            is_interpreter = self.interpreter_checkbox.isChecked()
            selected_language = self.language_combo.currentText()
            print(f"Interprète: {is_interpreter}, Langue: {selected_language}")  # Debug
            
            # Mettre à jour l'agent
            if hasattr(self.parent(), 'update_agent_mode'):
                self.parent().update_agent_mode(is_interpreter, selected_language)
                print("Agent mis à jour")  # Debug
                
                # Obtenir la fenêtre principale
                main_window = None
                for widget in QApplication.topLevelWidgets():
                    if isinstance(widget, frame):
                        main_window = widget
                        break
                
                print(f"Fenêtre principale trouvée : {main_window}")  # Debug
                
                if main_window:
                    # Créer la fenêtre de message personnalisée
                    message = f"Le mode interprète a été activé.\nLangue cible : {selected_language}" if is_interpreter else "Le mode conversationnel a été activé."
                    message_window = CustomMessageWindow(main_window, "Modifications enregistrées", message)
                    
                    # Forcer l'affichage de la fenêtre
                    print("Tentative d'affichage de la fenêtre de message")  # Debug
                    message_window.show()
                    message_window.raise_()
                    message_window.activateWindow()
                    
                    # Forcer le traitement des événements
                    QApplication.processEvents()
                    
                    # Retourner à la vue principale
                    if hasattr(self.parent(), 'stacked_widget'):
                        self.parent().stacked_widget.setCurrentWidget(self.parent().scroll_area)
                        print("Retour à la vue principale")  # Debug
                else:
                    print("Fenêtre principale non trouvée")  # Debug
                    
        except Exception as e:
            print(f"Erreur: {str(e)}")  # Debug
            # Afficher une fenêtre d'erreur
            main_window = None
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, frame):
                    main_window = widget
                    break
            
            if main_window:
                error_window = CustomMessageWindow(main_window, "Erreur", f"Une erreur est survenue : {str(e)}")
                error_window.show()
                error_window.raise_()
                error_window.activateWindow()
                QApplication.processEvents()
            else:
                print("Impossible d'afficher la fenêtre d'erreur : fenêtre principale non trouvée")  # Debug

class frame(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.principal = QWidget()
        self.layout_principale = QHBoxLayout()
        self.resize(1000,500)
        self.principal.setLayout(self.layout_principale)
        self.setCentralWidget(self.principal)
        
        # Initialiser l'agent Gemini
        try:
            self.gemini_agent = GeminiAgent()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'initialisation de Gemini : {str(e)}")
            sys.exit(1)
            
        # Initialiser le gestionnaire audio
        self.audio_handler = AudioHandler()
        
        # Liste pour stocker les messages
        self.messages = []
        
        # Créer le widget empilé pour gérer les différentes vues
        self.stacked_widget = QStackedWidget()
        
        self.lato()
        self.centro()
        
        # Centrer l'animation après que la fenêtre est montrée
        QTimer.singleShot(0, self.center_recording_animation)

    def create_demo_frame(self):
        frame = QWidget()
        frame.setStyleSheet("background-color:#1A1B26;")
        layout_frame = QVBoxLayout()
        layout_frame.setSpacing(20)
        layout_frame.setContentsMargins(40, 40, 40, 40)  # Marges plus grandes
        frame.setLayout(layout_frame)

        top = QWidget()
        top.setFixedHeight(50)
        layout_top = QHBoxLayout()
        layout_top.setContentsMargins(0, 0, 0, 0)
        top.setLayout(layout_top)

        logo = QLabel()
        logo.setPixmap(QPixmap(r"C:\Users\farya\Desktop\NLP-20240515T082008Z-001\NLP\AryadAI\AI\logoIA.png").scaled(36,36))

        nameapk = QLabel("AryadAi")
        nameapk.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 24px;
                color: #E2E8F0;
            }
        """)

        plus = QLabel("plus")
        plus.setFixedSize(18,16)
        plus.setStyleSheet("""
            QLabel {
                background-color: #C6C7F8;
                border-radius: 4px;
                color: black;
                padding: 2px;
                font-size: 7px;
                margin-top: 3px;
            }
        """)

        layout_top.addStretch()
        layout_top.addWidget(logo)
        layout_top.addWidget(nameapk)
        layout_top.addWidget(plus)
        layout_top.addStretch()

        bottom = QWidget()
        layout_bottom = QHBoxLayout()
        layout_bottom.setSpacing(40)  # Plus d'espace entre les sections
        bottom.setLayout(layout_bottom)

        # Sections Examples, Capabilities, Limitations
        for section_title, icon_path, items in [
            ("Exemples", "1.png", [
                "Expliquez l'informatique quantique simplement",
                "Des idées créatives pour un anniversaire de 10 ans",
                "Comment faire une requête HTTP en Javascript ?"
            ]),
            ("Capacités", "2.png", [
                "Se souvient des conversations précédentes",
                "Permet les corrections et suivis",
                "Formé pour refuser les demandes inappropriées"
            ]),
            ("Limitations", "3.png", [
                "Peut parfois générer des informations incorrectes",
                "Peut produire du contenu biaisé",
                "Connaissances limitées après 2021"
            ])
        ]:
            section = QWidget()
            section_layout = QVBoxLayout()
            section_layout.setSpacing(15)  # Plus d'espace entre les éléments
            section.setLayout(section_layout)
            
            icon = QLabel()
            icon.setPixmap(QPixmap(fr"C:\Users\farya\Desktop\NLP-20240515T082008Z-001\NLP\AryadAI\AI\{icon_path}").scaled(24,24))
            icon.setStyleSheet("margin-left: 85px;")
            
            title = QLabel(section_title)
            title.setStyleSheet("""
                QLabel {
                    margin-left: 70px;
                    color: #E2E8F0;
                    font-weight: bold;
                    font-size: 16px;
                }
            """)
            
            section_layout.addWidget(icon, alignment=Qt.AlignHCenter)
            section_layout.addWidget(title, alignment=Qt.AlignHCenter)
            
            for item in items:
                box = QWidget()
                box.setStyleSheet("""
                    QWidget {
                        background-color: #2B2D42;
                        border-radius: 8px;
                        padding: 12px;
                        border: 1px solid #3B3D52;
                    }
                """)
                label = QLabel(item)
                label.setWordWrap(True)
                label.setStyleSheet("""
                    QLabel {
                        color: #E2E8F0;
                        font-size: 13px;
                    }
                """)
                box_layout = QVBoxLayout()
                box_layout.setContentsMargins(8,8,8,8)
                box_layout.addWidget(label)
                box.setLayout(box_layout)
                section_layout.addWidget(box)
            
            layout_bottom.addWidget(section)

        layout_frame.addWidget(top)
        layout_frame.addWidget(bottom)
        
        return frame

    def lato(self):
        lateral = QWidget()
        layout_lateral = QVBoxLayout()
        lateral.setLayout(layout_lateral)
        lateral.setFixedWidth(200)
        lateral.setStyleSheet("background-color:#1A1B26;")

        top = QWidget()
        layout_top = QVBoxLayout()
        layout_top.setSpacing(10)
        layout_top.setContentsMargins(10, 10, 10, 10)
        
        btn = QPushButton("+ Nouvelle Discussion")
        btn.setFixedHeight(30)
        btn.setStyleSheet("""
            QPushButton {
                background-color:#C6C7F8;
                border-radius:4px;
                color:black;
                font-weight:bold;
            }
            QPushButton:hover {
                background-color:#B5B6E8;
            }
        """)
        btn.clicked.connect(self.clear_conversations)

        info1 = QPushButton("Éthique de l'IA")
        info1.setStyleSheet("""
            QPushButton {
                text-align:left;
                padding:8px;
                border-radius:4px;
                color: #E2E8F0;
            }
            QPushButton:hover {
                background-color:#2B2D42;
            }
        """)
        info1.setIcon(QIcon(QPixmap(r"C:\Users\farya\Desktop\NLP-20240515T082008Z-001\NLP\AryadAI\AI\12.png").scaled(20,20)))

        info2 = QPushButton("Impact de l'IA")
        info2.setStyleSheet("""
            QPushButton {
                text-align:left;
                padding:8px;
                border-radius:4px;
                color: #E2E8F0;
            }
            QPushButton:hover {
                background-color:#2B2D42;
            }
        """)
        info2.setIcon(QIcon(QPixmap(r"C:\Users\farya\Desktop\NLP-20240515T082008Z-001\NLP\AryadAI\AI\12.png").scaled(20,20)))

        info3 = QPushButton("Nouveau chat")
        info3.setStyleSheet("""
            QPushButton {
                text-align:left;
                padding:8px;
                border-radius:4px;
                color: #E2E8F0;
            }
            QPushButton:hover {
                background-color:#2B2D42;
            }
        """)
        info3.setIcon(QIcon(QPixmap(r"C:\Users\farya\Desktop\NLP-20240515T082008Z-001\NLP\AryadAI\AI\12.png").scaled(20,20)))
        info3.clicked.connect(self.clear_conversations)

        layout_top.addWidget(btn)
        layout_top.addWidget(info1)
        layout_top.addWidget(info2)
        layout_top.addWidget(info3)
        layout_top.addStretch()
        top.setLayout(layout_top)

        bottom = QWidget()
        layout_bottom = QVBoxLayout()
        layout_bottom.setSpacing(10)
        layout_bottom.setContentsMargins(10, 10, 10, 10)

        info1_1 = QPushButton("Effacer les conversations")
        info1_1.setStyleSheet("""
            QPushButton {
                text-align:left;
                padding:8px;
                border-radius:4px;
                color: #E2E8F0;
            }
            QPushButton:hover {
                background-color:#2B2D42;
            }
        """)
        info1_1.setIcon(QIcon(QPixmap(r"C:\Users\farya\Desktop\NLP-20240515T082008Z-001\NLP\AryadAI\AI\11.png").scaled(20,20)))
        info1_1.clicked.connect(self.clear_conversations)

        info2_2 = QPushButton("Mode clair")
        info2_2.setStyleSheet("""
            QPushButton {
                text-align:left;
                padding:8px;
                border-radius:4px;
                color: #E2E8F0;
            }
            QPushButton:hover {
                background-color:#2B2D42;
            }
        """)
        info2_2.setIcon(QIcon(QPixmap(r"C:\Users\farya\Desktop\NLP-20240515T082008Z-001\NLP\AryadAI\AI\10.png").scaled(20,20)))

        info3_3 = QPushButton("Mon compte")
        info3_3.setStyleSheet("""
            QPushButton {
                text-align:left;
                padding:8px;
                border-radius:4px;
                color: #E2E8F0;
            }
            QPushButton:hover {
                background-color:#2B2D42;
            }
        """)
        info3_3.setIcon(QIcon(QPixmap(r"C:\Users\farya\Desktop\NLP-20240515T082008Z-001\NLP\AryadAI\AI\9.png").scaled(20,20)))
        info3_3.clicked.connect(self.show_account_settings)

        info4_4 = QPushButton("Mises à jour & FAQ")
        info4_4.setStyleSheet("""
            QPushButton {
                text-align:left;
                padding:8px;
                border-radius:4px;
                color: #E2E8F0;
            }
            QPushButton:hover {
                background-color:#2B2D42;
            }
        """)
        info4_4.setIcon(QIcon(QPixmap(r"C:\Users\farya\Desktop\NLP-20240515T082008Z-001\NLP\AryadAI\AI\8.png").scaled(20,20)))

        info5_5 = QPushButton("Déconnexion")
        info5_5.setStyleSheet("""
            QPushButton {
                text-align:left;
                padding:8px;
                border-radius:4px;
                color: #E2E8F0;
            }
            QPushButton:hover {
                background-color:#2B2D42;
            }
        """)
        info5_5.setIcon(QIcon(QPixmap(r"C:\Users\farya\Desktop\NLP-20240515T082008Z-001\NLP\AryadAI\AI\7.png").scaled(20,20)))
        info5_5.clicked.connect(self.close)

        layout_bottom.addWidget(info1_1)
        layout_bottom.addWidget(info2_2)
        layout_bottom.addWidget(info3_3)
        layout_bottom.addWidget(info4_4)
        layout_bottom.addWidget(info5_5)
        bottom.setLayout(layout_bottom)

        layout_lateral.addWidget(top)
        layout_lateral.addWidget(bottom)
        self.layout_principale.addWidget(lateral)

    def centro(self):
        self.centre_widget = QWidget()
        centre_layout = QVBoxLayout()
        centre_layout.setContentsMargins(0, 0, 0, 0)
        self.centre_widget.setLayout(centre_layout)
        self.centre_widget.setStyleSheet("background-color:#1A1B26;")

        # Créer le widget empilé pour gérer les différentes vues
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background-color:#1A1B26;")

        # Zone de messages avec défilement
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #1A1B26;
            }
            QScrollBar:vertical {
                border: none;
                background: #1A1B26;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #3B3D52;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout()
        self.messages_layout.setSpacing(16)
        self.messages_layout.setContentsMargins(20, 20, 20, 20)
        self.messages_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.messages_widget.setLayout(self.messages_layout)
        self.scroll_area.setWidget(self.messages_widget)
        
        # Vue d'accueil (Exemples, Capacités, Limitations)
        self.demo_frame = self.create_demo_frame()
        
        # Créer la vue des paramètres du compte
        self.account_settings = AccountSettingsWidget(self)
        
        # Ajouter les vues au widget empilé
        self.stacked_widget.addWidget(self.scroll_area)
        self.stacked_widget.addWidget(self.demo_frame)
        self.stacked_widget.addWidget(self.account_settings)
        
        # Ajouter le widget empilé au layout central
        centre_layout.addWidget(self.stacked_widget, 1)

        # Animation d'enregistrement
        self.recording_animation = RecordingAnimation(self.centre_widget)
        self.recording_animation.setFixedSize(200, 50)
        self.recording_animation.hide()
        
        # Zone de saisie message
        frame_message = QWidget()
        frame_message_layout = QHBoxLayout()
        frame_message.setLayout(frame_message_layout)
        frame_message_layout.setContentsMargins(145, 21, 145, 14)
        frame_message_layout.setSpacing(10)

        frame_message.setStyleSheet("""
            QWidget {
                background-color:#1A1B26;
            }
        """)

        frame_message_in = QWidget()
        frame_message_in_layout = QHBoxLayout()
        frame_message_in.setLayout(frame_message_in_layout)
        frame_message_in_layout.setContentsMargins(10, 5, 10, 5)
        frame_message_in_layout.setSpacing(10)
        frame_message_in.setStyleSheet("""
            QWidget {
                border: 1px solid #3B3D52;
                border-radius: 16px;
                background-color: #2B2D42;
            }
        """)
        frame_message_in.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        micro = QPushButton()
        micro.setIcon(QIcon(QPixmap(r"C:\Users\farya\Desktop\NLP-20240515T082008Z-001\NLP\AryadAI\AI\4.png").scaled(20,20)))
        micro.setStyleSheet("""
            QPushButton {
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #565869;
                border-radius: 4px;
            }
        """)
        micro.clicked.connect(self.toggle_recording)

        img = QPushButton()
        img.setIcon(QIcon(QPixmap(r"C:\Users\farya\Desktop\NLP-20240515T082008Z-001\NLP\AryadAI\AI\5.png").scaled(20,20)))
        img.setStyleSheet("""
            QPushButton {
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #565869;
                border-radius: 4px;
            }
        """)
        img.clicked.connect(self.select_image)

        self.saisie = QTextEdit()
        self.saisie.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.saisie.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.saisie.setPlaceholderText("Tapez votre message...")
        self.saisie.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                border: none;
                color: #E2E8F0;
                font-size: 14px;
            }
        """)
        self.saisie.setFixedHeight(35)

        send = QPushButton()
        send.setIcon(QIcon(QPixmap(r"C:\Users\farya\Desktop\NLP-20240515T082008Z-001\NLP\AryadAI\AI\6.png").scaled(20,20)))
        send.setStyleSheet("""
            QPushButton {
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #565869;
                border-radius: 4px;
            }
        """)
        send.clicked.connect(self.send_message)

        frame_message_in_layout.addWidget(micro)
        frame_message_in_layout.addWidget(img)
        frame_message_in_layout.addWidget(self.saisie)
        frame_message_in_layout.addWidget(send)

        frame_message_layout.addStretch()
        frame_message_layout.addWidget(frame_message_in)
        frame_message_layout.addStretch()

        centre_layout.addWidget(frame_message)

        # Afficher la vue d'accueil au démarrage
        self.stacked_widget.setCurrentWidget(self.demo_frame)

        self.layout_principale.addWidget(self.centre_widget)

    def center_recording_animation(self):
        # Calculer la position centrée basée sur la taille actuelle du widget central
        if self.centre_widget is not None:
            animation_width = self.recording_animation.width()
            animation_height = self.recording_animation.height()
            
            centre_rect = self.centre_widget.geometry()
            centre_width = centre_rect.width()
            centre_height = centre_rect.height()

            x_pos = (centre_width - animation_width) // 2
            y_pos = (centre_height - animation_height) // 2
            
            self.recording_animation.move(x_pos, y_pos)

    def toggle_recording(self):
        if self.demo_frame.isVisible():
            self.demo_frame.hide()
            self.scroll_area.show()
            
        if self.recording_animation.isVisible():
            self.recording_animation.stop()
            # Arrêter l'enregistrement
            self.audio_handler.stop_recording()
            # L'audio sera traité quand l'utilisateur clique sur send
        else:
            self.center_recording_animation()
            self.recording_animation.set_audio_handler(self.audio_handler)
            self.audio_handler.start_recording()
            self.recording_animation.start()

    def select_image(self):
         # Masquer la vue d'accueil et afficher la zone de chat si c'est la première interaction avec l'image
        if self.demo_frame.isVisible():
            self.demo_frame.hide()
            self.scroll_area.show()
            
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner une image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_name:
            self.add_message(f"Image sélectionnée : {file_name}", True)

    def send_message(self):
        message = self.saisie.toPlainText().strip()
        if message or self.audio_handler.recording:
            if self.demo_frame.isVisible():
                self.demo_frame.hide()
                self.scroll_area.show()

            if self.audio_handler.recording:
                # Arrêter l'enregistrement et l'animation
                self.recording_animation.stop()
                transcribed_text = self.audio_handler.stop_recording()
                if transcribed_text and transcribed_text != "Aucun audio enregistré":
                    # Ajouter le message transcrit
                    self.add_message(transcribed_text, True)
                    # Obtenir la réponse de Gemini
                    self.get_gemini_response(transcribed_text, None)
            elif message:
                # Traitement normal du message texte
                self.add_message(message, True)
                self.saisie.clear()
                
                # Ajouter l'indicateur de frappe
                self.typing_indicator = TypingIndicator()
                indicator_container = QWidget()
                indicator_layout = QHBoxLayout()
                indicator_layout.setContentsMargins(0, 0, 0, 0)
                indicator_container.setLayout(indicator_layout)
                indicator_layout.addWidget(self.typing_indicator)
                indicator_layout.addStretch()
                self.messages_layout.addWidget(indicator_container)
                
                QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
                    self.scroll_area.verticalScrollBar().maximum()
                ))

                typing_indicator_ref = indicator_container
                QTimer.singleShot(100, lambda: self.get_gemini_response(message, typing_indicator_ref))

    def get_gemini_response(self, message, typing_indicator_widget):
        if typing_indicator_widget:
            # Retirer l'indicateur de frappe
            if typing_indicator_widget in self.messages_layout.children():
                typing_indicator = typing_indicator_widget.findChild(TypingIndicator)
                if typing_indicator:
                    typing_indicator.timer.stop()
                QTimer.singleShot(0, lambda: self.messages_layout.removeWidget(typing_indicator_widget))
                QTimer.singleShot(0, typing_indicator_widget.deleteLater)

        # Obtenir la réponse de Gemini
        ai_response_text = self.gemini_agent.get_response(message)
        
        # Ajouter le TypingLabel et démarrer l'animation
        ai_message_widget = QWidget()
        ai_message_layout = QHBoxLayout()
        ai_message_layout.setContentsMargins(0, 0, 0, 0)
        ai_message_widget.setLayout(ai_message_layout)
        
        typing_label = TypingLabel(ai_response_text)
        ai_message_layout.addWidget(typing_label)
        ai_message_layout.addStretch()
        
        self.messages_layout.addWidget(ai_message_widget)
        typing_label.start_typing(interval=30)

        # Afficher l'animation pendant la synthèse vocale
        self.recording_animation.start()
        
        # Déterminer la langue pour la synthèse vocale
        target_language = 'Français'  # Langue par défaut
        if hasattr(self.gemini_agent, 'interpreter_chain') and self.gemini_agent.interpreter_chain:
            # Si on est en mode interprète, utiliser la langue cible
            target_language = self.account_settings.language_combo.currentText()
        
        # Synthétiser la réponse en parole avec la langue appropriée
        def on_synthesis_complete():
            self.recording_animation.stop()
            
        self.audio_handler.speak(ai_response_text, language=target_language, callback=on_synthesis_complete)

        # Faire défiler vers le bas pendant l'animation de frappe
        QTimer.singleShot(len(ai_response_text) * typing_label._timer.interval() + 200, 
                         lambda: self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum()))

    def add_message(self, text, is_user):
        # Cette fonction est maintenant principalement pour les messages utilisateur ou les messages système simples
        # La réponse de l'IA avec animation est gérée séparément dans get_gemini_response
        if is_user or "Enregistrement" in text or "Image sélectionnée" in text:
            message_widget = MessageWidget(text, is_user)
            self.messages_layout.addWidget(message_widget)
            
            # Animation d'apparition (peut être conservée ou modifiée)
            # Pour les messages courts comme l'enregistrement terminé ou l'image sélectionnée, on peut désactiver l'animation si désiré.
            # message_widget.setMaximumHeight(0)
            # animation = QPropertyAnimation(message_widget, b"maximumHeight")
            # animation.setDuration(300)
            # animation.setStartValue(0)
            # animation.setEndValue(message_widget.sizeHint().height())
            # animation.setEasingCurve(QEasingCurve.OutCubic)
            # animation.start()
            
            # Faire défiler vers le bas
            QTimer.singleShot(100, lambda: self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().maximum()
            ))
        # Les messages de l'IA (is_user=False pour la réponse simulée) ne sont plus ajoutés ici directement

    def resizeEvent(self, event):
        # Recalculer la position de l'animation lorsque la fenêtre est redimensionnée
        self.center_recording_animation()
        super().resizeEvent(event)

    def show_account_settings(self):
        """Affiche la vue des paramètres du compte"""
        self.stacked_widget.setCurrentWidget(self.account_settings)

    def clear_conversations(self):
        """Efface toutes les conversations"""
        # Supprimer tous les widgets du layout des messages
        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Réinitialiser la liste des messages
        self.messages = []
        
        # Afficher la vue d'accueil
        self.stacked_widget.setCurrentWidget(self.demo_frame)

    def update_agent_mode(self, is_interpreter, target_language):
        """Met à jour le mode de l'agent (interprète ou conversationnel)"""
        print("Mise à jour du mode de l'agent")  # Debug
        try:
            if is_interpreter:
                print(f"Activation du mode interprète pour la langue : {target_language}")  # Debug
                # Mettre à jour le prompt de l'agent pour l'interprétation
                self.gemini_agent.update_prompt_for_interpreter(target_language)
            else:
                print("Activation du mode conversationnel")  # Debug
                # Restaurer le prompt normal de conversation
                self.gemini_agent.restore_normal_prompt()
            print("Mode de l'agent mis à jour avec succès")  # Debug
        except Exception as e:
            print(f"Erreur lors de la mise à jour du mode de l'agent : {str(e)}")  # Debug
            raise e

if __name__=="__main__":
    apk = QApplication(sys.argv)
    fenetre = frame()
    fenetre.show()
    sys.exit(apk.exec())






