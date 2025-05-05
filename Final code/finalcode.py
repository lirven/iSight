import google.generativeai as genai
import os
import time
import subprocess
from PIL import Image
from picamera2 import Picamera2
from gpiozero import Button
from signal import pause
import pyaudio
import wave
from vosk import Model, KaldiRecognizer, SetLogLevel
from threading import Lock

# --- Vosk setup ---
SetLogLevel(0)
vosk_model = Model(lang="en-us")
recognizer = KaldiRecognizer(vosk_model, 16000)

# --- Button setup with debounce ---
button = Button(17, bounce_time=0.1)  # 100ms debounce

# --- Gemini setup ---
#genai.configure(api_key="")
genai.configure(api_key="")
model = genai.GenerativeModel(
    "models/gemini-2.0-pro-exp-02-05",
    system_instruction=(
        """
        ---Core Identity
        - You are iSight, a wearable assistive device created by Luke Irven
        - Primary function: Environmental interpretation & hazard navigation for visually impaired users
        - Operation mode: chest-mounted (default) or manual positioning (handheld)
        -  Answer as concisely and accurately as possible to help the user as best as possible
        - If the Prompt is blank, just provide an extremely brief description of the scene in-front of you, or warn of any hazard, whichever is more suitable
        - only ask the user to repeat their question if it does not make sense, if it is blank just do a safety assessment

        ---Response Protocols
        1. Safety Assessment:
           - Immediate hazards (<0.5m): "Stop! [object] directly ahead"
           - Navigable obstacles: "Safe path: [action] to avoid [object]" (e.g., "Step left 20cm")
           - Environmental notes: "Aware: [feature] at [distance]" (e.g., "Door ajar 2m ahead")

        2. Navigation Formatting:
        {
        "action": "[specific movement]",
        "direction": "[clock-face/degrees]",
        "distance": "[metric units]",
        }

        3. Uncertainty Handling:
        - Image quality <60%: "View obscured. Please reposition device"
        
        
        ---Ethical Constraints
        - Privacy: Never describe human faces/identifiable features
        - Safety: Prioritize obstacle avoidance over curiosity-driven observations
        - certainty:If you are asked if it is safe to move forwards,
          you must answer with either Yes or No,
          you cannot be indecisive or unsure
          if there is an object but it is further away, tell them how mnay steps forward they can take
         
         
        """
    ),
)

# --- Camera setup ---
picam2 = Picamera2()
camera_config = picam2.create_preview_configuration()
picam2.configure(camera_config)

# --- Thread lock for recording ---
recording_lock = Lock()

def speak(text):
    subprocess.run(["espeak", "-ven+f3", "-k5", "-s150", text])

def record_audio():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    WAVE_OUTPUT_FILENAME = "output.wav"

    audio = None
    stream = None
    try:
        audio = pyaudio.PyAudio()
        stream = audio.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            input=True,
                            frames_per_buffer=CHUNK)

        frames = []
        print("Recording...")
        while button.is_pressed:
            data = stream.read(CHUNK)
            frames.append(data)

        print("Recording stopped.")

        # Save recording to file
        waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        waveFile.setnchannels(CHANNELS)
        waveFile.setsampwidth(audio.get_sample_size(FORMAT))
        waveFile.setframerate(RATE)
        waveFile.writeframes(b''.join(frames))
        waveFile.close()

        return WAVE_OUTPUT_FILENAME

    finally:
        if stream is not None:
            stream.stop_stream()
            stream.close()
        if audio is not None:
            audio.terminate()
        time.sleep(0.5)  # Let audio hardware reset

def speech_to_text(wav_file):
    wf = wave.open(wav_file, "rb")
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
        print("Audio file must be WAV format mono PCM.")
        return ""

    rec = KaldiRecognizer(vosk_model, wf.getframerate())
    rec.SetWords(True)
    rec.SetPartialWords(True)

    results = []
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            results.append(rec.Result())
        else:
            results.append(rec.PartialResult())

    results.append(rec.FinalResult())
    return '\n'.join([r for r in results if r])

def button_pressed():
    if not recording_lock.acquire(blocking=False):
        print("Recording already in progress. Ignoring button press.")
        return
    try:
        #Record audio while button is pressed
        wav_file = record_audio()

        #Take a photo
        picam2.start()
        time.sleep(2)
        file_path = os.path.expanduser("~/Pictures/PhotoToTest.jpg")
        picam2.capture_file(file_path)
        picam2.stop()
        print(f"Photo saved as {file_path}")

        #Convert speech to text
        prompt = speech_to_text(wav_file)
        print(f"Prompt: {prompt}")

        #Generate content using the prompt and image
        image1 = Image.open(file_path)
        response = model.generate_content([prompt, image1])
        print(response.text)
        speak(response.text)
    finally:
        recording_lock.release()

button.when_pressed = button_pressed
print("Press the button to start. Press CTRL-C to exit.")
pause()
