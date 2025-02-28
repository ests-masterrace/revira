from dataclasses import dataclass, field


@dataclass
class OllamaConfig:
    url: str = "http://localhost:11434/api/generate"
    model: str = "deepseek-r1:1.5b"
    headers: dict = field(default_factory=lambda: {"Content-Type": "application/json"})
