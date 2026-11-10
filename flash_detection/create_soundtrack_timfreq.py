#! /usr/bin/env python
# Original code: Ekim Celikay, e.celikay@bcbl.eu
# Adapted: <10-11-2026, m.utrosa@bcbl.eu>
'''
The create_soundtrack_soundgen() module generates sounds as defined in an 
imported .csv file. The generate soundtracks (sound arrays) are saved as 
.wav files.

TODOs: add and verify correctnes of logging tones (end & current time)
       replace set_dbspl() with Jasmin's code for sound normalization
'''
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# 01. IMPORT
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
import csv
import warnings
import numpy as np
import pandas as pd
import soundfile as sf
from pathlib import Path
import sounddevice as sd

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# 02. FUNCTIONS & CLASSES
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# TODO: Correct for HL and SPL
# This is minor for small differences in standard frequency
# Would be best that a new standard is not a deviant possibility of a previous standard ...

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

    def generate_soundtrack(self, df, current_time, max_amplitude, num_harmonics, tone_duration, harmonic_factor, dbspl, verbose=False):
        """
        Generate tone sequences with timing deviants for current run.

        :param df: A dataframe with tone sequence parameters with ms as the time unit.
        :param current_time: Current time in the experiment in milliseconds, relative to start of the task.
        :param max_amplitude: Maximum amplitude to avoid clipping.
        :param num_harmonics: Number of harmonic tones.
        :param tone_duration: Duration of the tone in milliseconds.
        :param harmonic_factor: Harmonic amplitude decay factor for the tone.
        :param dbspl: Desired dB SPL (loudness) level (cannot change post sound creation).
        :param verbose: If True, prints updates to the terminal.

        :yield: final_sequence: An array of audio samples, representing harmonic a complex tone sequence.
        :yield: sequence_log: A text file with onset, duration, and tone timing information.
        """
        # Convert to seconds & sound array duration
        current_time = current_time / 1000
        current_time = current_time * self.sample_rate

        # Reminder that we're assuming ms as the input unit
        if verbose:
            message = (
                "\nAssuming input values (ISI, timing deviants, tone duration) are in milliseconds."
                "\nVerify units in the input parameters and csv files."
                )
            warnings.warn(message, UserWarning)

        # Initialize tone count, sequence and log
        tone_count = 0
        sequence = []
        sequence_log = str()

        # Get tone samples (only once)
        tone_duration = tone_duration / 1000
        tone_samples = int(tone_duration * self.sample_rate)

        # Loop through all rows of the dataframe
        # Each row is a linear combination of its column values
        for row in df.itertuples():

            # --------------- Get EVENT samples ---------------------
            # ----------------- Adding TONES
            # Generate a standard tone
            if pd.isna(row.dev_cat):
                sound = self.sound_maker(
                    row.base_freq,
                    max_amplitude,
                    num_harmonics,
                    tone_duration,
                    harmonic_factor,
                    dbspl
                )
            elif not pd.isna(row.dev_cat): # Deviant tones have a category

                # Generate a frequency standard tone
                if row.dev_cat == 'timing': 
                    sound = self.sound_maker(
                            row.base_freq,
                            max_amplitude,
                            num_harmonics,
                            tone_duration,
                            harmonic_factor,
                            dbspl
                            )

                # Generate a frequency deviant tone
                elif row.dev_cat == 'pitch':
                    dev_freq = row.base_freq * (2**int(row.dev))
                    sound = self.sound_maker(
                            dev_freq,
                            max_amplitude,
                            num_harmonics,
                            tone_duration,
                            harmonic_factor,
                            dbspl
                            )
                
                # Raise error
                else:
                    raise ValueError(
                        f"Unrecognized deviant category: {row.dev_cat}. "
                        "Please check the input file."
                    ) 
            else:
                raise ValueError(
                    f"Undefined deviant category: {row.dev_cat}. "
                    "Please check the input file or add silent tone."
                )

            # Apply ramp to the start and the end
            ramped_sound = self.sine_ramp(sound)

            # Identify tone type
            if not pd.isna(row.dev): # DEVIANTS
                if row.dev > 0: # Positive deviants
                    if row.dev_cat == "timing":
                        tone_type = f"fStd-{int(row.base_freq)}Hz_delta-p{int(row.dev_abs)}ms_type-fStdtDev"
                    elif row.dev_cat == "pitch":
                        tone_type = f"fStd-{int(row.base_freq)}Hz_fDev-p{int(row.dev_abs)}_type-fDevtStd"
                elif row.dev < 0: # Negative deviants
                    if row.dev_cat == "timing":
                        tone_type = f"fStd-{int(row.base_freq)}Hz_delta-n{int(row.dev_abs)}ms_type-fStdtDev"
                    elif row.dev_cat == "pitch":
                        tone_type = f"fStd-{int(row.base_freq)}Hz_fDev-n{int(row.dev_abs)}_type-fDevtStd"
            else: # STANDARDS
                tone_type = f"fStd-{int(row.base_freq)}Hz_type-fStdtStd"

            # Log tones
            onset_sec = current_time / self.sample_rate
            log_format = f"{onset_sec}\t{tone_duration}\t{tone_type}\n"
            sequence_log = sequence_log + log_format

            # Add the sound to the sequence
            sequence.append(ramped_sound)
            current_time += tone_samples

            # ----------------- Adding ISI
            # Convert milliseconds to seconds and get no. isi samples
            isi = row.isi / 1000
            isi_samples  = int(isi * self.sample_rate)
            
            # Add one less ISI. Sequence ends with a tone.
            if tone_count < len(df):
                
                # Get the number of samples for a standard isi
                current_isi = isi_samples

                # Adjust the ISI before or after a timing deviant
                # Check current event, for ISI after timDev
                if row.dev_cat == 'timing':

                    # Get the number of deviant samples
                    dev = row.dev_abs / 1000
                    dev_samples  = int(dev * self.sample_rate)
                    
                    if row.dev_dir == 'early':
                        current_isi = isi_samples + dev_samples
                    elif row.dev_dir == 'late':
                        current_isi = isi_samples - dev_samples
                
                else:
                    # Check the next event, for ISI before timDev
                    if tone_count < len(df) - 1:
                        
                        # Extract variables
                        is_next_timDev  = df.iloc[tone_count + 1]['dev_cat']
                        next_timDev_dir = df.iloc[tone_count + 1]['dev_dir']
                        next_dev_delta  = df.iloc[tone_count + 1]['dev_abs']
                        
                        # Adjust the ISI after a timing deviant
                        if pd.isna(is_next_timDev): # Standard ISI
                            current_isi = isi_samples
                        elif is_next_timDev == 'timing':
                            
                            # Get the number of deviant samples
                            dev = next_dev_delta / 1000
                            dev_samples  = int(dev * self.sample_rate)
                            
                            # Get the number of current ISI samples
                            if next_timDev_dir == 'early':
                                current_isi = isi_samples - dev_samples
                            elif next_timDev_dir == 'late':
                                current_isi = isi_samples + dev_samples
                        elif is_next_timDev == 'pitch':
                            current_isi = isi_samples
                        else:
                            raise ValueError(
                                f"Undefined next deviant category: {row.dev_cat}. "
                                "Please check the input file or add silent tone."
                            )

                # Append the ISI to the sequence
                sequence.append(np.zeros(current_isi))

                # Update tone count and time
                tone_count += 1
                current_time += current_isi

        # -------------- Join ALL segments ----------------------
        final_sequence = np.concatenate(sequence)

        # Yield the tone sequence, sequence log
        yield final_sequence, sequence_log

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

    # Load the session parameters from csv
    df = pd.read_csv(parPath)

    # Initialize the class
    sound_gen = SoundGen(params["SAMPLE_RATE"], params["TAU"])
    
    # Play the soundtrack over the runs
    no_runs = len(df["run_idx"].unique())
    for run in range(no_runs):
 
        # Correct for zero-indexing
        run_idx = run + 1

        # Select only the part of the dataframe relevant for the current trial
        df_run = df[df["run_idx"] == run_idx]
        
        # Initialize log for sequences
        # TODO: add subject ID
        # TODO: either add a timestamp or change IMPORT of logfiles ...
        out_dir = Path(f"ses-{sesID:003d}")
        out_dir.mkdir(parents=True, exist_ok=True)
        log_path = out_dir / f"ses-{sesID:02d}_task-timfreqDev_run-{run_idx:02d}_events.tsv"

        # Write the log file using standard file I/O
        with open(log_path, mode="w", newline="") as tsv_file:
            
            # Write header
            tsv_file.write("onset\tduration\ttrial_type\n")

            # Generate the soundtrack of the experimental session
            for soundtrack, sequence_log in sound_gen.generate_soundtrack(
               df_run,
               0, # current time
               params["MAX_AMPLITUDE"],
               params["NUM_HARMONICS"], 
               params["TONE_DURATION"], 
               params["HARMONIC_FACTOR"],
               params["TONE_LOUDNESS"]
            ):
                
                # Optionally play the soundtrack
                # sd.play(soundtrack, samplerate=params["SAMPLE_RATE"])
                # sd.wait()
                
                # Write relevant info to log for current run
                tsv_file.write(sequence_log)

                # Optionally, save the run soundtrack as a .wav file
                if c.write_wav:
                    filename = f"exp_ses-{sesID:02d}_run_{run_idx:02d}.wav"
                    sf.write(
                        c.outPath / filename,
                        soundtrack,
                        params["SAMPLE_RATE"]
                    )