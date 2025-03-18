from asyncio.windows_events import NULL
import sys
import os
from altair import TimeLocale
import speech_recognition as sr
from pydub import AudioSegment
import deepspeech
import numpy as np
import wave
import pygetwindow as gw
import pyautogui
import time
import threading
import sounddevice as sd
import vosk
import json
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox

MODEL_PATH = "vosk-model-en-us-0.42-gigaspeech"
if not os.path.exists(MODEL_PATH):
    print(f"Model not found at {MODEL_PATH}")
    sys.exit(1)

model = vosk.Model(MODEL_PATH) 

# Setup the recognizer
recognizer = vosk.KaldiRecognizer(model, 16000)
window = NULL
        

def get_focused_window():
    try:
        window = gw.getActiveWindow()
        if window:
            return window.title
        else:
            return None
    except Exception as e:
        print(f"Error retrieving focused window: {e}")
        return None
    
def input_text(text):
    # A small delay to allow the window to be focused
    #time.sleep(0.1)
    pyautogui.typewrite(text)
                    
def detect_focus_field(self):
    while not self.stop_event_input.is_set():
        focused_window = get_focused_window()
        if focused_window:
            #print(f"Focused Window: {focused_window}")
            if self.bRun == 1:
                if self.trans_text != "":
                    input_text(" " + self.trans_text)    
                    self.trans_text = ""                
        time.sleep(0.1)
    
# Callback function that will be executed to read audio chunks
def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
        
    #data = indata.tobytes()
    recognizer.AcceptWaveform(bytes(indata))
    data = recognizer.Result()
    if data:
        result = json.loads(data)
        if 'text' in result:
            print("Recognized:", result['text'])
            window.trans_text = result['text']
            
def livspeech_to_text_vosk(self):
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                        channels=1, callback=callback):
        print("Listening... Press Ctrl+C to stop.")
        
        while not self.stop_event_trans.is_set():
            time.sleep(0.3)
    
class SpeechToTextUI(QtWidgets.QDialog):
    def __init__(self):
        super(SpeechToTextUI, self).__init__()
        uic.loadUi('SpeechToText.ui', self)  # Load the UI file

        self.langCombo.addItem("en_US")
        self.langCombo.addItem("Hindi")
        self.langCombo.setCurrentIndex(0)
        
        self.StartPushButton.clicked.connect(self.on_start_button_clicked)
        self.PausePushButton.clicked.connect(self.on_pause_button_clicked)
        self.StopPushButton.clicked.connect(self.on_stop_button_clicked)
        self.PausePushButton.setEnabled(False)
        self.StopPushButton.setEnabled(False)
        
        self.stop_event_input = threading.Event()
        self.bRun = 0
        self.input_thread = threading.Thread(target=detect_focus_field, args=(self,))
        self.input_thread.start()
        
        self.trans_text = ""
                
        self.stop_event_trans = threading.Event()
        self.trans_thread = threading.Thread(target=livspeech_to_text_vosk, args=(self,))
        self.trans_thread.start()
                
    def closeEvent(self, event):
        # Show a confirmation dialog before closing
        runfalg = self.bRun
        if self.bRun == 1:
            self.bRun = 0
            time.sleep(0.3)
        reply = QMessageBox.question(self, 'Message',
            "Are you sure you want to quit?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.stop_event_input.set()
            self.input_thread.join()
            self.stop_event_trans.set()
            self.trans_thread.join()  
            event.accept()  # Close the window
        else:
            event.ignore()  # Ignore the close event
            self.bRun = runfalg
                    
    def on_start_button_clicked(self):
        self.bRun = 1
        self.StartPushButton.setEnabled(False)
        self.PausePushButton.setEnabled(True)
        self.StopPushButton.setEnabled(True)        
        print("Start button clicked")
    def on_pause_button_clicked(self):
        self.bRun = 0
        self.StartPushButton.setEnabled(True)
        self.PausePushButton.setEnabled(False)
        self.StopPushButton.setEnabled(True)      
        print("Pause button clicked")
    def on_stop_button_clicked(self):
        self.bRun = 0
        self.StartPushButton.setEnabled(True)
        self.PausePushButton.setEnabled(True)
        self.StopPushButton.setEnabled(False)        
        print("Stop button clicked")
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SpeechToTextUI()
    window.show()
    sys.exit(app.exec_())
