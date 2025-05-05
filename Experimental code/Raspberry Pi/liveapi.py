
import google.generativeai as genai
import PIL.Image
import io
import time
from picamera2 import Picamera2
import cv2  

genai.configure(api_key="AIzaSyDHZBMD8PmN1RaIMXlC91R6q9SzAgAxI6Y")  
model = genai.GenerativeModel('gemini-2.0-flash-exp')

picam2 = Picamera2()
camera_config = picam2.create_video_configuration(main={"size": (640, 480)}) 
picam2.configure(camera_config)
picam2.start()
time.sleep(2)  # Camera warm-up


def generate_frames_and_prompts(initial_prompt, subsequent_prompts=None):
    yield {"role": "user", "parts": [{"text": initial_prompt}]}

    try:
        while True:
            request = picam2.capture_request()
            array = request.make_array("main")
            request.release()

            # Convert to RGB (Gemini API needs RGB, picamera2 gives BGR)
            rgb_array = cv2.cvtColor(array, cv2.COLOR_BGR2RGB)
            pil_image = PIL.Image.fromarray(rgb_array)
            img_byte_arr = io.BytesIO()
            pil_image.save(img_byte_arr, format='JPEG')
            image_bytes = img_byte_arr.getvalue()

            yield {
                "role": "user",  # Images are considered user input
                "parts": [{"inline_data": {"mime_type": "image/jpeg", "data": image_bytes}}],
            }

            time.sleep(0.1)

    except GeneratorExit:
        print("Generator exiting.")

    if subsequent_prompts:
        for prompt in subsequent_prompts:
            yield {"role": "user", "parts": [{"text": prompt}]}



def video_chat(initial_prompt, subsequent_prompts=None):

    chat = model.start_chat()

    # Get the combined generator of frames and prompt
    input_generator = generate_frames_and_prompts(initial_prompt, subsequent_prompts)

    try:
        # Use send_message iteratively with the generator.
        for part in input_generator:
           responses = chat.send_message(part, stream=True)
           for response in responses:
               print(response.text, end="", flush=True)
        print()

    except Exception as e:
        print(f"error : {e}")
    finally:
        print("Closing camera .")
        picam2.stop()



if __name__ == '__main__':
    initial_prompt = "Describe what you see continuously. Be concise."
    subsequent_prompts = [
        "Is there a person in the frame?",
        "What color is the object?"
    ]
    video_chat(initial_prompt, subsequent_prompts)
