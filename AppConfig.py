from WhisperConfig import WhisperConfig
from OllamaConfig import OllamaConfig
from TTSConfig import TTSConfig
from MessagesConfig import MessagesConfig
from ConversationConfig import ConversationConfig
from dataclasses import dataclass, field

@dataclass
class AppConfig:
    whisper: WhisperConfig = field(default_factory=WhisperConfig)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    conversation: ConversationConfig = field(default_factory=ConversationConfig)
    messages: MessagesConfig = field(default_factory=MessagesConfig)
