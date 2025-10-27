#! /usr/bin/env python
# Time-stamp: <21-10-2025>
# Sofia Taglini's final version 24-07-2025
# Modifed by Monika Utrosa Skerjanec
# Testing detection accuracy for deviant tones 

#1: INSTALL LIBRARIES
import random
import numpy as np
import sounddevice as sd
from datetime import datetime 
from expyriment import design, control, stimuli, misc, io

# Import the external sequence generation file
import stimuli_generation as sg

#2: SET MODE and OUTPUT DEVICE
control.set_develop_mode(on = True) # Set to False when running the real experiment

#3: DEFINE PARAMETERS OF INTEREST
# Amount of ISI values defines the number of blocks
# Amount of deltas defines the number of trials * 2 (adding "no-signal" trials)
params_interest = {
    "ISI_max"     : 701,  # exclusive
    "ISI_min"     : 600,  # inclusive
    "ISI_step"    : 100,
    "delta_max"   : 351,  # exclusive
    "delta_min"   : 300,  # inclusive
    "delta_step"  : 10,
    "delta_extra" : [-15, -5, 5, 15], # must be a list
    "threshold"   : 50 # literature based min. detectable deviance
}

#4: DEFINE BASE UNCHANGING PARAMETERS 
params = {

    # Experiment structure 
    "ITI"       : 2000, # msec
    "WAIT_TIME" : 3000, # msec (ensuring reading at the start & end of the experiment)

	# Visual
    "FIXATION_CROSS_SIZE"     : (20, 20),
	"FIXATION_CROSS_POSITION" : (0, 0),
	"FIXATION_CROSS_WIDTH"    : 4,
	"HEADING_SIZE"            : 30, 
	"TEXT_SIZE"               : 20,
    "WHITE"                   : (255, 255, 255), # fixation cross
    "BLACK"                   : (0, 0, 0),       # screen background

	# Audio
	"SAMPLE_RATE"     : 48000,  # Sampling rate in Hz
    "TAU"             : 5,      # Ramping window in msec
    "HARMONIC_FACTOR" : 0.7,    # Harmonic factor for the sound generation: should be something between 0.7-0.9
    "NUM_HARMONICS"   : 5,      # Number of harmonics: starting with 5 as it sounds okay
	"TONE_DURATION"   : 50,     # Duration of each tone in msec
    "TONE_FREQUENCY"  : 392,    # Equivalent to musical tone A
    "MAX_AMPLITUDE"   : 1.1,    # Calculated through simluation (see: audioDist_sim.py)
    "NO_TONES"        : 7,      # Informed by iterative singing preferences: 10.1016/j.cub.2023.02.070

    # Text (for instructions and goodbye message)
    "INTRO_HEADING" : f"Welcome to the auditory detection test",
    "INTRO_TEXT"    : (f"When you being the experiment, you will be presented with a fixation cross."
                        " Please keep your gazed fixed to it for the duration of the experiment.\n\n"
                        "You will then be presented with a series of tones: "
                        "your task is to pay attention to whether any of the tones is presented at a different timing interval to the rest.\n\n "
                        "If you think you hear a tone that is presented at a different interval, please press any key with the number 1, 2, 3, or 4.\n\n"
                        "Thank you for your attention! \n\n \n\n You may now press the space bar to being."),
    "REST_HEADING" : "Time to take a break",
    "REST_TEXT"    : f"Please feel free to rest for max 2 min. You could even step outside for a moment.\n\n "
                      "Once you're ready to continue, put the headphones on and press the spacebar.",
    "END_HEADING"  : "The End of the Experiment", 
    "END_TEXT"     : "Thank you so much for your participation!\n\n",
}

#5: INITIALIZE EXPERMIENT
sesh = input("Enter the session number with leading zero (e.g.: 01, 02, ...):")
exp  = design.Experiment(name = "timingDev")
control.initialize(exp)

# Set variables to be saved
exp.add_data_variable_names(['SUB_ID', 'SESSION_NO', 'BLOCK_NO', 'TRIAL_NO', 
                             'NO_TONES', 'TONE_IDX', 'ISI', 'DELTA', 'RESPONSE', 'RT'])

# Get current time for unique ID of output files
now = datetime.now() 
ts  = int(now.timestamp()) 

#6:CREATE STIMULI
# Create general experiment features and preload them for faster presentation
keyboard = io.Keyboard()

cross  = stimuli.FixCross(size       = params["FIXATION_CROSS_SIZE"],
						  position   = params["FIXATION_CROSS_POSITION"], 
						  line_width = params["FIXATION_CROSS_WIDTH"],
                          colour     = params["WHITE"])
cross.preload()

instructions = stimuli.TextScreen(heading = params["INTRO_HEADING"], heading_size = params["HEADING_SIZE"], heading_colour = params["WHITE"],
                                  text = params["INTRO_TEXT"],       text_size = params["TEXT_SIZE"],       text_colour = params["WHITE"], )
instructions.preload()

rest = stimuli.TextScreen(heading = params["REST_HEADING"], heading_size = params["HEADING_SIZE"], heading_colour = params["WHITE"],
                          text = params["REST_TEXT"],       text_size = params["TEXT_SIZE"],       text_colour =  params["WHITE"], )
rest.preload()

goodbye_message = stimuli.TextScreen(heading = params["END_HEADING"], heading_colour = params["WHITE"], heading_size = params["HEADING_SIZE"],
                                     text = params["END_TEXT"],       text_colour = params["WHITE"],    text_size = params["TEXT_SIZE"])
goodbye_message.preload()

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
no_empty   = aboveT - belowT
if no_empty > 0:
    possible_empty = np.setdiff1d(np.arange(-params_interest["threshold"], params_interest["threshold"], dtype = np.int64), deltas)
    empty  = np.random.choice(possible_empty, size = no_empty, replace = False)
    deltas = np.concatenate([deltas, empty])
deltas = np.sort(deltas)

# Generate core sound stimuli
sound_gen = sg.SoundGen(params["SAMPLE_RATE"], params["TAU"]) 

#7: RUN EXPERIMENT 
control.start(skip_ready_screen = True)

# Rename output data 
exp.data.rename(f"sub-{exp.subject:02d}_ses-{sesh}_task-{exp.name}_ts-{ts}.tsv")   
exp.events.rename(f"sub-{exp.subject:02d}_ses-{sesh}_task-{exp.name}_ts-{ts}.tsv") 

# Present instructions and wait a minimal time needed to read instructions.
instructions.present()
exp.clock.wait(params["WAIT_TIME"])
keyboard.wait(keys = [misc.constants.K_SPACE])
cross.present()

# Randomize the order of ISI in blocks per experimental session (run)
random.shuffle(isi_list)

for block, current_isi in enumerate(isi_list):

    # Shuffle deltas per block
    random.shuffle(deltas)

    for trial, current_delta in enumerate(deltas):
        cross.present()

        sequence, tone_idx, duration = sound_gen.generate_sequence(
                                          params["TONE_FREQUENCY"],
                                          params["MAX_AMPLITUDE"],
                                          params["NUM_HARMONICS"], 
                                          params["TONE_DURATION"],
                                          params["HARMONIC_FACTOR"],
                                          current_isi, 
                                          params["NO_TONES"], 
                                          current_delta
                                          )
        
        # Clearing any key presses before playing the sound 
        keyboard.clear()
        
        # Play the generated sound sequence
        start_time = exp.clock.time
        key, rt = None, None
        sd.play(sequence, params["SAMPLE_RATE"],  blocking = False)

        while (exp.clock.time - start_time) < ((duration/params["SAMPLE_RATE"]) * 1000):
            keys = keyboard.read_out_buffered_keys()
            if keys:
                rt = exp.clock.time - start_time / 1000 # sec
                key = keys[0]

        # Wait until the sound has finished playing 
        sd.wait()                           
        
        # Save data per trial
        if key == None:
           exp.data.add([exp.subject, sesh, block + 1, trial + 1, params["NO_TONES"], 
                         tone_idx, current_isi, current_delta, None, rt])
        else:
           exp.data.add([exp.subject, sesh, block + 1, trial + 1, params["NO_TONES"],
                         tone_idx, current_isi, current_delta, chr(key), rt])

        # Wait to distinguish trials
        if trial != len(deltas) - 1:
            exp.clock.wait(params["ITI"])

    # At the end of each block, give time to rest (works as inter-block-interval)
    if block != len(isi_list) - 1:
        rest.present()
        keyboard.wait(keys = [misc.constants.K_SPACE])

goodbye_message.present()
exp.clock.wait(params["WAIT_TIME"])

#8: END EXPERIMENT
control.end()