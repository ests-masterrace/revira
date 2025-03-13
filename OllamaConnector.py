import requests
import json


class OllamaConnector:
    """Handles communication with the Ollama API"""

    def __init__(self, config):
        self.config = config
        self.context = []

    def generate_response(self, prompt, callback=None):
        try:
            if not prompt.strip():
                return "I couldn't hear anything. Please try again."
            payload = {
                "model": self.config.get_value("ollama", "model"),
                "stream": True,
                "context": self.context,
                "prompt": prompt,
                # "system": self.config.conversation.system_prompt,
            }
            response = requests.post(
                self.config.get_value("ollama", "url"),
                json=payload,
                headers=self.config.get_value("ollama", "headers"),
                stream=True,
            )
            response.raise_for_status()
            full_response = ""
            sentence_buffer = ""

            in_think = False
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    body = json.loads(line)
                    token = body.get("response", "")

                    # Check if we are inside a <think> block
                    if "<think>" in token:
                        in_think = True  # Start ignoring tokens
                        continue
                    if "</think>" in token:
                        in_think = False  # Stop ignoring tokens
                        continue

                    if not in_think:  # Only append if not in <think> mode
                        sentence_buffer += token
                        full_response += token

                    if token in [".", "!", "?", ":"]: # TODO: ignore emojies
                        if callback and sentence_buffer:
                            callback(sentence_buffer)
                            sentence_buffer = ""
                    if "context" in body:
                        self.context = body["context"]
                    if body.get("done", False) and sentence_buffer:
                        if callback:
                            callback(sentence_buffer)
                except json.JSONDecodeError:
                    continue
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to Ollama API: {e}")
            return "I'm having trouble connecting to my language model."
