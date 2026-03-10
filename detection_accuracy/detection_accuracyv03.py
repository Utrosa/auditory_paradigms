#! /usr/bin/env python
# Time-stamp: <2026-03-09 m.utrosa@bcbl.eu>

# 00. PREPARATION ---------------------------------------------------------------------------------
## Start by importing the neccesary modules and packages. If you do not have the python packages
## installed on your laptop, you can install them with: pip install {package name}.
import random
import numpy as np
from itertools import product
from expyriment import design, control, stimuli, io, misc

control.set_develop_mode(on=True) # developping == True / testing == False.

# 01. DEFINE FUNCTIONS  ---------------------------------------------------------------------------
def calculate_trial_duration(trial_list, parameter_list):
	"""
	Calculates duration in ms for each trial combination.
	"""
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

def create_deviations(num_values, min_val, max_val):

	# Generate logarithmic values between 1 and 500
	log_values = np.logspace(np.log10(min_val), np.log10(max_val), 2000)

	# Bias weights: strongly favor higher values, but keep small chance for low ones
	x = np.linspace(0, 1, len(log_values))
	weights = (x ** 4) + 0.001  # steeper bias (x**4 makes small values rarer)
	weights /= weights.sum()

	# Randomly sample up to 50 unique values
	chosen = np.random.choice(log_values, size=num_values, replace=False, p=weights)

	# Round to integers and sort
	chosen = np.sort(np.unique(np.rint(chosen).astype(int)))
	chosen = [ch for ch in chosen]
	return chosen

# 02. SET PARAMETERS ------------------------------------------------------------------------------
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
	"MIN_TONES": 3,             # min. no. of tones in a single sequence
	"MAX_TONES" : 7,            # max. no. of tones in a single sequence
	"TONE_DURATION" : 50,       # msec
	"TONE_FREQUENCY" : 440,     # TO-DO: changing frequency
	"TONE_SAMPLERATE" : 44100,  # Change depending on the speakers
	"TONE_BITDEPTH" : 16,       # Change depending on the speakers

	# Colors in RGB
	"BLACK"  : (0, 0, 0),	    # screen background
	"WHITE"  : (255, 255, 255), # fixation cross
	"GREEN"  : (50, 205, 50),   # correct response
	"RED"    : (204, 0, 0),     # incorrect reponse
	"CYAN"   : (0,255,255),     # correct for colorblind
	"ORANGE" : (255,165,0),     # incorrect for colorblind

	# Experiment Structure
	"ITI" : 1500,            # Should be longer than the largest ISI and DEV.
	"NO_TRIALS" : 10,
	"NO_RUNS" : 4,
	"TRIAL_DURATION" : 1100, # Should be shorter than ITI
	"RUN_DURATION": 60000,   # 10 min in msec
	"MIN_RUN_DURATION": 54000,
	"ISI_MIN": 700, # Minimum duration of ISI
	"ISI_MAX": 701, # Maximum duration of ISI
	"ISI_NO" : 1,   # How many ISI values to test?
	"DEV_MIN": 1,   # Minimum tone timing deviation 
	"DEV_MAX": 300, # Maximum tone timing deviation ISI
	"DEV_NO" : 64,  # How many deviations to test?

	}

# 03. STRUCTURE THE EXPERIMENT --------------------------------------------------------------------
# ITI: Inter Trial Interval (time between two sequences, i.e., trials).
# NO_TRIALS: Number of trial repetitions. A trial is a sequence of tones.
# NO_TONES: Integer number of sounds in the sequence.
# DEV: Absolute size of tone's timing deviation in milliseconds.
# DEV_TYPE: Type of deviation (early or late).
# DEV_LOC: Position of the timing deviation in the sequence.
#		   The first three tones are never displaced & the last one neither.
# ISI: Inter Stimulus Interval (time between presentation of two sequential tones).
NO_TONES = random.sample(
	range(params["MIN_TONES"],params["MAX_TONES"]),
	params["MAX_TONES"] - params["MIN_TONES"]
	)
DEV      = create_deviations(params["DEV_NO"], params["DEV_MIN"], params["DEV_MAX"])
DEV.insert(0, 0) # Have to add here because the log can't be 0 (logarithmically creating devs)
DEV_TYPE = ['early', 'on_time', 'late']
DEV_LOC  = random.sample(
	range(params["MIN_TONES"] + 1, params["MAX_TONES"]),
	params["MAX_TONES"] - (params["MIN_TONES"] + 1)
	)
DEV_LOC.insert(0, 0) # Include a location 0 for cases where there is no deviation in the sequence.
ISI      = random.sample(range(params["ISI_MIN"], params["ISI_MAX"]), params["ISI_NO"])

# ALL_COMBOS: A list of tuples with all posible combinations of the above parameters.
ALL_COMBOS = list(product(NO_TONES, DEV, DEV_TYPE, DEV_LOC, ISI))

# VALID_COMBOS: removing invalid parameter combinations and adding constraints.
VALID_COMBOS = []

for combo in ALL_COMBOS:
    no_tones  = combo[0]
    deviation = combo[1]
    dev_type  = combo[2]
    dev_loc   = combo[3]
    isi       = combo[4]

    # dev_loc cannot exceed no_tones
    if dev_loc > no_tones:
        continue

    # If DEV == 0, then DEV_TYPE must be "on_time" and DEV_LOC must be 0
    if deviation == 0:
        if dev_type != "on_time" or dev_loc != 0:
            continue

    # If DEV != 0, then DEV_LOC cannot be 0 (and type cannot be "on_time")
    if deviation != 0:
        if dev_loc == 0 or dev_type == "on_time":
            continue

    # ISI has to be longer than the deviation
    if isi < np.abs(deviation): 
        continue

    # Fixed duration must remain positive
    # duration = no_tones * tone_duration + (no_tones - 1) * ISI +/- dev
    base_duration = (no_tones * params["TONE_DURATION"]) + ((no_tones - 1) * isi)
    
    # Check if the resulting duration is non-positive
    if (base_duration - deviation) <= 0:
        continue

    # If all checks pass, add to list
    VALID_COMBOS.append(combo)

COMBO_DURATIONS = calculate_trial_duration(VALID_COMBOS, params)
paired_trials = list(zip(VALID_COMBOS, COMBO_DURATIONS))
random.shuffle(paired_trials)

# TRIAL_COMBOS: a random sample of no_trials per run.
# RUN_COMBOS: a list of lists (trials)
RUN_COMBOS = []
for run in range(params["NO_RUNS"]):
	TRIAL_COMBOS = random.sample(VALID_COMBOS, params["NO_TRIALS"])
	RUN_COMBOS.append(TRIAL_COMBOS)

# 04. INITIALIZE THE EXPERIMENT -------------------------------------------------------------------
exp = design.Experiment(name="timingDev")
control.initialize(exp)

# 05. CREATE & PRELOAD THE STIMULI ----------------------------------------------------------------
keyboard = io.Keyboard()
instructions = stimuli.TextScreen(
	"Instructions", params["TEXT"],
	heading_size = params["HEADING_SIZE"],
	text_size = params["TEXT_SIZE"]
	)
instructions.preload()
canvas = stimuli.Canvas(size = params["CANVAS_SIZE"], colour = params["BLACK"]); canvas.preload()
cross  = stimuli.FixCross(
	size = params["FIXATION_CROSS_SIZE"],
	position = params["FIXATION_CROSS_POSITION"],
	line_width = params["FIXATION_CROSS_WIDTH"],
	colour = params["WHITE"]
	)
cross.preload()

tone = stimuli.Tone(
	params["TONE_DURATION"],
	params["TONE_FREQUENCY"],
	params["TONE_SAMPLERATE"],
	params["TONE_BITDEPTH"]
	)
tone.preload()

# Set up data storage
exp.add_data_variable_names(['TRIAL_NO', 'NO_TONES', 'DEV', 'DEV_TYPE', 'DEV_LOC', 'ISI', 'RESPONSE'])

# 06. RUN THE EXPERIMENT ---------------------------------------------------------------------------
control.start(skip_ready_screen=True)


# Loop through runs
for TRIAL_PARAMS in RUN_COMBOS:

	# Show the instructions and wait for the participant to read the instructions.
	instructions.present()
	keyboard.wait(keys=[misc.constants.K_2])

	canvas.present()
	cross.present()

	# Wait for the MRI scanner signal the start of functional sequence to sync the task.
	keyboard.wait(keys=[misc.constants.K_s])

	# Start the task after the 4th trigger. One "s" trigger per TR "trigger".
	keyboard.wait(keys=[misc.constants.K_s])
	keyboard.wait(keys=[misc.constants.K_s])
	keyboard.wait(keys=[misc.constants.K_s])
	keyboard.wait(keys=[misc.constants.K_s])

	# Loop through trials
	for rep, trial in enumerate(TRIAL_PARAMS):
		if rep < len(TRIAL_PARAMS) and rep > 0:
			exp.clock.wait(params["ITI"]) # Time to wait between trials

		no_tones = trial[0]
		dev      = trial[1]
		dev_type = trial[2]
		dev_loc  = trial[3]
		isi      = trial[4]

		# Play sequence
		for count in range(no_tones):
			
			tone.present()
			current_isi = isi

			# For late tones, the ISI before the diplaced tone is longer, ISI after shorter.
			if dev_type == "late":
				if count == (dev_loc - 1): # ISI before
					current_isi = isi + dev
				elif count == dev_loc: # ISI after
					current_isi = isi - dev

			# For early tones, the ISI before the diplaced tone is shorter, ISI after longer.
			elif dev_type == "early":
				if count == (dev_loc - 1):
					current_isi = isi - dev
				elif count == dev_loc:
					current_isi = isi + dev

			exp.clock.wait(current_isi)
		
		# Save data
		key = None
		if key == None:
			exp.data.add([rep + 1, no_tones, dev, dev_type, dev_loc, isi, key])
		else:
			exp.data.add([rep + 1, no_tones, dev, dev_type, dev_loc, isi, chr(key)])

# 07. END THE EXPERIMENT --------------------------------------------------------------------------
control.end()