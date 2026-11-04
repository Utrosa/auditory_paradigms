#! /usr/bin/env python
# Time-stamp: <04-11-2026, m.utrosa@bcbl.eu>
'''
create_soundtrack_soundgen() module generates sounds as defined in csv
optionally, you can save generated sound arrays as .wav files to disk
TODOs: add and verify correctnes of logging tones
       wtf is current time thing
       might have to add the number of flashes per run (?) for feedback ... lool
'''
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# 01. IMPORT
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
import warnings
import numpy as np
import pandas as pd
import soundfile as sf
from pathlib import Path
import sounddevice as sd

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# 02. FUNCTIONS & CLASSES
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# TODO: replace set_dbspl() with Jasmin's code for sound normalization
def set_dbspl(sound, dbspl, ref=20e-6):
    """
    Normalize waveform to target dB SPL.

    :param sound : np.array, input waveform
    :param dbspl: float, desired sound level in dB SPL
    :param ref: float, reference pressure (default 20 µPa)
    """

    # Apply dB SPL scaling (RMS based)
    rms = np.sqrt(np.mean(sound**2))
    target_rms = ref * (10 ** (dbspl / 20))
    scale = target_rms / rms
    scaled_sound = sound * scale

    return scaled_sound

class SoundGen:
    def __init__(self, sample_rate, tau):
        """
        Initialize the CreateSound instance.

        :param sample_rate: Sample rate of sounds in Hz.
        :param tau: The ramping window in milliseconds.
        """
        self.sample_rate = sample_rate
        self.tau = tau / 1000 # convert to sec
    
    def sound_maker(self, freq, max_amplitude, num_harmonics, tone_duration, harmonic_factor, dbspl):
        """
        Make a single normalized sound.

        :param freq: Tone frequency in Hz.
        :param max_amplitude: Maximum amplitude to avoid clipping.
        :param num_harmonics: Number of harmonic tones.
        :param tone_duration: Duration of the tone in seconds.
        :param harmonic_factor: Harmonic amplitude decay factor for the tone.
        :param dbspl: Desired dB SPL (loudness) level (cannot change post sound creation).
        
        :return: normalized_sound: an array of audio samples representing a harmonic complex tone.
        """
        
        # Create a time array: each sample represents one event per second 
        t = np.linspace(
            0,                                     # start
            tone_duration,                         # stop
            int(self.sample_rate * tone_duration), # number of samples
            endpoint = False                       # stop is not the last sample
            )
        
        # Initialize a sound array
        sound = np.zeros_like(t)

        # Generate the harmonics
        for k in range(1, num_harmonics + 1):
            harmonic  = np.sin(2 * np.pi * freq * k * t)
            amplitude = max_amplitude * (harmonic_factor ** (k - 1)) / num_harmonics
            sound += amplitude * harmonic

        # Normalize the sound
        normalized_sound = set_dbspl(sound, dbspl)
        
        return normalized_sound

    def sine_ramp(self, sound):
        """ Apply ramping to the start and end of the sound """

        L = int(self.tau * self.sample_rate)
        t = np.linspace(0, L / self.sample_rate, L)
        sine_window = np.sin(np.pi * t / (2 * self.tau)) ** 2  # Sine fade-in

        sound = sound.copy()
        sound[:L] *= sine_window         # Apply fade-in
        sound[-L:] *= sine_window[::-1]  # Apply fade-out

        return sound

    def generate_soundtrack(self, df, max_amplitude, num_harmonics, tone_duration, harmonic_factor, dbspl):
        """
        Generate tone sequences with timing deviants for current run.

        :param df: A dataframe with tone sequence parameters with ms as the time unit.
        :param current_time: Current time in the experiment in sec, relative to start of the task.
        :param max_amplitude: Maximum amplitude to avoid clipping.
        :param num_harmonics: Number of harmonic tones.
        :param tone_duration: Duration of the tone in milliseconds.
        :param harmonic_factor: Harmonic amplitude decay factor for the tone.
        :param dbspl: Desired dB SPL (loudness) level (cannot change post sound creation).
        
        :yield: final_sequence: An array of audio samples, representing harmonic a complex tone sequence.
        """
        # Reminder that we're assuming ms as input unit
        message = (
            "\nAssuming input values (ISI, timing deviants, tone duration) are in milliseconds."
            "\nVerify units in the input parameters and csv files."
            )
        warnings.warn(message, UserWarning)

        # Convert to sec (only once - the same isi and tone durations in a run)
        isi = row.isi / 1000
        tone_duration = tone_duration / 1000

        # Calculate how many isi and tone samples are in an event
        isi_samples  = int(isi * self.sample_rate)
        tone_samples = int(tone_duration * self.sample_rate)

        # Initialize tone count, sequence and log
        tone_count = 1 # I don't like zero indexing
        sequence = []
        sequence_log = str()

        # Loop through all rows of the dataframe
        # Each row is a linear combination of its column values
        for row in df.itertuples():

            # ----------------- Adding TONES ------------------
            # What is the deviant category?
            if row.dev_cat:
                if row.dev_cat == 'timing':  # TONE STANDARD
                    sound = self.sound_maker(
                            row.base_freq,
                            max_amplitude,
                            num_harmonics,
                            tone_duration,
                            harmonic_factor,
                            dbspl
                            )
                elif row.dev_cat == 'pitch': # TONE DEV
                    if row.dev_type == "upper":
                        dev_freq = row.base_freq + row.dev
                        sound = self.sound_maker(
                                dev_freq,
                                max_amplitude,
                                num_harmonics,
                                tone_duration,
                                harmonic_factor,
                                dbspl
                                )
                    elif row.dev_type == "lower":
                        dev_freq = row.base_freq - row.dev
                        sound = self.sound_maker(
                                dev_freq,
                                max_amplitude,
                                num_harmonics,
                                tone_duration,
                                harmonic_factor,
                                dbspl
                                )

                    else:
                        print("Unrecognized deviant direction. Check input csv file - column 'dev_cat'.")
                else:
                    print("Unrecognized deviant category. Check input csv file - column 'dev_cat'.")
            else: # TONE STANDARD
                sound = self.sound_maker(
                row.base_freq,
                max_amplitude,
                num_harmonics,
                tone_duration,
                harmonic_factor,
                dbspl
                )
            
            # Apply ramp to start and end using the sine_ramp method
            ramped_sound = self.sine_ramp(sound)
            
            # Add the sound to the sequence
            sequence.append(ramped_sound)
            current_time += tone_samples # TODO: WTF is this?

            # ----------------- Adding ISI --------------------
            # Get the number of samples for the timing deviation
            if row.dev:
                dev = row.dev_abs / 1000
                dev_samples = int(dev * self.sample_rate)

            # Get the number of samples for a standard isi
            current_isi = isi_samples

            # TODO: Check if the next tone is a timing deviant (ISI is adjusted before the deviant tone ...)
            # if next_row.dev:

            # Convert dev to sec & get sample no.
            if row.dev:
                dev = row.dev_abs / 1000
                dev_samples = int(dev * self.sample_rate)

            # For sound trials with timing deviations
            if not pd.isna(row.dev_type):

                # Late tones
                # The ISI before the current tone is longer, ISI after shorter.
                # "dev_samples" are calculated from absolute timing deviant value
                if row.dev_type == "late":
                    if tone_count == (row.dev_loc - 1):
                        current_isi = isi_samples + dev_samples
                    elif tone_count == row.dev_loc:
                        current_isi = isi_samples - dev_samples

                # Early tones
                # The ISI before the current tone is shorter, ISI after longer.
                elif row.dev_type == "early":
                    if tone_count == (row.dev_loc - 1):
                        current_isi = isi_samples - dev_samples
                    elif tone_count == row.dev_loc:
                        current_isi = isi_samples + dev_samples
                
                # On-time tones
                else:
                    current_isi = isi_samples

            # Add the ISI
            # Note: there's one less isi in the sequence than tones.
            if tone_count < row.no_tones:
                sequence.append(np.zeros(current_isi))
                current_time += current_isi

            # -------------- Join all segments ----------------
            final_sequence = np.concatenate(sequence)

            # Yield the tone sequence, sequence log, and end time
            end_time = current_time / self.sample_rate
            yield final_sequence, sequence_log, end_time

            # Clear the list for the next iteration (memory <3)
            sequence.clear()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# 03. AUDIO STIMULI GENERATION
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
if __name__ == "__main__":

    # Import configuration
    from config_timfreq import params
    import config_timfreq as c

    # Ask for user-defined parameters
    sesh = input("Enter the session number:")
    sesID = int(sesh)
    parPath  = c.outPath / f"ses-{sesID:03d}_exp_parameter_combo.csv"

    # Load the session parameters from csv and order by run indices
    df = pd.read_csv(parPath)
    df.sort_values(by=["run_idx"], inplace=True)

    # Initialize the class
    sound_gen = SoundGen(params["SAMPLE_RATE"], params["TAU"])

    # Play the soundtrack over the runs
    no_runs = len(df["run_idx"].unique())
    for run in range(no_runs):

        # Correct for zero-indexing
        run_idx = run + 1

        # Select only the part of the dataframe relevant for the current trial
        df_run = df[df["run_idx"] == run_idx]

        # Generate the soundtrack of the experimental session
        for soundtrack, trial_log, time_end in sound_gen.generate_soundtrack(
           df_run,
           run_idx, # This should be the run's start time
           params["MAX_AMPLITUDE"],
           params["NUM_HARMONICS"], 
           params["TONE_DURATION"], 
           params["HARMONIC_FACTOR"],
           params["TONE_LOUDNESS"]
           ):
            sd.play(soundtrack, samplerate=params["SAMPLE_RATE"])
            sd.wait()

            # Optionally, save the run soundtrack as a .wav file
            if write_wav:
                filename = f"exp_combo-{sesID:03d}_run_{run_idx:02d}.wav"
                sf.write(
                    outPath / filename,
                    soundtrack,
                    params["SAMPLE_RATE"]
                )