#! /usr/bin/env python
# Time-stamp: <03-10-2025>
# Monika Utrosa Skerjanec

#1: INSTALL LIBRARIES
import random
import numpy as np
import soundfile as sf
import sounddevice as sd

#Import the external sequence generation file
import stimuli_generation as sg

#2: DEFINE PARAMETERS OF INTEREST
# Amount of ISI values defines the number of blocks
# Amount of deltas defines the number of trials (with correction for no-signal trials)
params_interest = {
    "ISI_max"     : 800,  # exclusive
    "ISI_min"     : 500,  # inclusive
    "ISI_step"    : 100,
    "delta_max"   : 301,  # exclusive
    "delta_min"   : -300, # inclusive
    "delta_step"  : 10,
    "delta_extra" : [-15, -5, 5, 15], # must be a list
    "threshold"   : 50
}

#3: DEFINE BASE UNCHANGING PARAMETERS 
params = {
    "SAMPLE_RATE"     : 48000,  # Sampling rate in Hz
    "TAU"             : 5,      # Ramping window in msec
    "HARMONIC_FACTOR" : 0.9,    # Harmonic factor for the sound generation: should be something between 0.7-0.9
    "NUM_HARMONICS"   : 5,      # Number of harmonics: starting with 5 as it sounds okay
    "TONE_DURATION"   : 100,    # Duration of each tone in msec
    "TONE_FREQUENCY"  : 440,    # Equivalent to A musical tone
    "NO_TONES"        : 7,      # Informed by iterative singing preferences: 10.1016/j.cub.2023.02.070
}

#4: GENERATE ISI & DELTAS
#Generate a list of inter-stimulus-intervals (ISI)
isi_list = list(np.arange(params_interest["ISI_min"],
                          params_interest["ISI_max"], 
                          params_interest["ISI_step"],
                          dtype = np.int64))
                
#Generate list of possible deviations (deltas)
deltas = np.setdiff1d(np.arange(params_interest["delta_min"], 
                                params_interest["delta_max"],
                                params_interest["delta_step"],
                                dtype = np.int64),
                      [0])

# Add custom deviations
extra  = np.array(params_interest["delta_extra"], dtype = np.int64)
deltas = np.concatenate([deltas, extra])

# Balance signal vs no-signal trials
deltas_abs = np.abs(deltas)
belowT     = np.sum(deltas_abs < params_interest["threshold"])
aboveT     = np.sum(deltas_abs > params_interest["threshold"])
no_empty = aboveT - belowT
if no_empty > 0:
    possible_empty = np.setdiff1d(np.arange(-params_interest["threshold"], params_interest["threshold"], dtype = np.int64), deltas)
    empty  = np.random.choice(possible_empty, size = no_empty, replace = False)
    deltas = np.concatenate([deltas, empty])
    
deltas = np.sort(deltas)

#Generate core sound stimuli
sound_gen = sg.SoundGen(params["SAMPLE_RATE"], params["TAU"])

#5: GENERATE SEQUENCES
random.shuffle(isi_list)
for block, current_isi in enumerate(isi_list):

    # Shuffle deltas per block
    random.shuffle(deltas)

    for trial, current_delta in enumerate(deltas):

        sequence, tone_idx = sound_gen.generate_sequence(
                                      params["TONE_FREQUENCY"], 
                                      params["NUM_HARMONICS"], 
                                      params["TONE_DURATION"],
                                      params["HARMONIC_FACTOR"],
                                      current_isi, 
                                      params["NO_TONES"], 
                                      current_delta
                                      )
        
        # Play the generated sound sequence
        sd.play(sequence, params["SAMPLE_RATE"])
        sd.wait()

        # Save the sequence
        filename = f"sequence_delta_{current_delta}_isi_{current_isi}.wav"
        sf.write(filename, sequence, params["SAMPLE_RATE"])