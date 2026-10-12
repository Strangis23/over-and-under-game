import wave
import math
import struct
import random

SAMPLE_RATE = 44100

def write_wav(filename, samples):
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        packed = b''.join(struct.pack('<h', max(-32767, min(32767, int(s * 32767)))) for s in samples)
        wav_file.writeframes(packed)
    print(f"Generated {filename}")

def gen_click():
    duration = 0.04
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        env = math.exp(-t * 120.0)
        freq = 1200.0 - (t * 8000.0)
        s = math.sin(2 * math.pi * freq * t) * env * 0.6
        samples.append(s)
    write_wav("assets/audio/click.wav", samples)

def gen_swoosh():
    duration = 0.22
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        env = math.sin(math.pi * (t / duration)) ** 1.5
        noise = (random.random() * 2.0 - 1.0) * 0.4
        freq = 200.0 + (t / duration) * 600.0
        tone = math.sin(2 * math.pi * freq * t) * 0.4
        samples.append((tone + noise) * env * 0.7)
    write_wav("assets/audio/swoosh.wav", samples)

def gen_correct():
    duration = 0.45
    num_samples = int(SAMPLE_RATE * duration)
    samples = [0.0] * num_samples
    notes = [523.25, 659.25, 783.99, 1046.50]  # C5, E5, G5, C6
    staggers = [0.0, 0.07, 0.14, 0.21]
    for n_idx, (freq, start_t) in enumerate(zip(notes, staggers)):
        start_samp = int(start_t * SAMPLE_RATE)
        for i in range(start_samp, num_samples):
            t = (i - start_samp) / SAMPLE_RATE
            env = math.exp(-t * 9.0)
            tone = math.sin(2 * math.pi * freq * t) + 0.3 * math.sin(4 * math.pi * freq * t)
            samples[i] += tone * env * 0.35
    write_wav("assets/audio/correct.wav", samples)

def gen_wrong():
    duration = 0.4
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        env = math.exp(-t * 6.0)
        # Low discordant buzz
        freq1 = 140.0 - t * 40.0
        freq2 = 148.0 - t * 40.0
        tone = 0.5 * math.sin(2 * math.pi * freq1 * t) + 0.5 * math.sin(2 * math.pi * freq2 * t)
        # Distortion / crunch
        clipped = math.tanh(tone * 2.5) * 0.6
        samples.append(clipped * env)
    write_wav("assets/audio/wrong.wav", samples)

def gen_streak():
    duration = 0.6
    num_samples = int(SAMPLE_RATE * duration)
    samples = [0.0] * num_samples
    # Major chord fanfare
    freqs = [523.25, 659.25, 783.99, 1046.50, 1318.51]
    for freq in freqs:
        for i in range(num_samples):
            t = i / SAMPLE_RATE
            env = math.exp(-t * 5.0)
            tone = math.sin(2 * math.pi * freq * t) * 0.2
            samples[i] += tone * env
    write_wav("assets/audio/streak.wav", samples)

if __name__ == "__main__":
    gen_click()
    gen_swoosh()
    gen_correct()
    gen_wrong()
    gen_streak()
