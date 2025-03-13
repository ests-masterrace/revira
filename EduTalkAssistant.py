from EduTalkUI import EduTalkUI

# from ConfigLoader import ConfigLoader
from AudioHandler import AudioHandler
from SpeechRecognizer import SpeechRecognizer
from OllamaConnector import OllamaConnector
from TextToSpeech import TextToSpeech

from ConfigParser import ConfigParser

import chromadb
from rag.rag import (
    EMBED_MODEL,
    read_txtf,
    read_pdf,
    read_png,
    chunk_splitter,
    get_embedding,
)

import time
import requests
import re
import threading
import pygame
import tkinter as tk
from tkinter import filedialog
import ollama

CONFIG_FILEPATH = "config.toml"

AUDIO_CONFIG: dict[str, int] = {
    "CHANNELS": 1,
    "RATE": 16000,
    "CHUNK": 512,  # Reduced chunk size for lower latency
}


# Main Assistant Class
class EduTalkAssistant:
    """Main class coordinating all components"""

    def __init__(self, config_path=None):
        self.config = ConfigParser(CONFIG_FILEPATH)
        self.config.read_config()
        self.audio_handler = AudioHandler()
        self.ui = EduTalkUI(self.config, self.status_update, self)
        self.speech_recognizer = SpeechRecognizer(self.config)
        self.ollama = OllamaConnector(self.config)
        self.tts = TextToSpeech(self.config)
        self.flashcards = []
        self.is_running = True
        self.is_recording = False
        self.speech_thread = None
        self.has_shutdown = False
        self.tt_data = "No timetable data."

    def status_update(self, message):
        print(f"\t:> {message}")

    def initialize(self):
        self.ui.display_message("Loading speech recognition model...")
        if not self.speech_recognizer.load_model():
            self.ui.display_message(self.config.get_value("messages", "error_model"))
            time.sleep(3)
            return False
        try:
            self.ui.display_message("Testing connection to language model...")
            requests.get(
                self.config.get_value("ollama", "url").replace("/generate", "/"),
                timeout=2,
            )
        except Exception as e:
            print(e)
            self.ui.display_message(self.config.get_value("messages", "error_api"))
            time.sleep(3)
            return False
        self.ui.display_message(self.config.get_value("messages", "ready"))
        return True

    def start_recording(self):
        if not self.is_recording:
            self.is_recording = True
            self.ui.set_recording(True)
            self.audio_handler.start_recording()

    def stop_recording(self):
        if self.is_recording:
            self.is_recording = False
            self.ui.set_recording(False)
            self.ui.display_message(self.config.get_value("messages", "processing"))
            audio_data = self.audio_handler.stop_recording()

            if len(audio_data) < AUDIO_CONFIG["RATE"] * 0.5:
                self.ui.display_message(self.config.get_value("messages", "no_audio"))
                time.sleep(1)
                self.ui.display_message(self.config.get_value("messages", "ready"))
                return

            self.ui.display_message(self.config.get_value("messages", "processing"))
            transcription = self.speech_recognizer.transcribe(audio_data)
            # DEBUG
            # print(f"Transcription result: '{transcription}'")
            if not transcription or transcription.startswith("Error:"):
                self.ui.display_message("Couldn't understand audio")
                time.sleep(2)
                self.ui.display_message(self.config.get_value("messages", "ready"))
                return

            chromaclient = chromadb.HttpClient(host="localhost", port=8000)
            collection = chromaclient.get_or_create_collection(name="user_tt")

            queryembed = ollama.embed(model=EMBED_MODEL, input=transcription)[
                "embeddings"
            ]

            self.tt_data = "\n\n".join(
                collection.query(query_embeddings=queryembed, n_results=10)[
                    "documents"
                ][0]
            )
            self.tt_data = "[Timetable data:\n" + self.tt_data + "]" # TODO: improve RAG
            sys_prompt = self.config.get_value("conversation",  "system_prompt")
            prompt = sys_prompt.replace("<query>", transcription)
            prompt = re.sub(r"\[(.*?)\]", self.tt_data, prompt, count=1)
            self.generate_response(prompt)

    def speak_chunk(self, text_chunk):
        self.ui.set_speaking(True)
        self.ui.display_message(text_chunk)
        self.tts.speak(text_chunk, self.ui.display_waveform)

    def generate_response(self, user_input):
        """Generates a response using the Ollama API."""

        def response_thread():
            self.ui.set_speaking(True)
            full_response = self.ollama.generate_response(user_input, self.speak_chunk)
            self.ui.set_speaking(False)
            self.ui.display_message(full_response)
            time.sleep(1)
            self.ui.display_message(self.config.get_value("messages", "ready"))

        self.speech_thread = threading.Thread(target=response_thread)
        self.speech_thread.daemon = True
        self.speech_thread.start()

    def stop_speaking(self):
        if self.ui.is_speaking:
            self.tts.stop()
            self.ui.set_speaking(False)

    def upload_file(self):
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        file_path = filedialog.askopenfilename(title="Select timetable file...")
        root.destroy()
        return file_path

    def run(self):
        if not self.initialize():
            return
        while self.is_running:
            if self.is_recording:
                audio_frame = self.audio_handler.process_frame()
                self.ui.display_waveform(audio_frame)
            action = self.ui.update()
            if action == "quit":
                self.shutdown()
                break
            elif action == "start_recording":
                self.start_recording()
            elif action == "stop_recording":
                self.stop_recording()
            elif action == "stop_speaking":
                self.stop_speaking()
            elif action == "upload_file":
                print("Upload img/pdf file...")
                path = self.upload_file()
                if path:
                    print(f">>>> Selected file: {path}")
                    if path:  # TODO: Make a separate function
                        chromaclient = chromadb.HttpClient(host="localhost", port=8000)
                        text_content = ""
                        if path.endswith(".pdf"):
                            text_content = read_pdf(path)
                        elif path.endswith(".txt"):
                            text_content = read_txtf(path)
                        # elif path.endswith(".png"):
                        #     text_content = read_png(path)
                        else:
                            print(">>>> Selected file is not supported.")
                            print(">>>>\tSupported filetypes are: PDF, PNG, TXT.")

                        if text_content:
                            # collection = chromaclient.get_or_create_collection(
                            #     name="user_tt",
                            #     metadata={"hnsw:space": "cosine"},
                            # )
                            # if any(
                            #     coll.name == "user_tt"
                            #     for coll in chromaclient.list_collections()
                            # ):
                            #     chromaclient.delete_collection("user_tt")
                            #     collection = chromaclient.get_or_create_collection(
                            #         name="user_tt",
                            #         metadata={"hnsw:space": "cosine"},
                            #     )

                            collection = chromaclient.get_or_create_collection(
                                name="user_tt",
                                metadata={"hnsw:space": "cosine"},
                            )
                            try:
                                chromaclient.get_collection("user_tt")
                                chromaclient.delete_collection("user_tt")
                                collection = chromaclient.get_or_create_collection(
                                    name="user_tt",
                                    metadata={"hnsw:space": "cosine"},
                                )
                            except ValueError:
                                pass

                            chunks = chunk_splitter(text_content)
                            embeds = get_embedding(chunks)
                            chunknumber = list(range(len(chunks)))
                            ids = [f"tt_{path}_{i}" for i in chunknumber]
                            metadatas = [{"source": path} for _ in chunknumber]

                            collection.add(
                                ids=ids,
                                documents=chunks,
                                embeddings=embeds,
                                metadatas=metadatas,
                            )
                            print(f"embedding the the file: '{path}' with success.")

    def shutdown(self):
        if self.has_shutdown:
            return  # Skip if already shut down
        self.has_shutdown = True  # Mark as shut down
        self.is_running = False
        if hasattr(self, "tts"):
            self.tts.stop()  # Stop text-to-speech
        if hasattr(self, "audio_handler"):
            self.audio_handler.cleanup()  # Clean up audio resources
        pygame.quit()  # Uninitialize Pygame
        print(self.config.get_value("messages", "exit_message"))  # Display exit message
