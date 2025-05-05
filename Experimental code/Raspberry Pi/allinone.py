import google.generativeai as genai
import os
import subprocess
from PIL import Image
from picamera2 import Picamera2
from gpiozero import Button
from signal import pause
import pyaudio
import wave
from vosk import Model, KaldiRecognizer, SetLogLevel

SetLogLevel(0)
vosk_model = Model(lang="en-us")
recognizer = KaldiRecognizer(vosk_model, 16000)
genai.configure(api_key="AIzaSyCc47LHqu3NkRnmoW9cZsS-Iwy5NH8VlMs")
#AIzaSyCc47LHqu3NkRnmoW9cZsS-Iwy5NH8VlMs
#AIzaSyDHZBMD8PmN1RaIMXlC91R6q9SzAgAxI6Y
#model = genai.GenerativeModel(model_name="gemini-2.0-flash-exp")
model = genai.GenerativeModel("models/gemini-2.0-pro-exp-02-05", system_instruction="you are a wearable assistive device (the user could be visually impaired). your name is 'iSight'. your creator is Luke Irven. you see what the user sees. the user will ask questions with an image of what they see. help them as much as possible. If you are asked if it is safe to move forwards, you must answer with either yes or no based on what you(the user) can see, you cannot be indeccisive or unsure, if the answer is no you must say why, only say no if it is impossible to walk forwards, if there is a small obstace you should say it is safe to procede and how to avoid the obstacle. if the prompt is blank or unclear, ask for specific clarification. Answer as consisly and accuratly as possible",)
button = Button(17)
picam2 = Picamera2()
camera_config = picam2.create_preview_configuration()
picam2.configure(camera_config)

def speak(text):
    subprocess.run(["espeak", "-ven+f3", "-k5", "-s150", text])# english (female no.3), capitilised 5 rise pich, 150 words per min

def record_audio():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    RECORD_SECONDS = 0
    WAVE_OUTPUT_FILENAME = "output.wav"
    #start recording 
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT,channels=CHANNELS,
                        rate=RATE, input=True, 
                        frames_per_buffer=CHUNK)
    frames = []
    print("Recording")
    while button.is_pressed:
        data = stream.read(CHUNK)
        frames.append(data)
        RECORD_SECONDS += 1
    # Stop recording
    stream.stop_stream()
    stream.close()
    audio.terminate()
    # Save recording to file
    waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(audio.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()
    return WAVE_OUTPUT_FILENAME

def speech_to_text(wav_file):
    wf = wave.open(wav_file, "rb")
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
    wav_file = record_audio()
    picam2.start()
    file_path = os.path.expanduser("~/Pictures/PhotoToAnalyse.jpg")
    picam2.capture_file(file_path)
    picam2.stop()
    print(f"Photo saved as {file_path}")
    prompt = speech_to_text(wav_file)
    print(f"Prompt: {prompt}")
    image_path_1 = "/home/rasberry/Pictures/PhotoToAnalyse.jpg"
    image1 = Image.open(image_path_1)
    response = model.generate_content([prompt, image1])
    print(response.text)
    speak(response.text)

button.when_pressed = button_pressed
print("Press the button to start. -- CTRL-C to exit.")
pause()


system_instruction = """
---Core Identity
- You are iSight, a wearable assistive device created by Luke Irven
- Primary function: Environmental interpretation & hazard navigation for visually impaired users
- Operation mode: chest-mounted (default) or manual positioning (handheld)


---Potential Questions


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
  
  
  
"""
