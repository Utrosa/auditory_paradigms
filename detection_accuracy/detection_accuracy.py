#! /usr/bin/env python
# Time-stamp: <2026-03-16 m.utrosa@bcbl.eu>

# 01. PREPARATION ---------------------------------------------------------------------------------

# Import python packages
import random
import pandas as pd
from pathlib import Path
from expyriment import design, control, stimuli, io, misc

# Import custom-made functions
import create_soundtrack_expyriment

# Set developping mode: developping == True / testing == False.
control.set_develop_mode(on=True)

# 02. LOAD PARAMETERS COMBO -----------------------------------------------------------------------
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
	"TONE_SAMPLERATE" : 48000,  # Change depending on the speakers
	"TONE_BITDEPTH" : 16,       # Change depending on the speakers

	# Colors in RGB
	"BLACK"  : (0, 0, 0),	    # screen background
	"WHITE"  : (255, 255, 255), # fixation cross
	"GREEN"  : (50, 205, 50),   # correct response
	"RED"    : (204, 0, 0),     # incorrect reponse
	"CYAN"   : (0,255,255),     # correct for colorblind
	"ORANGE" : (255,165,0),     # incorrect for colorblind

	# Experiment Structure
	"NO_RUNS" : 4,
	"ITI" : 1500,     		 # Inter Trial Interval (time between two sequences, i.e., trials)       
					  		 # Should be longer than the largest ISI and DEV.
	"NO_TRIALS" : 10,		 # The number of trial repetitions. A trial is a single tone sequence.
	
	# ISI: Inter Stimulus Interval (time between presentation of two sequential tones).
	"ISI_MIN": 700, # Minimum duration of ISI (inclusive)
	"ISI_MAX": 701, # Maximum duration of ISI (exclusive)
	"ISI_NO" : 1,   # How many ISI values to test?
	
	# Deviations
	"DEV_MIN": 1,   # Minimum tone timing deviation (inclusive) 
	"DEV_MAX": 300, # Maximum tone timing deviation ISI (exclusive)
	"DEV_NO" : 64,  # How many deviations to test? !!! TODO: this is not accurate as we correct for no signal trials to calculate sensitivity!!
	}
homePath  = Path("/home/mutrosa/Documents/projects/auditory_paradigms/detection_accuracy/")
paramPath = homePath / "out" / "exp_parameter_combo_ses-002.csv"
df = pd.read_csv(paramPath)

# 03. STRUCTURE THE EXPERIMENT --------------------------------------------------------------------
no_runs   = len(df["RUN_NO"].unique())
no_trials = len(df["TRIAL_NO"].unique())

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
canvas = stimuli.Canvas(size = params["CANVAS_SIZE"], colour = params["BLACK"])
cross  = stimuli.FixCross(
	size = params["FIXATION_CROSS_SIZE"],
	position = params["FIXATION_CROSS_POSITION"],
	line_width = params["FIXATION_CROSS_WIDTH"],
	colour = params["WHITE"]
	)
cross.preload()
cross.plot(canvas) # Plot on canvas now, less to do later
canvas.preload()
soundtrack = create_sequences(
	tone,
	df,
	params["TONE_SAMPLERATE"],
	params["TONE_BITDEPTH"], 
	save_audio=False
	)

# Set up data storage
exp.add_data_variable_names(['TRIAL_NO', 'NO_TONES', 'DEV', 'DEV_TYPE', 'DEV_LOC', 'ISI', 'RESPONSE'])

# 06. RUN THE EXPERIMENT ---------------------------------------------------------------------------
control.start(skip_ready_screen=True)

# Show the instructions and wait for the participant to read the instructions.
instructions.present()
keyboard.wait(keys=[misc.constants.K_2])

canvas.present()

# Wait for the MRI scanner signal the start of functional sequence to sync the task.
keyboard.wait(keys=[misc.constants.K_s])

# Start the task after the 4th trigger. One "s" trigger per TR "trigger".
keyboard.wait(keys=[misc.constants.K_s])
keyboard.wait(keys=[misc.constants.K_s])
keyboard.wait(keys=[misc.constants.K_s])
keyboard.wait(keys=[misc.constants.K_s])

for cr, r in enumerate(soundtrack):
	
	for cs, s in enumerate(r):

		# Enable ESCAPE
		keyboard.check(keys=[misc.constants.K_ESCAPE])
		
		# s.save(f"sound-{cs+1}_run-{cr+1}.wav")
		s.play()
		s.wait_end()
	
	exp.clock.wait(5000) # pause between runs

# 07. END THE EXPERIMENT --------------------------------------------------------------------------
control.end()