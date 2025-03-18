import sys
import os
import queue
import threading
import torch
import torchaudio
from vosk import Model, KaldiRecognizer
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QPushButton, QVBoxLayout, QWidget, QFileDialog

# Ensure the model path is correct
MODEL_PATH = "path_to_vosk_model_en_us_0.42_gigaspeech"
if not os.path.exists(MODEL_PATH):
    print(f"Model path {MODEL_PATH} does not exist.")
    sys.exit(1)

# Initialize the Vosk model
model = Model(MODEL_PATH)
rec = KaldiRecognizer(model, 16000)

# Queue for audio data
audio_queue = queue.Queue()

def audio_callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    audio_queue.put(bytes(indata))

def recognize_audio():
    """Recognize speech from the audio queue."""
    while True:
        data = audio_queue.get()
        if rec.AcceptWaveform(data):
            result = rec.Result()
            print(result)
            text_edit.append(result)

class SpeechToTextApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Speech to Text")
        self.setGeometry(100, 100, 400, 300)

        # Create a text edit to display the recognized text
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)

        # Create a button to start/stop recording
        self.record_button = QPushButton("Start Recording", self)
        self.record_button.clicked.connect(self.toggle_recording)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        layout.addWidget(self.record_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Audio stream
        self.stream = None
        self.recording = False

    def toggle_recording(self):
        if self.recording:
            self.record_button.setText("Start Recording")
            self.stream.stop_stream()
            self.stream.close()
            self.recording = False
        else:
            self.record_button.setText("Stop Recording")
            self.stream = torchaudio.io.StreamReader(
                src="default",
                format="pulse",
                buffer_size=1024,
                sample_rate=16000,
                num_channels=1,
            )
            self.stream.add_audio_callback(audio_callback)
            self.stream.start()
            self.recording = True

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = SpeechToTextApp()
    ex.show()

    # Start the recognition thread
    recognition_thread = threading.Thread(target=recognize_audio)
    recognition_thread.daemon = True
    recognition_thread.start()

    sys.exit(app.exec_())