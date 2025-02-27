import gtts
import pygame
import tempfile
import numpy as np
import os

class TextToSpeech:
    """Handles text-to-speech functionality using gTTS and Pygame mixer"""
    def __init__(self, config):
        self.config = config

    def speak(self, text, ui_callback=None):
        if not text:
            return
        try:
            tts = gtts.gTTS(text=text, lang='en')
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            temp_file.close()
            tts.save(temp_file.name)
            pygame.mixer.music.load(temp_file.name)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                if ui_callback:
                    ui_callback(np.zeros(1024, dtype=np.float32))
                pygame.time.Clock().tick(10)
            os.remove(temp_file.name)
        except Exception as e:
            print(f"Error during speech generation or playback: {e}")

    def stop(self):
        pygame.mixer.music.stop()
