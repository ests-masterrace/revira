from dataclasses import dataclass


# Configuration dataclasses
@dataclass
class WhisperConfig:
    model_path: str = "base"  # tiny
    lang: str = "en"
    use_fp16: bool = False
    device: str = "cpu"  # 'cpu' or 'cuda'
