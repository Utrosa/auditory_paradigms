#! /usr/bin/env python
# Time-stamp: <2025-04-09 m.utrosa@bcbl.eu>

# PREPARATION -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
## Start by importing the neccesary modules and packages. If you do not have the python packages installed on your laptop, you can install them with: pip install {package name}.
import random
import pandas as pd
import numpy as np
from itertools import product
from expyriment import design, control, stimuli, io, misc

## SET MODE: developping == True / testing == False.
control.set_develop_mode(on=True)

## FUNCTIONS
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

def calculate_trial_duration(trial_list, parameter_list):
	durations = []
	for combo in trial_list:	
		nodev_dur = combo[0] * parameter_list["TONE_DURATION"] + (combo[0] - 1) * combo[-1]
		if combo[2] == "early":
			duration =  nodev_dur - combo[1]
			durations.append(duration)
		elif combo[2] == "late":
			duration = nodev_dur + combo[1]
			durations.append(duration)
		else:
			durations.append(nodev_dur)
	return durations

## PARAMETERS -------------------------------------------------------------------------------
params = {

	# Visual
	"CANVAS_SIZE" : (1920, 1080), # Monitor resolution. PC: 1920, 1080. MRI: 1024, 768.
	"FIXATION_CROSS_SIZE"     : (20, 20),
	"FIXATION_CROSS_POSITION" : (0, 0),
	"FIXATION_CROSS_WIDTH"    : 4,
	"HEADING_SIZE" : 30, 
	"TEXT_SIZE"    : 20,
	"TEXT" 		   : f"Identify the sound that is displaced when hearing it. \n"
					  "Press a button to start.",

	# Audio
	"MIN_TONES": 3, # min. no. of tones in a single sequence
	"MAX_TONES" : 7,
	"TONE_DURATION" : 50,
	"TONE_FREQUENCY" : 440,
	"TONE_SAMPLERATE" : 48000,  # Change depending on the speakers
	"TONE_BITDEPTH" : 16,       # Change depending on the speakers

	# Colors in RGB
	"BLACK" : (0, 0, 0),	   # screen background
	"WHITE" : (255, 255, 255), # fixation cross
	"GREEN" : (50, 205, 50),   # correct response
	"RED"   : (204, 0, 0),     # incorrect reponse

	# Experiment Structure
	"ITI" : 1500, # Should be longer than the largest ISI and DEV.
	"NO_TRIALS" : 2,
	"TRIAL_DURATION" : 1109 # Should be shorter than ITI
}

# EXPERIMENT STRUCTURE ----------------------------------------------------------------------
# ITI: Inter Trial Interval (time between two sequences, i.e., trials).
# NO_TRIALS: Number of trial repetitions. A trial is a sequence of tones.
# NO_TONES: Integer number of sounds in the sequence.
# DEV: Absolute size of tone's timing deviation in milliseconds.
# DEV_TYPE: Type of deviation (early or late).
# DEV_LOC: Position of the timing deviation in the sequence.
# ISI: Inter Stimulus Interval (time between presentation of two sequential tones).

## List comprehensions for all possible values for two ranges of values & adding conditions (rather than removing from all_combos).
## Also, see how to define variables in one line with conditionals!

NO_TONES = random.sample(range(params["MIN_TONES"], params["MAX_TONES"]), params["MAX_TONES"] - params["MIN_TONES"])
DEV      = np.random.randn(1,3) # SEE PYTHON COURSE 4
DEV_TYPE = ['early', 'on_time', 'late']
DEV_LOC  = random.sample(range(params["MIN_TONES"] + 1, params["MAX_TONES"]), params["MAX_TONES"] - (params["MIN_TONES"] + 1)) # First three tones are never displaced.
DEV_LOC.insert(0, 0) # Include a location 0 for cases where there is no deviation in the sequence.
ISI      = random.sample(range(60, 600), 3)

# ALL_COMBOS: List of tuples. The tuple contains NO_TONES, DEV, DEV_TYPE, DEV_LOC, and ISI.
# The list contains all posible combinations of these parameters. 
# FILTERED_COMBOS: ALL_COMBOS with constraints.
	# The location of deviation has to be <= to the number of tones in the sequence.
	# If DEV == 0, then DEV_TYPE has to be "on_time" and DEV_LOC has to be "None".
	# If DEV != 0, then DEV_LOC cannot be 0.
	# Fixed duration of trials. 
	# duration = no_tones * tone_duration + (no_tones - 1) * ISI +/- dev
# TRIAL_PARAMS: a sequence of tones, repecting the parameters given in the tuple of FILTERED_COMBOS.
ALL_COMBOS = list(product(NO_TONES, DEV, DEV_TYPE, DEV_LOC, ISI))
VALID_COMBOS = [combo for combo in ALL_COMBOS if combo[3] <= combo[0]]
# VALID_COMBOS = [combo for combo in FILTERED_COMBOS if not (

#         (combo[2] == "on_time" & (combo[1] != 0 or combo[3] != 0)) or
#         (combo[2] != "on_time" & (combo[1] == 0 or combo[3] == 0)) or
#         (combo[1] == 0 & (combo[2] != "on_time" or combo[3] != 0)) or
#         (combo[3] == 0 & combo[1] != 0) or
#         (combo[3] == 0 & combo[2] != 0) or
#         (combo[3] != 0 & combo[1] == 0) or
#         (combo[3] != 0 & combo[2] == 0) or
#         (combo[2] == 0 & combo[1] != 0) or
#         (combo[2] != 0 & combo[1] == 0) or                      
#     	(((combo[0] * params["TONE_DURATION"] + (combo[0] - 1) * combo[-1]) - combo[1]) <= 0) or
#     	(combo[2] == "early" and combo[-1] > combo[1]) or
#     	(combo[2] == "late" and combo[-1] > combo[1])
#     )
# ]

COMBO_DURATIONS = calculate_trial_duration(VALID_COMBOS, params)
print(np.unique(COMBO_DURATIONS.all()))
random_trial_duration = random.sample(list(set(COMBO_DURATIONS)), 1)
VALID_COMBOS_EQUAL_LENGTH = [combo for i, combo in enumerate(VALID_COMBOS) if COMBO_DURATIONS[i] == random_trial_duration[0]]

# random.shuffle(VALID_COMBOS)
TRIAL_PARAMS = random.sample(VALID_COMBOS_EQUAL_LENGTH, params["NO_TRIALS"]) # Without replacement ;) ----------------- USE ALL COMBINATIONS

# INITIALIZE THE EXPERIMENT --------------------------------------------------------------------
exp = design.Experiment(name="Timing")
control.initialize(exp)

# CREATE & PRELOAD THE STIMULI -----------------------------------------------------------------
keyboard = io.Keyboard()
instructions = stimuli.TextScreen("Instructions", params["TEXT"], heading_size = params["HEADING_SIZE"], text_size = params["TEXT_SIZE"])
instructions.preload()
canvas = stimuli.Canvas(size = params["CANVAS_SIZE"], colour = params["BLACK"]); canvas.preload()
cross  = stimuli.FixCross(size = params["FIXATION_CROSS_SIZE"], position = params["FIXATION_CROSS_POSITION"], 
						 line_width = params["FIXATION_CROSS_WIDTH"], colour = params["WHITE"]); cross.preload()
tones_by_trial = create_and_preload_tones(TRIAL_PARAMS, params["TONE_DURATION"], params["TONE_FREQUENCY"], 
										  params["TONE_SAMPLERATE"], params["TONE_BITDEPTH"])

# STORE DATA -----------------------------------------------------------------------------------
exp.add_data_variable_names(['TRIAL_NO', 'NO_TONES', 'DEV', 'DEV_TYPE', 'DEV_LOC', 'ISI', 'RESPONSE'])

# RUN THE EXPERIMENT ---------------------------------------------------------------------------
control.start(skip_ready_screen=True)    # Start the experiment without the ready screen
instructions.present()
keyboard.wait(keys=[misc.constants.K_2]) # Press no. 2 when you read the instructions.
keyboard.wait(keys=[misc.constants.K_s]) # Wait for S trigger from the MRI scanner. One S per TR.

# Loop through trials
for rep, trial in enumerate(TRIAL_PARAMS):
	no_tones = trial[0]
	dev = trial[1]
	dev_type = trial[2]
	dev_loc = trial[3]
	isi = trial[4]
	trial_tones = tones_by_trial[rep]
	canvas.present()
	cross.present()
	exp.clock.wait(params["ITI"])

	# During each trial, the code is "listening for key presses."
	key = keyboard.check(keys=[misc.constants.K_1, misc.constants.K_2,
			misc.constants.K_3, misc.constants.K_4])

	# Play sequence ------ a soundwave in memory ----------------------------------------------- TO - D0
	for count, t in enumerate(trial_tones):
		keyboard.check(keys=[misc.constants.K_ESCAPE]) # Enable stopping the exp. with ESC button

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
	
	# Save data
	if key == None:
		exp.data.add([rep + 1, no_tones, dev, dev_type, dev_loc, isi, key])
	else:
		exp.data.add([rep + 1, no_tones, dev, dev_type, dev_loc, isi, chr(key)]) # Conver ASCII to character

# END THE EXPERIMENT ----------------------------------------------------------------------------
control.end()