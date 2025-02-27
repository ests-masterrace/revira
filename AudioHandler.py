import sounddevice as sd
import numpy as np

AUDIO_CONFIG = {
    "CHANNELS": 1,
    "RATE": 16000,
    "CHUNK": 512  # Reduced chunk size for lower latency
}


class AudioHandler:
    """Handles audio recording using sounddevice"""
    def __init__(self):
        self.frames = []
        self.latest_frame = None
        self.stream = None
        self.dtype = 'int16'
        self.channels = AUDIO_CONFIG["CHANNELS"]
        self.rate = AUDIO_CONFIG["RATE"]
        self.chunk = AUDIO_CONFIG["CHUNK"]

    def callback(self, indata, frames, time, status):
        if status:
            print(status)
        self.frames.append(indata.copy())
        self.latest_frame = indata.copy()

    def start_recording(self):
        self.frames = []
        self.latest_frame = None
        self.stream = sd.InputStream(
            samplerate=self.rate,
            channels=self.channels,
            dtype=self.dtype,
            blocksize=self.chunk,
            callback=self.callback
        )
        self.stream.start()

    def process_frame(self):
        if self.latest_frame is not None:
            return self.latest_frame.flatten().astype(np.float32) / 32768.0
        else:
            return np.zeros(self.chunk, dtype=np.float32)

    def stop_recording(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        if not self.frames:
            return np.zeros(0, dtype=np.float32)
        audio_data = np.concatenate(self.frames, axis=0).flatten()
        audio_data = audio_data.astype(np.float32) / 32768.0
        self.frames = []
        return audio_data

    def cleanup(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
