import pyaudio

p = pyaudio.PyAudio()

for i in range(p.get_device_count()):
    s = p.get_device_info_by_index(i)['name']
    if s.__contains__('Yeti'):
        print(p.get_device_info_by_index(i),'\n')

CHUNK = 1024  # Samples: 1024,  512, 256, 128
RATE = 44100  # Equivalent to Human Hearing at 40 kHz
INTERVAL = 1  # Sampling Interval in Seconds ie Interval to listen

stream = p.open(format=p.get_format_from_width(width=2),
                channels=1,
                output=True,
                rate=OUTPUT_SAMPLE_RATE,
                input_device_index=INDEX_OF_CHOSEN_INPUT_DEVICE, # This is where you specify which input device to use
                stream_callback=callback)

# Start processing and do whatever else...
stream.start_stream()