#! /usr/bin/env python

# PREPARATION -----------------------------------------------------------------------------

## Start by importing the neccesary modules and packages. If you do not have the python packages
## installed on your laptop, you can install them with: pip install {package name}.
import random
import pandas as pd
import numpy as np
from itertools import product
from expyriment import design, control, stimuli, io, misc

control.set_develop_mode(on=True) # SET MODE: developping == True / testing == False.

# FUNCTIONS --------------------------------------------------------------------------------
def create_and_preload_tones(trials, tone_duration, tone_frequency, tone_samplerate, tone_bitdepth):
    tones_by_trial = []

    for trial in trials:
        no_tones = trial[0]

        trial_tones = []
        for _ in range(no_tones):
        	tone = stimuli.Tone(tone_duration, tone_frequency, tone_samplerate, tone_bitdepth)
        	tone.preload()
        	trial_tones.append(tone)

        tones_by_trial.append(trial_tones)  # Store all tones for the trial

    return tones_by_trial

# PARAMETERS -------------------------------------------------------------------------------
params = {

	# Visual
	"CANVAS_SIZE" : (1920, 1080), # monitor resolution

	"FIXATION_CROSS_SIZE"     : (20, 20),
	"FIXATION_CROSS_POSITION" : (0, 0),
	"FIXATION_CROSS_WIDTH"    : 4,

	# Audio
	"MIN_TONES": 3, # min. no. of tones in a single sequence
	"MAX_TONES" : 7,
	"TONE_DURATION" : 50,
	"TONE_FREQUENCY" : 440,
	"TONE_SAMPLERATE" : 48000, # Change depending on the speakers!!
	"TONE_BITDEPTH" : 16,       # Change depending on the speakers!!

	# Colors in RGB
	"BLACK" : (0, 0, 0),	   # screen background
	"WHITE" : (255, 255, 255), # fixation cross
	"GREEN" : (50,205,50),     # correct response
	"RED"   : (204,0,0),       # incorrect reponse
}

# EXPERIMENT STRUCTURE ----------------------------------------------------------------------

# NO_TRIALS: Number of trial repetitions. A trial is a sequence of tones.
# ITI: Inter Trial Interval (time between two sequences, i.e., trials).
NO_TRIALS = 2
ITI = 300 # msec

# NO_TONES: Integer number of sounds in the sequence.
# DEV: Absolute size of tone's timing deviation in milliseconds.
# DEV_TYPE: Type of deviation (early or late).
# DEV_LOC: Position of the timing deviation in the sequence.
# ISI: Inter Stimulus Interval (time between presentation of two sequential tones).
DEV = random.sample(range(0, 1001), 1000)
NO_TONES = random.sample(range(params["MIN_TONES"], params["MAX_TONES"]), params["MAX_TONES"] - params["MIN_TONES"])
DEV_TYPE = ['early', 'late']
DEV_LOC = random.sample(range(params["MIN_TONES"] + 1, params["MAX_TONES"]), params["MAX_TONES"] - (params["MIN_TONES"] + 1)) # First three tones are never displaced.
ISI = random.sample(range(50, 250), NO_TRIALS) # By intuition, I think 50 msec ISI should be long enough to hear sound as separate but see Abel & MTD studies ----- TO-DO

# ALL_COMBOS: List of tuples. The tuple contains NO_TONES, ISI, DEV, DEV_TYPE, DEV_LOC. The list
# contains all posible combinations of these parameters. Trials are randomly sampled from it on 
# each run of the experiment.

ALL_COMBOS = list(product(NO_TONES, DEV, DEV_TYPE, DEV_LOC, ISI))
# Constraint: location of deviation has to match number of tones in the sequence
FILTERED_COMBOS = [combo for combo in ALL_COMBOS if combo[1] <= combo[0]]
random.shuffle(FILTERED_COMBOS)

# TRIALS: a sequence of tones, repecting the parameters given in the tuple of FILTERED_COMBOS.
# During each trial, the code is "listening for key presses." A green fixation cross is presented, 
# when a HIT occurs.
TRIAL_PARAMS = random.sample(FILTERED_COMBOS, NO_TRIALS) # Without replacement ;)

# INITIALIZE THE EXPERIMENT --------------------------------------------------------------------
exp = design.Experiment(name="Timing")
control.initialize(exp)

# CREATE & PRELOAD THE STIMULI -----------------------------------------------------------------
keyboard = io.Keyboard()
canvas   = stimuli.Canvas(size=params["CANVAS_SIZE"], colour=params["BLACK"]); canvas.preload()
cross = stimuli.FixCross(size=params["FIXATION_CROSS_SIZE"], position=params["FIXATION_CROSS_POSITION"], 
						 line_width=params["FIXATION_CROSS_WIDTH"], colour=params["WHITE"]); cross.preload()
tones_by_trial = create_and_preload_tones(TRIAL_PARAMS, params["TONE_DURATION"], params["TONE_FREQUENCY"], params["TONE_SAMPLERATE"], 
	                             params["TONE_BITDEPTH"])

# STORE DATA -----------------------------------------------------------------------------------
exp.add_data_variable_names(['TRIAL_NO', 'NO_TONES', 'DEV', 'DEV_TYPE', 'DEV_LOC', 'ISI'])

# RUN THE EXPERIMENT ---------------------------------------------------------------------------
control.start(skip_ready_screen=True)    # Start the experiment without the ready screen
keyboard.wait(keys=[misc.constants.K_s]) # Wait for S trigger from the MRI scanner

for rep, trial in enumerate(TRIAL_PARAMS):
	no_tones = trial[0]
	dev = trial[1]
	dev_type = trial[2]
	dev_loc = trial[3]
	isi = trial[4]
	trial_tones = tones_by_trial[rep]
	canvas.present()
	cross.present()
	exp.clock.wait(ITI)

	for count, t in enumerate(trial_tones):
		keyboard.check(keys=[misc.constants.K_ESCAPE]) # Enable stopping the exp. with ESC button
		# key = keyboard.check(keys=[misc.constants.K_1, misc.constants.K_2,  # Only the first occurrence is returned!
		# 							misc.constants.K_3, misc.constants.K_4]) # All possible keys on the MRI response pad.
	
		# For late tones, the ISI before the diplaced tone is longer, ISI after shorter.
		if dev_type == "late" and count == (dev_loc - 1): # ISI before
			t.present()
			exp.clock.wait(isi + dev)

		if dev_type == "late" and count == dev_loc: # ISI after
			t.present()
			exp.clock.wait(isi - dev)

		# For early tones, the ISI before the diplaced tone is shorter, ISI after longer.
		if dev_type == "early" and count == (dev_loc - 1):
			t.present()
			exp.clock.wait(isi - dev)

		if dev_type == "early" and count == dev_loc:
			t.present()
			exp.clock.wait(isi + dev)

		# For on-time tones, all ISI are the same.
		else:
			t.present()
			exp.clock.wait(isi)

	exp.data.add([rep + 1, no_tones, dev, dev_type, dev_loc, isi])

# END THE EXPERIMENT ----------------------------------------------------------------------------
control.end()