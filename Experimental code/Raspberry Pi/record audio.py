import pyaudio
import wave
import RPi.GPIO as GPIO

# Audio settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

# GPIO setup
BUTTON_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Initialize PyAudio
p = pyaudio.PyAudio()

# Open stream
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

print("Press the button to start recording...")

frames = []
recording = False

try:
    while True:
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:
            if not recording:
                print("Recording started...")
                recording = True
                frames = []
            
            data = stream.read(CHUNK)
            frames.append(data)
        elif recording:
            print("Recording stopped. Saving file...")
            recording = False
            
            # Save the recorded data as a WAV file
            wf = wave.open("output.wav", 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            print("File saved as output.wav")

except KeyboardInterrupt:
    print("Recording stopped by user")

finally:
    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    p.terminate()
    GPIO.cleanup()

print("Program ended")
