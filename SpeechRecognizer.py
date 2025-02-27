import whisper

# Supporting Classes
class SpeechRecognizer:
    """Handles speech recognition using Whisper"""
    def __init__(self, config):
        self.config = config
        self.model = None

    def load_model(self):
        try:
            self.model = whisper.load_model(self.config.whisper.model_path)
            return True
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            return False

    def transcribe(self, audio_data):
        if self.model is None:
            return "Error: Model not loaded"
        try:
            transcript = self.model.transcribe(
                audio_data,
                language=self.config.whisper.lang,
                fp16=self.config.whisper.use_fp16
            )
            return transcript["text"].strip()
        except Exception as e:
            print(f"Error during transcription: {e}")
            return f"Error: {str(e)}"
