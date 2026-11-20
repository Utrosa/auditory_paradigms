#! /usr/bin/env python
# Time-stamp: <20-11-2026, m.utrosa@bcbl.eu>
'''
Requires Expyriment version 1.0.0
TODO: log events
TODO: test timing of events
'''
from expyriment import design, control, stimuli, misc, io
from config_timfreq import params, twitch, feedback_flash
import config_timfreq as c
from pathlib import Path
import pandas as pd
import numpy as np
import ast
from datetime import datetime

# 01. USER-DEFINED PARAMETERS ------------------------------------------------------------
sub    = input("Enter the subject number:")
sesh   = input("Enter the session number:")
combo  = input("Enter the combo number:")
comboID, sesID, subID = int(combo), int(sesh), int(sub)
control.set_develop_mode(on = params["DEVELOP_MODE"])

# 02. PRECOMPUTED PARAMETERS -------------------------------------------------------------
tonesPath = c.outPath / f"exp_parameter_combo-{comboID:03d}.csv"
flashPath = c.outPath / f"exp_distractor_combo-{comboID:03d}.csv"
logsPath = c.projPath / f"flash_logs/sub-{subID:02d}/ses-{sesID:02d}"
logsPath.mkdir(exist_ok=True, parents=True)

# Load the dataframe
df_flash = pd.read_csv(flashPath)
no_runs  = len(df_flash["run_idx"].unique())

# Load audio files for the current session and sort by run number
main_task_wavs = list(c.outPath.glob("**/*.wav"))
main_task_audio = [file_1 for file_1 in main_task_wavs if f"ses-{sesID:02d}" and f"sub-{subID:02d}" in str(file_1)]
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

# Plotting
fix_cross.plot(canvas)

# Preloading for faster presentation
fix_cross.preload()
canvas.preload()
blank_canvas.preload()
wrong.preload()
correct.preload()
circle.preload()

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

# Loop through the runs. Equivalent to looping through "main_audio" 
# because there is one audio file per run.
for run in range(no_runs):

	# Initialize unique timestamps, output file for flash counting task, and 
	# a dictionary to track performance on this task.
	nw = datetime.now()
	ts = int(nw.timestamp())
	flash_log = io.OutputFile(suffix=sesh, directory=str(logsPath))
	flash_log.write("onset\tduration\ttrial_type\tresponse_time\n")
	run_performance = {"CORRECT": 0, "INCORRECT": 0}

	# Extract variables specific to the current run
	run_idx = run + 1
	flash_run = df_flash[df_flash["run_idx"] == run_idx]
	main_audio_values = main_audio.get(f"run-{run_idx:02d}")

	# Check if quit key is pressed
	keyboard.check(keys=[misc.constants.K_y])	

	# Wait for onset of the functional sequence
	keyboard.wait(keys=[misc.constants.K_s])
	canvas.present()

	# Mark the start of the functional sequence
	run_start_time = exp.clock.time

	print(f"---- RUN:{run_idx} ----")
	print(f"Run start: {run_start_time}")
	
	# Wait for 4 's' keys from the scanner to synchronize scanner & script onsets.
	keyboard.wait(keys=[misc.constants.K_s]); keyboard.wait(keys=[misc.constants.K_s])
	keyboard.wait(keys=[misc.constants.K_s]); keyboard.wait(keys=[misc.constants.K_s])
	
	# Mark the starting time of the task.
	task_start_time = exp.clock.time
	print(f"Task start: {task_start_time - run_start_time}")
	
	# Play the audio stimuli
	main_audio_values.play()

	# While playing the main task audiofile, flash the disk.
	while main_audio_values.is_playing:

		# Check if quit key is pressed
		keyboard.check(keys=[misc.constants.K_y])

		# Iterate through the flashes programmed for the current run.
		for _, row in flash_run.iterrows():

			# Wait until the onset time for the distractor
			while exp.clock.time - task_start_time < row.onset:
				if not main_audio_values.is_playing:
					break
			
			if not main_audio_values.is_playing:
				break
			
			# Start twitch at onset
			twons = exp.clock.time
			for _ in range(int(row["n_reps"])):
				twitch(
						stimulus = circle,
						duration = params["FLASH_DURATION"],
						isi      = row["isi"],
						screen   = canvas,
						clock    = clock,
						keyboard = keyboard
						)
			twend = exp.clock.time
			print(f"Actual twitch duration: {abs((twons - task_start_time) - (twend - task_start_time))}")
			print(f"Programmed twitch duration: {row.duration}\n\n")

			# Collect responses only if twitched & within max response period
			response, rt, perfo_code = None, None, None
			response_time_start = exp.clock.time

			# Check for key presses with max response time
			while exp.clock.time - response_time_start < params["MAX_RESPONSE_TIME"]:

				# Non-blocking function to check for pressed keys
				keys = keyboard.read_out_buffered_keys()

				# ------ Key-press trials ------ 
				if keys and keys[0] != 115:  # 115 is "s" from scanner sync box
					response = keys[-1]      # If multiple, we take the last key

					# Get time of key press
					key_press_time = exp.clock.time / 1000
					
					# Get reaction time
					rt = (exp.clock.time - response_time_start) / 1000

					# Show feedback
					perfo_code, run_performance = feedback_flash(
						row["n_reps"], # Actual number of flashes
						response,      # Participant's count
						correct,       # Fixation cross for correct responses
						wrong          # Fixation cross for incorrect responses
					)
					
					# Log the responses
					flash_log.write(f"{key_press_time}\t100\t{chr(response)}\t{rt}\n")

					# Refresh the screen after max time for seeing feedback
					exp.clock.wait(params["MAX_FEEDBACK_TIME"])
					canvas.present() # Refresh the screen

			# ------ No-key trials ------   
			if not response:
				perfo_code, run_performance = feedback_flash(
					row["n_reps"], # Actual number of flashes
					response,      # Participant's count
					correct,       # Fixation cross for correct responses
					wrong          # Fixation cross for incorrect responses
				)
				exp.clock.wait(params["MAX_FEEDBACK_TIME"])
				canvas.present() # Refresh the screen

	# Rename the logs according to BIDS standard
	flash_log.rename(f"sub-{exp.subject:02d}_ses-{sesID:02d}_task-flash_ts-{ts}_events.tsv")
	
	# Save the run-level log
	flash_log.save()

	# Clearing any key presses
	keyboard.clear()

	# If the main task ends before the MRI protocol, instruct the participant to
	# keep calm and remain still.
	blank_canvas.present()
	scanner_text.present()

	# Wait for the MRI QU to end the run by pressing a key unavailable to the participant.
	keyboard.wait(keys=[misc.constants.K_e])

	# When the MRI QU signals acquistion end, show text with performance updates.
	mainTask_performance = f'Correct: {run_performance["CORRECT"]}, Wrong: {run_performance["INCORRECT"]}'
	percent_correct = f'Percentage correct: {round((run_performance["CORRECT"] / len(flash_run)) * 100)} %'
	mainTask_progress = f'Blocks completed: {run_idx} / {no_runs}'
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