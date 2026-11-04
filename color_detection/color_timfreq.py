#! /usr/bin/env python
# Time-stamp: <04-11-2026, m.utrosa@bcbl.eu>
'''
Requires Expyriment version 1.0.0
'''
from expyriment import design, control, stimuli, misc, io
from config_timfreq import params, twitch
from pathlib import Path
import pandas as pd
import ast

# 01. USER-DEFINED PARAMETERS ------------------------------------------------------------
idx  = input("Enter the index of exp_parameter_combo csv:")
sesh = input("Enter the session number:")
comboID, sesID = int(idx), int(sesh)
control.set_develop_mode(on = params["DEVELOP_MODE"])

# 02. PRECOMPUTED PARAMETERS -------------------------------------------------------------
homePath  = Path(params["PROJECT_ROOT"])
paramPath = homePath / "tests" / f"ses-{comboID:03d}_exp_parameter_combo.csv"

# Load the dataframe and extract variables
df        = pd.read_csv(paramPath)
flash_rep = df["flash_rep"]
flash_isi = df["flash_isi"]
no_runs   = len(df["run_idx"].unique())

# Sort the trials are ordered by blocks & trials
df.sort_values(by=["run_idx"], inplace=True)

# 03. INITIALIZE THE EXPERIMENT ----------------------------------------------------------
# Settings to ensure that the window size fits the stimuli computer & projector in the MRI
control.defaults.opengl = 2 # OpenGL (vsync / blocking); default
control.defaults.display_resolution = params["CANVAS_SIZE"] # default is None
control.defaults.window_size = params["CANVAS_SIZE"] # relevant when running in window mode
control.defaults.window_no_frame = True              # relevant when running in window mode

# Initialize the experiment with a name following BIDS specification
exp = design.Experiment(name = "color_devLoc")
control.initialize(exp)

# 04. CREATE & PRELOAD THE STIMULI -------------------------------------------------------
keyboard = io.Keyboard()
clock    = misc.Clock()

canvas = stimuli.Canvas(size = params["CANVAS_SIZE"], colour = params["BLACK"])
blank_canvas = stimuli.Canvas(size = params["CANVAS_SIZE"], colour = params["BLACK"])

scanner_text = stimuli.TextScreen(
    params["MRI_HEADING"],
    params["MRI_TEXT"],
    heading_size=params["HEADING_SIZE"],
    heading_colour=params["WHITE"],
    text_size=params["TEXT_SIZE"],
    text_colour=params["WHITE"]
    )
instructions_loc = stimuli.TextScreen(
    params["INTRO_HEADING"] + "repetition detection experiment!",
    params["INTRO_TEXT_LOC"],
    heading_size=params["HEADING_SIZE"],
    heading_colour=params["WHITE"],
    text_size=params["TEXT_SIZE"],
    text_colour=params["WHITE"]
    )
instructions_task = stimuli.TextScreen(
    params["INTRO_HEADING"] + "counting experiment!",
    params["INTRO_TEXT_TASK"],
    heading_size=params["HEADING_SIZE"],
    heading_colour=params["WHITE"],
    text_size=params["TEXT_SIZE"],
    text_colour=params["WHITE"]
    )
goodbye_exp_message = stimuli.TextScreen(
    params["END_HEADING"],
    params["END_TEXT"],
    heading_size=params["HEADING_SIZE"],
    heading_colour=params["WHITE"],
    text_size=params["TEXT_SIZE"],
    text_colour=params["WHITE"]
    )

circle = stimuli.Circle(
	radius = params["FLASH_RADIUS"],
	colour = params["WHITE"],
	position = params["FLASH_POSITION"]
	)
fix_cross = stimuli.FixCross(
	size = params["FIXATION_CROSS_SIZE"], 
	position = params["FIXATION_CROSS_POSITION"], 
	line_width = params["FIXATION_CROSS_WIDTH"], 
	colour = params["WHITE"]
	)
wrong = stimuli.FixCross(
	size = params["FIXATION_CROSS_SIZE"], 
	position = params["FIXATION_CROSS_POSITION"], 
	line_width = params["FIXATION_CROSS_WIDTH"], 
	colour = params["WRONG"]
	)
correct = stimuli.FixCross(
	size = params["FIXATION_CROSS_SIZE"], 
	position = params["FIXATION_CROSS_POSITION"], 
	line_width = params["FIXATION_CROSS_WIDTH"], 
	colour = params["CORRECT"]
	)

# Plotting
fix_cross.plot(canvas)

# 05. RUN THE EXPERIMENT -----------------------------------------------------------------
control.start(skip_ready_screen=True)

## ---------------------------------------------------------------------------------------
## TWITCH COUNTING TASK
## ---------------------------------------------------------------------------------------
task_name = "counting"

# Present instructions for the counting task and wait a minimal time needed to read them.
instructions_task.present()
exp.clock.wait(params["WAIT_TIME"])
keyboard.wait(keys=params['DETECTION_SYMBOL'])

# Clear instructions and show a blank screen.
instructions_task.clear_surface()
blank_canvas.present()

# Check if quit key is pressed
keyboard.check(keys=[misc.constants.K_y])

# Wait for onset of the functional sequence for the main task
keyboard.wait(keys=[misc.constants.K_s])
canvas.present()

# Mark the start of the functional sequence for the main task
task_start_time = exp.clock.time

# Wait for 4 's' keys from the scanner to synchronize scanner & script onsets.
keyboard.wait(keys=[misc.constants.K_s]); keyboard.wait(keys=[misc.constants.K_s])
keyboard.wait(keys=[misc.constants.K_s]); keyboard.wait(keys=[misc.constants.K_s])

for index, value in flash_rep.items():

	# Check if quit key is pressed
	keyboard.check(keys=[misc.constants.K_y])

	# Track timing and twich when programmed
	if value > 0:
		for _ in range(value):
			twitch(
				flash = circle,
				flash_isi = int(flash_isi[index]),
				canvas = canvas,
				cross = fix_cross,
				clock = clock,
				keyboard = keyboard
				)

		# Wait for some time
		exp.clock.wait(100)
	else:
		pass

# Say thanks at the end of the counting task
goodbye_task_message = stimuli.TextScreen(
    params["TASK_END_HEADING"] + task_name + " task.",
    params["TASK_END_TEXT"],
    heading_size=params["HEADING_SIZE"],
    heading_colour=params["WHITE"],
    text_size=params["TEXT_SIZE"],
    text_colour=params["WHITE"]
)
goodbye_task_message.present()
exp.clock.wait(params["WAIT_TIME"])
goodbye_task_message.clear_surface() 

## ---------------------------------------------------------------------------------------
## LOCALIZER TASK
## ---------------------------------------------------------------------------------------
task_name = "localizer"
## ---------------------------------------------------------------------------------------
# Say thanks & goodbye to the participant
goodbye_exp_message.present()
exp.clock.wait(params["WAIT_TIME"])
goodbye_exp_message.clear_surface()
control.end()