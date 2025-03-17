import gtts
import pygame
import tempfile
import numpy as np
import os
from pydub import AudioSegment


class TextToSpeech:
    """Handles text-to-speech functionality using gTTS and Pygame mixer"""

    def __init__(self, config):
        self.config = config
        pygame.mixer.init()

    def speak(self, text, speed=1.0, ui_callback=None):
        pygame.mixer.init()
        if not text:
            return
        try:
            tts = gtts.gTTS(text=text, lang="en")
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            temp_file.close()
            tts.save(temp_file.name)

            # Load audio with pydub
            audio = AudioSegment.from_file(temp_file.name)
            new_frame_rate = int(audio.frame_rate * speed)  # Adjust speed
            audio = audio._spawn(
                audio.raw_data, overrides={"frame_rate": new_frame_rate}
            )
            audio = audio.set_frame_rate(44100)  # Standard playback rate

            # Save modified audio
            modified_temp_file = tempfile.NamedTemporaryFile(
                delete=False, suffix=".mp3"
            )
            audio.export(modified_temp_file.name, format="mp3")

            # pygame.mixer.music.load(temp_file.name)
            pygame.mixer.music.load(modified_temp_file.name)  # Load modified audio
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                if ui_callback:
                    ui_callback(np.zeros(1024, dtype=np.float32))
                pygame.time.Clock().tick(10)
            os.remove(temp_file.name)  # Remove original
            os.remove(modified_temp_file.name)  # Remove modified file

        except Exception as e:
            print(f"Error during speech generation or playback: {e}")

    def stop(self):
        pygame.mixer.music.stop()
