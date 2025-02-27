from EduTalkUI import EduTalkUI
from ConfigLoader import ConfigLoader
from AudioHandler import AudioHandler
from SpeechRecognizer import SpeechRecognizer
from OllamaConnector import OllamaConnector
from TextToSpeech import TextToSpeech

import time
import requests
import re
import threading
import pygame

AUDIO_CONFIG = {
    "CHANNELS": 1,
    "RATE": 16000,
    "CHUNK": 512  # Reduced chunk size for lower latency
}

# Main Assistant Class
class EduTalkAssistant:
    """Main class coordinating all components"""
    def __init__(self, config_path=None):
        self.config = ConfigLoader.load(config_path)
        self.audio_handler = AudioHandler()
        self.ui = EduTalkUI(self.config, self.status_update, self)
        self.speech_recognizer = SpeechRecognizer(self.config)
        self.ollama = OllamaConnector(self.config)
        self.tts = TextToSpeech(self.config)
        self.flashcards = []
        self.is_running = True
        self.is_recording = False
        self.speech_thread = None
        self.has_shutdown = False

    def status_update(self, message):
        print(f"\t:> {message}")

    def initialize(self):
        self.ui.display_message("Loading speech recognition model...")
        if not self.speech_recognizer.load_model():
            self.ui.display_message(self.config.messages.error_model)
            time.sleep(3)
            return False
        try:
            self.ui.display_message("Testing connection to language model...")
            requests.get(self.config.ollama.url.replace("/generate", "/"), timeout=2)
        except Exception as e:
            print(e)
            self.ui.display_message(self.config.messages.error_api)
            time.sleep(3)
            return False
        self.ui.display_message(self.config.messages.ready)
        return True

    def start_recording(self):
        if not self.is_recording:
            self.is_recording = True
            self.ui.set_recording(True)
            self.audio_handler.start_recording()


    def stop_recording(self):
        if self.is_recording:
            self.is_recording = False
            self.ui.set_recording(False)
            self.ui.display_message(self.config.messages.processing)
            audio_data = self.audio_handler.stop_recording()
            
            if len(audio_data) < AUDIO_CONFIG["RATE"] * 0.5:
                self.ui.display_message(self.config.messages.no_audio)
                time.sleep(1)
                self.ui.display_message(self.config.messages.ready)
                return
            
            self.ui.display_message(self.config.messages.processing)
            transcription = self.speech_recognizer.transcribe(audio_data)
            print(f"Transcription result: '{transcription}'")  # Debug output
            if not transcription or transcription.startswith("Error:"):
                self.ui.display_message("Couldn't understand audio")
                time.sleep(2)
                self.ui.display_message(self.config.messages.ready)
                return
            self.generate_response(transcription)

    def speak_chunk(self, text_chunk):
        self.ui.set_speaking(True)
        self.ui.display_message(text_chunk)
        self.tts.speak(text_chunk, self.ui.display_waveform)


    def generate_response(self, user_input):
        """Generates a response using the Ollama API."""

        def response_thread():
            self.ui.set_speaking(True)

            full_response = self.ollama.generate_response(user_input, self.speak_chunk)
            full_response = re.sub(
                r"<think>.*?</think>",
                "",
                full_response,
                flags=re.DOTALL
            ) # rm the <think> part if exists

            print(full_response)

            self.ui.set_speaking(False)
            self.ui.display_message(full_response)
            time.sleep(1)
            self.ui.display_message(self.config.messages.ready)

        self.speech_thread = threading.Thread(target=response_thread)
        self.speech_thread.daemon = True
        self.speech_thread.start()

    
    def stop_speaking(self):
        if self.ui.is_speaking:
            self.tts.stop()
            self.ui.set_speaking(False)

    def run(self):
        if not self.initialize():
            return
        while self.is_running:
            if self.is_recording:
                audio_frame = self.audio_handler.process_frame()
                self.ui.display_waveform(audio_frame)
            action = self.ui.update()
            if action == "quit":
                self.shutdown()
                break
            elif action == "start_recording":
                self.start_recording()
            elif action == "stop_recording":
                self.stop_recording()
            elif action == "stop_speaking":
                self.stop_speaking()

    def shutdown(self):
        if self.has_shutdown:
            return  # Skip if already shut down
        self.has_shutdown = True  # Mark as shut down
        self.is_running = False
        if hasattr(self, 'tts'):
            self.tts.stop()  # Stop text-to-speech
        if hasattr(self, 'audio_handler'):
            self.audio_handler.cleanup()  # Clean up audio resources
        pygame.quit()  # Uninitialize Pygame
        print(self.config.messages.exit_message)  # Display exit message
