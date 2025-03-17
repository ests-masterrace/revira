from EduTalkUI import EduTalkUI

# from ConfigLoader import ConfigLoader
from AudioHandler import AudioHandler
from SpeechRecognizer import SpeechRecognizer
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

import re
import pygame
import tkinter as tk
from tkinter import filedialog
from ollama import embed, chat, Client
# TODO: add text mode

# MAIN
# window loop
# WHEN SPACE is pressed:  start recording
# WHEN SPACE is released: stop  recording
#                     AND start transcribing
# WHEN transcribing is done: use ollama api to run the MODEL
# WHEN the MODEL's reponse is back, USE TTS to make it an audio
#                                   AND then run the audio

CONFIG_FILEPATH = "config.toml"


def main():
    config = ConfigParser(CONFIG_FILEPATH)
    config.read_config()
    ui = EduTalkUI(config)
    audio = AudioHandler()
    stt = SpeechRecognizer(config)
    tts = TextToSpeech(config)

    ollama_client = Client(host="http://localhost:11434")

    modelname = config.get_value("ollama", "model")

    is_running = True
    is_recording = False

    ui.display_message("Loading speech recognition model...")
    if not stt.load_model():
        ui.display_message(config.get_value("messages", "error_model"))
    ui.display_message(config.get_value("messages", "ready"))

    while is_running:
        if is_recording:
            audio_frame = audio.process_frame()
            ui.display_waveform(audio_frame)
        action = ui.update()
        if action == "quit":
            is_running = False
            break
        elif action == "start_recording":
            is_recording = True
            audio.start_recording()
        elif action == "stop_recording":
            ui.set_recording(False)
            ui.display_message(config.get_value("messages", "processing"))
            audio_data = audio.stop_recording()
            # TODO: handle no audio input
            ui.display_message(config.get_value("messages", "processing"))
            transcription = stt.transcribe(audio_data)

            print(f"Transcription result: '{transcription}'")
            if not transcription or transcription.startswith("Error:"):
                ui.display_message("Couldn't understand audio")
                ui.display_message(config.get_value("messages", "ready"))
                continue

            chromaclient = chromadb.HttpClient(host="localhost", port=8000)
            collection = chromaclient.get_or_create_collection(name="user_tt")

            queryembed = embed(model=EMBED_MODEL, input=transcription)["embeddings"]

            tt_data = "\n\n".join(
                collection.query(query_embeddings=queryembed, n_results=10)[
                    "documents"
                ][0]
            )
            tt_data = "[Timetable data:\n" + tt_data + "]"  # TODO: improve RAG
            sys_prompt = config.get_value("conversation", "system_prompt")
            prompt = sys_prompt.replace("<query>", transcription)
            prompt = re.sub(r"\[(.*?)\]", tt_data, prompt, count=1)
            print("\n\n")

            print(prompt, end="\n\n")

            stream = ollama_client.chat(
                model=modelname,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )

            in_think = False
            for chunk in stream:
                token = chunk["message"]["content"]

            if "<think>" in token:
                in_think = True  # Start ignoring tokens
                continue
            if "</think>" in token:
                in_think = False  # Stop ignoring tokens
                continue

            if not in_think:  # Only append if not in <think> mode
                print(token, end="", flush=True)
                tts.speak(token.encode("ascii", "ignore").decode())

        elif action == "stop_speaking":
            tts.stop()
            ui.set_speaking(False)
        elif action == "upload_file":
            print("Upload img/pdf file...")
            root = tk.Tk()
            root.withdraw()
            path = filedialog.askopenfilename(title="Select timetable file...")
            root.destroy()
            if path:
                print(f">>>> Selected file: {path}")
                if path:  # TODO: Make a separate function
                    chromaclient = chromadb.HttpClient(host="localhost", port=8000)
                    text_content = ""
                    if path.endswith(".pdf"):
                        text_content = read_pdf(path)
                    elif path.endswith(".txt"):
                        text_content = read_txtf(path)
                    elif path.endswith(".png"):
                        text_content = read_png(path)
                    else:
                        print(">>>> Selected file is not supported.")
                        print(">>>>\tSupported filetypes are: PDF, PNG, TXT.")

                    if text_content:
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
    pygame.quit()


if __name__ == "__main__":
    main()
