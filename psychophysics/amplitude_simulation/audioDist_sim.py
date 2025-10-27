#! /usr/bin/env python
# Time-stamp: <20-10-2025, m.utrosa@bcbl.eu>
# Simulate Sounds to Correct for Distortions

# Prerequisites
import numpy as np
import time

# Parameters
sample_rate   = 48000   # Sample rate in Hz
num_harmonics = 5       # Number of harmonics
tone_duration = 0.033   # Minimal tone duration in seconds

def sound_maker(sample_rate, freq, num_harmonics, tone_duration, harmonic_factor):
    """
    :param sample_rate: Sample rate in Hz.
    :param freq: Base frequency in Hz.
    :param num_harmonics: Number of harmonic tones.
    :param tone_duration: Duration of each tone in seconds.
    :param harmonic_factor: Harmonic amplitude decay factor for each tone.
    :return: sound: np.ndarray: array of audio samples representing the harmonic complex tone.
    """
    # Create the time array
    t = np.linspace(0, tone_duration, int(sample_rate * tone_duration), endpoint = False)
     
    # Initialize the sound array
    sound = np.zeros_like(t)

    # Generate the harmonics
    for k in range(1, num_harmonics + 1):
        omega = 2 * np.pi * freq * k
        harmonic = np.sin(omega * t)
        amplitude = (harmonic_factor ** (k - 1)) / num_harmonics
        sound = sound + amplitude * harmonic

    return sound

# Track absolute peak
z = 0

for loop_idx, harmonic_factor in enumerate(np.linspace(0.99, 0.009, 10000)):
    
    start = time.time()
    for _, freq in enumerate(np.linspace(33, 500, 10000).astype(int)):
        sound = sound_maker(sample_rate, 
                            freq, 
                            num_harmonics,
                            tone_duration,
                            harmonic_factor)

        # Get the peaks of each sound by checking absolute values
        z = max(z, np.max(np.abs(sound)))
    end = time.time()
    print(f"The inner loop {loop_idx + 1} took:", round(end - start, 4), "seconds.")

# Get the maximum number of all the sounds (should be <1)
# Find the amplitude number that will keep all these max values below one.
A = 1 / (z + 0.1)
print("The maximum value of all simulated sounds:", z, flush = True)
print("The amplitude number to keep all max values below one:", A, flush = True)

# RESULT <20.10.2025, 19:57>
# The maximum value of all simulated sounds: 0.7745342912157799
# The amplitude number to keep all max values below one: 1.1434657394735173