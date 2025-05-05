import google.generativeai as genai
import os
import time
from PIL import Image
from picamera2 import Picamera2
from gtts import gTTS  # Import gTTS for Text-to-Speech
from playsound import playsound  # Import playsound to play the audio file

# Configure Google Generative AI API
genai.configure(api_key="")
model = genai.GenerativeModel(model_name="gemini-2.0-flash-exp")

# Initialize and configure the camera
picam2 = Picamera2()
camera_config = picam2.create_preview_configuration()
picam2.configure(camera_config)
picam2.start()
time.sleep(2)

# Capture an image and save it
file_path = os.path.expanduser("~/Pictures/PhotoToTest.jpg")
picam2.capture_file(file_path)
picam2.stop()
print(f"Photo saved as {file_path}")

# Open the captured image and generate a description
image_path_1 = "/home/rasberry/Pictures/PhotoToTest.jpg"  
sample_file_1 = Image.open(image_path_1)
prompt = "describe the image in 10 words"
response = model.generate_content([prompt, sample_file_1])
description = response.text  # Extract the text response

# Print the description (optional)
print(description)

# Convert the description to speech using gTTS
tts = gTTS(text=description, lang='en')  # Create a TTS object with English language
audio_file = "response.mp3"  # Define the audio file name
tts.save(audio_file)  # Save the audio file

# Play the audio file
playsound(audio_file)
