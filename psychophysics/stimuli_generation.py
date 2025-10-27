#! /usr/bin/env python
# Time-stamp: <19-10-2025>
# Created by Ekim Celikay, modified by Sofia Taglini and Monika Utrosa Skerjanec
# Code on how to generate a tone based on Ekims input, modified for the present purposes

import numpy as np
import sounddevice as sd

class SoundGen:
    def __init__(self, sample_rate, tau):
        """
        Initialize the CreateSound instance.
        :param sample_rate: Sample rate of sounds ( per second).
        :param tau: The ramping window in milliseconds.
        """
        self.sample_rate = sample_rate
        self.tau = tau / 1000

    def sound_maker(self, freq, max_amplitude, num_harmonics, tone_duration,
                    harmonic_factor):
        """
        :param sample_rate: Sample rate in Hz.
        :param freq: Base frequency in Hz.
        :param max_amplitude: Maximum amplitude to avoid distortions or clipping.
        :param num_harmonics: Number of harmonic tones.
        :param tone_duration: Duration of each tone in seconds.
        :param harmonic_factor: Harmonic amplitude decay factor for each tone.
        :return: sound: array of audio samples representing the harmonic complex tone.
        """
        # Create the time array
        t = np.linspace(0, tone_duration, int(self.sample_rate * tone_duration),
                        endpoint = False)
        
        # Initialize the sound array
        sound = np.zeros_like(t)

        # Generate the harmonics
        for k in range(1, num_harmonics + 1):
            harmonic = np.sin(2 * np.pi * freq * k * t)
            amplitude = max_amplitude * (harmonic_factor ** (k - 1)) / num_harmonics
            sound += amplitude * harmonic

        return sound

    def sine_ramp(self, sound):
        L = int(self.tau * self.sample_rate)
        t = np.linspace(0, L / self.sample_rate, L)
        sine_window = np.sin(np.pi * t / (2 * self.tau)) ** 2  # Sine fade-in

        sound = sound.copy()
        sound[:L] *= sine_window         # Apply fade-in
        sound[-L:] *= sine_window[::-1]  # Apply fade-out

        return sound

    #Sequence generation, with one displaced tone 
    def generate_sequence(self, freq, max_amplitude, num_harmonics, tone_duration, harmonic_factor,
                          isi, no_tones, delta):

        # Convert to sec (input must be in msec)
        isi = isi / 1000
        delta = delta / 1000
        tone_duration = tone_duration / 1000

        # Generate the tone using the sound_maker method
        sound = self.sound_maker(freq, max_amplitude, num_harmonics, tone_duration,
                                 harmonic_factor)

        # Apply ramping and
        ramped_sound = self.sine_ramp(sound)

        # Calculate how many events/samples occur per event (tone, isi, delta)
        isi_samples   = int(isi * self.sample_rate)
        delta_samples = int(delta * self.sample_rate)
        tone_samples  = int(tone_duration * self.sample_rate)
        total_samples = int(tone_samples * no_tones + (no_tones - 1) * isi_samples)
         
        # Pick a random tone to displace
        displaced_tone = np.random.randint(4, no_tones)

        # Generate sequence with ISI gaps between each tone
        sequence = np.array([])

        for tone_idx in range(no_tones):
            
            # ----------------- Adding tones ------------------
            sequence = np.concatenate((sequence, ramped_sound))

            # ----------------- Adding ISI --------------------
            # Add ISI after last tone to prevent abrupt end
            if tone_idx == no_tones - 2:
                sequence = np.concatenate((sequence, np.zeros(isi_samples)))
            
            # Change the ISI before the displaced tone
            if tone_idx == displaced_tone - 2:
                
                # Positive delta (delay)
                if delta > 0:
                    isi_before = isi_samples + delta_samples
                    isi_after  = isi_samples - delta_samples
                    if isi_after <= 0:
                        raise ValueError(f"Displacement is set too big: delta = {delta} sec. Reduce delta or increase ISI.")
                    sequence = np.concatenate((sequence, np.zeros(isi_before)))

                # Negative delta (advance)
                elif delta < 0:
                    isi_before = isi_samples + delta_samples
                    isi_after  = isi_samples - delta_samples
                    if isi_before <= 0:
                        raise ValueError(f"Displacement is set too big: delta = {delta} sec. Reduce delta or increase ISI.")
                    sequence = np.concatenate((sequence, np.zeros(isi_before)))
               
               # Zero delta (on-time)
                elif delta == 0:
                    sequence = np.concatenate((sequence, np.zeros(isi_samples)))
            
            # Change the ISI after the displaced tone
            elif tone_idx == displaced_tone - 1:
                sequence = np.concatenate((sequence, np.zeros(isi_after)))
        
            # Add ISI after a regular tone
            else:
                sequence = np.concatenate((sequence, np.zeros(isi_samples)))

        return sequence, displaced_tone, total_samples
        
# Example usage:
if __name__ == "__main__":
    sample_rate = 48000  # Sample rate in Hz
    tau = 5              # Ramping window in msec
    sound_gen = SoundGen(sample_rate, tau)


    # Parameters for the sound generation
    freq = 392             # Frequency in Hz
    num_harmonics = 5      # Number of harmonics
    tone_duration = 50     # Duration of each tone in msec
    harmonic_factor = 0.7  # Harmonic amplitude decay factor
    no_tones = 7           # Number of tones in the sequence

    # Max safe amplitude calculated via a simulation
    A_max = 1.1
    target_rms = 0.4

    # Inter-stimulus interval in msec
    isi_list = list(np.arange(400, 800, 100))
    current_isi = np.random.choice(isi_list)

    # Deviations in msec
    deltas = list(np.arange(-300, 301, 10))
    extra = [5, 15]
    deltas.extend(extra)
    current_delta = np.random.choice(deltas)

    # Generate the sequence
    sequence, displaced_tone, duration = sound_gen.generate_sequence(
                                                   freq,
                                                   A_max,
                                                   num_harmonics, 
                                                   tone_duration, 
                                                   harmonic_factor,
                                                   current_isi,
                                                   no_tones,
                                                   current_delta
                                                   )
    sd.play(sequence, samplerate = sample_rate)
    sd.wait()                                  

    # Status
    print("DELTA:",          current_delta, 
          "ISI:",            current_isi,
          "TONE_DISPLACED:", displaced_tone)
    
    # Check available hardware
    print("DEFAULT", sd.default.device)
    print(sd.query_devices())

    # TRY with bluethooth off
    # sd.default.device = (None, 0) # No errors and with sound.
                                    # 0 HD-Audio Generic: ALC257 Analog (hw:1,0), ALSA (2 in, 2 out)
    # sd.default.device = (None, 1) # Invalid number of channels [PaErrorCode -9998]
                                    # 1 acp63: - (hw:2,0), ALSA (2 in, 0 out)
    # sd.default.device = (None, 2) # No errors but no sound.
                                    # 2 hdmi, ALSA (0 in, 8 out)

    # TRY with bluetho2 hdmi, ALSA (0 in, 8 out)oth on
    # sd.default.device = (None, 0) # No errors and with sound.
                                    # 0 HD-Audio Generic: ALC257 Analog (hw:1,0), ALSA (2 in, 2 out)
    # sd.default.device = (None, 1) # Invalid number of channels [PaErrorCode -9998]
                                    # 1 acp63: - (hw:2,0), ALSA (2 in, 0 out)
    # sd.default.device = (None, 2) # No errors but no sound.
                                    # 2 hdmi, ALSA (0 in, 8 out)