import speech_recognition as sr
import pyttsx3
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import tempfile
import os
from queue import Queue
import threading
import wave

class AudioHandler:
    def __init__(self):
        # Initialiser le recognizer avec des paramètres optimisés
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8

        # Initialiser le moteur de synthèse vocale
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        self.engine.setProperty('volume', 1.0)

        # Configuration des voix par langue
        self.voices = {}
        self.setup_voices()

        # Configuration de l'enregistrement
        self.sample_rate = 44100
        self.channels = 1
        self.recording = False
        self.audio_queue = Queue()
        self.audio_buffer = []

    def setup_voices(self):
        """Configure les voix disponibles pour chaque langue"""
        voices = self.engine.getProperty('voices')
        self.voices = {}
        
        for voice in voices:
            voice_id = voice.id.lower()
            if "hortense" in voice_id and "fr" in voice_id:
                self.voices['Français'] = voice.id
            elif "zira" in voice_id and "en" in voice_id:
                self.voices['Anglais'] = voice.id
            elif "helena" in voice_id and "es" in voice_id:
                self.voices['Espagnol'] = voice.id
            elif "arabic" in voice_id or "ar" in voice_id:
                self.voices['Arabe'] = voice.id
            elif "russian" in voice_id or "ru" in voice_id:
                self.voices['Russe'] = voice.id

        # Voix par défaut si aucune spécifique trouvée
        default_voice = voices[0].id if voices else None
        for lang in ['Français', 'Anglais', 'Espagnol', 'Arabe', 'Russe']:
            if lang not in self.voices:
                self.voices[lang] = default_voice

    def set_voice_for_language(self, language):
        """Change la voix en fonction de la langue"""
        if language in self.voices:
            self.engine.setProperty('voice', self.voices[language])
            print(f"Voix configurée pour la langue : {language}")
        else:
            print(f"Aucune voix spécifique trouvée pour la langue : {language}")

    def start_recording(self):
        """Démarre l'enregistrement audio"""
        self.recording = True
        self.audio_buffer = []

        def callback(indata, frames, time, status):
            if status:
                print(f"Status: {status}")
            if self.recording:
                self.audio_buffer.append(indata.copy())

        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            callback=callback,
            dtype=np.float32
        )
        self.stream.start()

    def stop_recording(self):
        """Arrête l'enregistrement et retourne le texte transcrit"""
        self.recording = False
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()

        if self.audio_buffer:
            audio_data = np.concatenate(self.audio_buffer, axis=0)
            audio_data = np.int16(audio_data * 32767)

            temp_file = None
            try:
                temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                temp_file.close()

                with wave.open(temp_file.name, 'wb') as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(2)
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(audio_data.tobytes())

                with sr.AudioFile(temp_file.name) as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = self.recognizer.record(source)
                    try:
                        text = self.recognizer.recognize_google(
                            audio,
                            language='fr-FR',
                            show_all=False
                        )
                        return text
                    except sr.UnknownValueError:
                        return "Je n'ai pas compris l'audio"
                    except sr.RequestError as e:
                        return f"Erreur de service: {e}"
            finally:
                if temp_file and os.path.exists(temp_file.name):
                    try:
                        os.unlink(temp_file.name)
                    except PermissionError:
                        pass
        return "Aucun audio enregistré"

    def speak(self, text, language='Français', callback=None):
        """Synthétise et joue le texte en parole avec la voix appropriée"""
        def speak_thread():
            self.set_voice_for_language(language)
            self.engine.say(text)
            self.engine.runAndWait()
            if callback:
                callback()

        threading.Thread(target=speak_thread).start()

    def get_audio_level(self):
        """Retourne le niveau audio actuel pour l'animation"""
        if self.recording and self.audio_buffer:
            current_buffer = self.audio_buffer[-1]
            rms = np.sqrt(np.mean(current_buffer ** 2))
            return min(1.0, (rms * 15) ** 0.5)
        return 0.0
