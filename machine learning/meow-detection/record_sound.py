import pyaudio
import wave
 
chunk = 1024      # Each chunk will consist of 1024 samples
sample_format = pyaudio.paInt16      # 16 bits per sample
channels = 2      # Number of audio channels
fs = 44100        # Record at 44100 samples per second
time_in_seconds = 3
filename = "soundsample.wav"
 
p = pyaudio.PyAudio()  # Create an interface to PortAudio
 
print('-----Now Recording-----')
 
#Open a Stream with the values we just defined
stream = p.open(format=sample_format,
                channels = channels,
                input_device_index = 1,
                rate = fs,
                frames_per_buffer = chunk,
                input = True)
 
frames = []  # Initialize array to store frames
 
# Store data in chunks for 3 seconds
for i in range(0, int(fs / chunk * time_in_seconds)):
    data = stream.read(chunk)
    frames.append(data)
 
# Stop and close the Stream and PyAudio
stream.stop_stream()
stream.close()
p.terminate()
 
print('-----Finished Recording-----')
 
# Open and Set the data of the WAV file
file = wave.open(filename, 'wb')
file.setnchannels(channels)
file.setsampwidth(p.get_sample_size(sample_format))
file.setframerate(fs)
 
#Write and Close the File
file.writeframes(b''.join(frames))
file.close()