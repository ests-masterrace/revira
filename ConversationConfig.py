from dataclasses import dataclass


@dataclass
class ConversationConfig:
    system_prompt: str = """
        You are EduTalk, an educational AI assistant.
        Provide concise, helpful answers to support students in their learning.
        Focus on explaining concepts clearly.
    """
    max_context_length: int = 4096
