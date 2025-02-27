from dataclasses import dataclass

@dataclass
class MessagesConfig:
    welcome: str = "Welcome to EduTalk, your AI voice assistant for learning. Press space to start speaking."
    loading: str = "Loading models. Please wait a moment..."
    ready: str = "Ready! Press space to speak and release when done."
    processing: str = "Processing your question..."
    no_audio: str = "No speech detected. Please try again."
    error_model: str = "Error loading model. Please check your installation."
    error_api: str = "Couldn't connect to the language model. Is Ollama running?"
    exit_message: str = "Thank you for using EduTalk. Goodbye!"
    flashcard_created: str = "Flashcard created for {}"
