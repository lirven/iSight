import google.generativeai as genai
import os
import time
from PIL import Image
from picamera2 import Picamera2
from gpiozero import Button
from signal import pause

button = Button(17)

genai.configure(api_key="")
model = genai.GenerativeModel(model_name="gemini-2.0-flash-exp")

# Initialize Picamera2 object once
picam2 = Picamera2()
camera_config = picam2.create_preview_configuration()
picam2.configure(camera_config)

def button_pressed():
    picam2.start()
    time.sleep(2)
    file_path = os.path.expanduser("~/Pictures/PhotoToTest.jpg")
    picam2.capture_file(file_path)
    picam2.stop()
    print(f"Photo saved as {file_path}")

    image_path_1 = "/home/rasberry/Pictures/PhotoToTest.jpg"
    sample_file_1 = Image.open(image_path_1)
    prompt = "describe the image in 10 words"
    response = model.generate_content([prompt, sample_file_1])
    print(response.text)

button.when_pressed = button_pressed
print("Press the button to take a photo and analyze it. Press CTRL-C to exit.")
pause()
