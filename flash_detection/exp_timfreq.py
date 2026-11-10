#! /usr/bin/env python
# Time-stamp: <05-11-2026, m.utrosa@bcbl.eu>
'''
Requires Expyriment version 1.0.0
TODO: integrate feedback with max response time
TODO: log events
TODO: test timing of events
TODO: max response period is the minimum separation of two flashes
'''
from expyriment import design, control, stimuli, misc, io
from config_timfreq import params, twitch, feedback_flash
import config_timfreq as c
from pathlib import Path
import pandas as pd
import ast

# 01. USER-DEFINED PARAMETERS ------------------------------------------------------------
idx  = input("Enter the index of exp_parameter_combo csv:")
sesh = input("Enter the session number:")
comboID, sesID = int(idx), int(sesh)
control.set_develop_mode(on = params["DEVELOP_MODE"])

# 02. PRECOMPUTED PARAMETERS -------------------------------------------------------------
tonesPath = c.outPath / f"ses-{comboID:03d}_exp_parameter_combo.csv"
flashPath = c.outPath / f"ses-{comboID:03d}_exp_distractor_combo.csv"

# Load the dataframe
df_tones = pd.read_csv(tonesPath)
df_flash = pd.read_csv(flashPath)
no_runs  = len(df_tones["run_idx"].unique())

# Load audio files for the current session and sort by run number
main_task_wavs = list(c.outPath.glob("**/*.wav"))
main_task_audio = [file_1 for file_1 in main_task_wavs if f"ses-{sesID:02d}" in str(file_1)]
main_task_audio.sort()

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
# Handles
keyboard = io.Keyboard()
clock    = misc.Clock()

# Text
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
scanner_text.preload(); goodbye_exp_message.preload()
instructions_loc.preload(); instructions_task.preload()

# Screen and Visuals
canvas = stimuli.Canvas(
	size = params["CANVAS_SIZE"],
	colour = params["BLACK"]
	)
blank_canvas = stimuli.Canvas(
	size = params["CANVAS_SIZE"],
	colour = params["BLACK"]
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
wrong.preload()
correct.preload()

# Plotting
fix_cross.plot(canvas)

# Audio files for main task
main_audio = {mta.stem.split(f"ses-{sesID:02d}_")[1]: stimuli.Audio(str(mta)) for mta in main_task_audio}
for s in main_audio.values():
    s.preload()

# 05. RUN THE EXPERIMENT -----------------------------------------------------------------
control.start(skip_ready_screen=True)

## ---------------------------------------------------------------------------------------
## TWITCH COUNTING TASK
## ---------------------------------------------------------------------------------------
task_name = "counting"

# Present instructions for the counting task and wait a minimal time needed to read them.
instructions_task.present()
exp.clock.wait(params["READING_TIME"])
keyboard.wait(keys=params['DETECTION_SYMBOL'])

# Clear instructions and show a blank screen.
instructions_task.clear_surface()
blank_canvas.present()

# Loop through the runs
# Would be equivalent to looping through main_audio because there is one audio per run.
for run in range(no_runs):
	
	# Initialize variables to track performance on run-level
	run_performance = {"CORRECT": 0, "INCORRECT": 0}

	# Extract variables specific to the current run
	run_idx = run + 1
	flash_rep = df_flash[df_flash["run_idx"] == run_idx]["flash_rep"]
	flash_isi = df_flash[df_flash["run_idx"] == run_idx]["flash_isi"]
	main_audio_values = main_audio.get(f"run_{run_idx:02d}")

	# Check if quit key is pressed
	keyboard.check(keys=[misc.constants.K_y])

	# Wait for onset of the functional sequence
	keyboard.wait(keys=[misc.constants.K_s])
	canvas.present()

	# Mark the start of the functional sequence # TODO: may be obsolete
	task_start_time = exp.clock.time

	# Wait for 4 's' keys from the scanner to synchronize scanner & script onsets.
	keyboard.wait(keys=[misc.constants.K_s]); keyboard.wait(keys=[misc.constants.K_s])
	keyboard.wait(keys=[misc.constants.K_s]); keyboard.wait(keys=[misc.constants.K_s])
	
	# Play the sequence
	run_start_time = exp.clock.time - task_start_time
	
	# While playing the main task audiofile, flash the disk
	main_audio_values.play()
	while main_audio_values.is_playing: # TODO: When this ends, so should the disk flashing
		print(f"RUN:{run}")
		print(f"{flash_rep.head()}\n")
		for index, value in flash_rep.items():
			print(value)
			if value > 0:
				print(f"Start loop: {clock.time}")
				exp.clock.wait(par["FLASH_WAIT_TIME"])
				print(f"Start twitch: {clock.time}")

				# Refresh the screen
				canvas.present()

				# Check if quit key is pressed
				keyboard.check(keys=[misc.constants.K_y])

				# Twitch
				for _ in range(value):
					twitch(
						flash = circle,
						flash_isi = int(flash_isi[index]),
						canvas = canvas,
						cross = fix_cross,
						clock = clock,
						keyboard = keyboard
						)
				print(f"End twitch: {clock.time}")
				
				# Collect responses only if twitched & within max response period
				response, rt, perfo_code = None, None, None
				response_time_start = clock.time

				# Check for key presses with max response time
				while clock.time - response_time_start < par["MAX_RESPONSE_TIME"]:

					# Non-blocking function to check for pressed keys
					keys = keyboard.read_out_buffered_keys()

					if keys and keys[0] != 115:  # 115 is "s" from scanner sync box
						response = keys[-1]      # If multiple, we take the last key

						# Get reaction time
						rt = (clock.time - response_time_start) / 1000			
						break

				# Show feedback only if flash was presented
				print(f"Start feedback function: {clock.time}")
				perfo_code, run_performance = feedback_flash(
					value,       # Actual number of flashes
					response,    # Participant's count
					correct,     # Fixation cross for correct responses
					wrong        # Fixation cross for incorrect responses
					)
				
				print(f"Value: {value}; ISI: {flash_isi[index]}")
				print(f"Response: {response}")
				print(f"Feedback: {perfo_code}")
				print(f"End feedback function: {clock.time}")

				# Refresh the screen after max time for seeing feedback
				# feedback_time_start = clock.time
				# while clock.time - feedback_time_start > max_feedback_time:
				# 	keyboard.check(keys=[misc.constants.K_y]) # Check for quit key
				# 	canvas.clear_surface()
				# 	canvas.present() # Refresh the screen
				# print(f"End: {clock.time}\n\n")

				# TODO: Log with correction of the response for MRI buttons (1 is 0 devs, ...)
				# 		Although this is already maybe done in feedback_flash()

	# If the main task ends before the MRI protocol, instruct the participant to
	# keep calm and remain still.
	blank_canvas.present()
	scanner_text.present()

	# Wait for the MRI QU to end the run by pressing a key unavailable to the participant.
	keyboard.wait(keys=[misc.constants.K_e])

	# When the MRI QU signals acquistion end, show text with performance updates.
	mainTask_performance = f'Correct: {run_performance["CORRECT"]}, Wrong: {run_performance["INCORRECT"]}'
	percent_correct = f'Percentage correct: {round((run_performance["CORRECT"] / no_sound_trials) * 100)} %'
	mainTask_progress = f'Blocks completed: {block_idx} / {no_blocks}'
	mainTask_rest = stimuli.TextScreen(
		params["REST_HEADING"], 
		mainTask_performance + f"\n\n{percent_correct}" + f"\n\n{mainTask_progress}" + "\n\n" + params["REST_TEXT"],
		heading_size=params["HEADING_SIZE"],
		heading_colour=params["WHITE"],
		text_size=params["TEXT_SIZE"],
		text_colour=params["WHITE"]
		)
	mainTask_rest.present()

	# Wait for the participant to signal they are rested
	keyboard.wait(keys=params['DETECTION_SYMBOL'])
	mainTask_rest.clear_surface()
	blank_canvas.present()

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
exp.clock.wait(params["READING_TIME"])
goodbye_task_message.clear_surface() 

## ---------------------------------------------------------------------------------------
## LOCALIZER TASK
## ---------------------------------------------------------------------------------------
task_name = "localizer"

## ---------------------------------------------------------------------------------------
# Say thanks & goodbye to the participant
goodbye_exp_message.present()
exp.clock.wait(params["READING_TIME"])
goodbye_exp_message.clear_surface()
control.end()