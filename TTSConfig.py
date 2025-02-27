from dataclasses import dataclass

@dataclass
class TTSConfig:
    rate: int = 145
    volume: float = 1.0
    voice_preference: str = "english"
