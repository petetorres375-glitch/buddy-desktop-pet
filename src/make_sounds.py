"""
make_sounds.py
Generates placeholder meow.wav and purr.wav using basic waveform synthesis.
No external audio files needed - built from math.

Core idea: a .wav file is just a long list of numbers describing speaker
position over time (the "waveform"). We build that list, then use Python's
built-in `wave` module to save it.
"""

import numpy as np
import wave

SAMPLE_RATE = 44100  # standard CD-quality: 44,100 numbers per second of audio


def save_wav(filename, samples, sample_rate=SAMPLE_RATE):
    """Convert a numpy array of samples (-1.0 to 1.0) into a .wav file."""
    # Clip to valid range, then scale up to 16-bit integer range
    samples = np.clip(samples, -1.0, 1.0)
    samples_int16 = (samples * 32767).astype(np.int16)

    with wave.open(filename, "w") as wf:
        wf.setnchannels(1)        # mono
        wf.setsampwidth(2)        # 2 bytes = 16-bit audio
        wf.setframerate(sample_rate)
        wf.writeframes(samples_int16.tobytes())

    print(f"Saved {filename} ({len(samples) / sample_rate:.2f}s)")


def make_meow(duration=0.6):
    """
    A meow: pitch starts low, rises ("mee-"), then falls ("-ow"),
    with a little vibrato (wobble) so it isn't a flat robotic tone.
    """
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)

    # Pitch contour: rises for first 40% of the sound, falls for the rest.
    # This shapes the "mee-OW" feel.
    rise_portion = 0.4
    pitch_curve = np.where(
        t < duration * rise_portion,
        300 + (t / (duration * rise_portion)) * 250,           # 300Hz -> 550Hz
        550 - ((t - duration * rise_portion) / (duration * (1 - rise_portion))) * 350  # 550Hz -> 200Hz
    )

    # Vibrato: a small wobble added on top of the main pitch (~7 wobbles/sec)
    vibrato = 15 * np.sin(2 * np.pi * 7 * t)
    instantaneous_freq = pitch_curve + vibrato

    # Build the tone by integrating frequency over time (this is how you
    # turn a "frequency at each moment" curve into an actual waveform)
    phase = 2 * np.pi * np.cumsum(instantaneous_freq) / SAMPLE_RATE
    tone = np.sin(phase)

    # Add a little harmonic "rasp" (real meows aren't a pure sine wave)
    tone += 0.25 * np.sin(2 * phase)
    tone += 0.1 * np.sin(3 * phase)

    # Volume envelope: fade in fast, fade out slower (natural-sounding shape)
    envelope = np.ones_like(t)
    fade_in_samples = int(0.05 * SAMPLE_RATE)
    fade_out_samples = int(0.25 * SAMPLE_RATE)
    envelope[:fade_in_samples] = np.linspace(0, 1, fade_in_samples)
    envelope[-fade_out_samples:] = np.linspace(1, 0, fade_out_samples)

    return tone * envelope * 0.6  # 0.6 = overall volume


def make_purr(duration=2.0):
    """
    A purr: a low rumbling tone whose volume pulses rapidly (~27 times/sec).
    This pulsing is mechanically close to how real cat purrs work.
    """
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)

    # Low rumble base tone (real purrs are very low, around 25-30Hz
    # fundamental with low growl-like harmonics)
    base_freq = 28
    tone = np.sin(2 * np.pi * base_freq * t)
    tone += 0.5 * np.sin(2 * np.pi * base_freq * 2 * t)  # harmonic for richness
    tone += 0.3 * np.sin(2 * np.pi * base_freq * 3 * t)

    # The "purr pulse": rapid amplitude wobble around 27 Hz, like a real purr
    pulse = 0.6 + 0.4 * np.sin(2 * np.pi * 27 * t)

    # Slight random texture so it's not perfectly mechanical
    np.random.seed(42)
    noise = np.random.normal(0, 0.03, len(t))

    signal = tone * pulse + noise

    # Smooth fade in/out so looping feels seamless
    envelope = np.ones_like(t)
    fade_samples = int(0.15 * SAMPLE_RATE)
    envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
    envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)

    return signal * envelope * 0.4


if __name__ == "__main__":
    meow = make_meow()
    save_wav("/home/claude/buddy_pet/assets/meow.wav", meow)

    purr = make_purr()
    save_wav("/home/claude/buddy_pet/assets/purr.wav", purr)
