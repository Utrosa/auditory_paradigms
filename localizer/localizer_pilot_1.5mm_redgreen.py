#! /usr/bin/env python
# Time-stamp: <20-10-2025 m.utrosa@bcbl.eu>

# 0. PREPARATION ------------------------------------------------------------------------
import numpy as np
import random, glob, os
from datetime import datetime
from expyriment import design, control, stimuli, io, misc
control.set_develop_mode(on = False) # While developping True, while testing False.

# 1. PARAMETERS -------------------------------------------------------------------------
sesh = input("Enter the session number with 0 prefixed (e.g.: 01, 02):")

# Get current time for unique ID of output files
now = datetime.now()
tis  = int(now.timestamp())

# Use current time to seed both random generators
seed = int(tis * 1000) % 2**32
random.seed(seed)
np.random.seed(seed)

# Speficy BIDS-formatted EventFile
# onset [msec], duration [msec], stim_file [wav], response [HIT/FALSE_ALARM/...]
# key [chr(ASCII)], press_time [msec], RT [msec]

log_format_fStr  = "{0:.3f};{1:.3f};{2};{3};{4};{5:.3f};{6:.3f}\n"
log_format_NaNs  = "{0:.3f};{1:.3f};{2};{3};{4};{5};{6}\n"
params = {

	# Local setup: All sounds must be in "Stimuli" folder. Sounds need "s3" prefix.
	"AUDIO_DIRECTORY" : "/home/mutrosa/Documents/projects/localizer_fMRI/task/",
	"AUDIOFILE_REGEX" : "**/*.wav",

	# Experiment structure
	"RUNS"     	   			: 7,  # the number of functional MRI sequences
	"NO_TRIALS"	   			: 5,  # the number of equally long sound and silence pairs
	"SOUNDS_PER_SEQUENCE"   : 20, # determines the length of trials; each sound is 1 sec

	# Visual
	"CANVAS_SIZE" : (1024, 768), # MRI monitor resolution.

	"FIXATION_CROSS_SIZE"     : (40, 40),
	"FIXATION_CROSS_POSITION" : (0, 0),
	"FIXATION_CROSS_WIDTH"    : 6,

	"HEADING_SIZE" : 30, 
	"TEXT_SIZE"    : 20,
	"INTRO_HEADING"   : "INSTRUCTIONS",
	"INTRO_TEXT" 	  : f"You will hear sequences of different sounds, separated by longer periods of silence."
						 "\n\nAt times, some sounds will play twice in a row. "
						 "\nPress any button as quickly as you can when you hear a sound repetition.\n"
						 "\nYou will receive feedback: green (correct) and red (incorrect).\n"
						 "\nDuring silent periods, just relax and stay still without moving your arms, legs, or head.\n"
						 "\nWe will repeat this task 7 times. Each run lasts about 4 minutes, with rest breaks in between.\n"
						 "\nPress any button to start.",
	"REST_HEADING" : "BREAK TIME",
	"REST_TEXT"    : "Please take a moment to rest and realign your body as needed.",
	"MRI_HEADING"  : "SCANNER CALIBRATION",
	"MRI_TEXT"     : "Please relax and remain still for a few moments.\n\nThank you!",

	# Colors in RGB
	"BLACK"   : (0, 0, 0),	     # screen background
	"WHITE"   : (255, 255, 255), # fixation cross
	"CORRECT" : (94,  207, 54),  # green
	"WRONG"   : (234, 15,  30),  # red

	# Sound
	"SOUND_STRATA"     : 84,   # the total amount of available sounds
	"SOUND_DURATION"   : 1000, # msec
	"SOUND_REP_PROB"   : .05,  # low enough to be stimulating/challenging

	# In the MRI, the rainbow response pad is 1234, while the gun one abcd.
	"DETECTION_SYMBOL"   : [misc.constants.K_1, misc.constants.K_2, misc.constants.K_3, misc.constants.K_4],
	"DETECTION_ASCII"    : ['49', '50', '51', '52']
}

# 2. FUNCTIONS --------------------------------------------------------------------------
def create_soundtrack(sound_strata, sequence_len, rep_prob, sequence_no):
	'''
	Generates sounds sequences with the following constraints:
	(a) Each sound has a probability of repetition defined by rep_prob.
	(b) The last two and first three sounds in the experiment are always unique.
	(c) Sounds are distributed randomly across the experiment.
	(d) All sounds are used fairly, avoiding selection bias.

	Parameters:
	- sound_strata: A list of all loaded sounds.
	- sequence_len: The number of sounds per sequence.
	- rep_prob: The probability of a sound repeating within the experiment.
	- sequence_no: The total number of sequences.

	Returns:
	- sequences: A list of lists (sound sequences) with the above constraints.
	'''

	# Calculate the number of unique and repeated sounds across the sequences.
	total_sounds = sequence_len * sequence_no
	n_reps_float = rep_prob * total_sounds
	n_reps = int(np.floor(n_reps_float) + (np.random.rand() < (n_reps_float - np.floor(n_reps_float))))
	n_norep_max = total_sounds - n_reps
	if n_reps > total_sounds - 5:
		raise ValueError("Probability of repetitions is too high.")

	# If the number of sounds needed in total is larger then the number of available sounds,
	# prolong the sound strata by looping through it multiple times.
	n_loops = int(np.ceil(total_sounds / len(sound_strata)))

	# Create a list of non-repeated sounds. A repetition is when two sounds repeat consecutively.
	resample = True
	while resample:
		all_strata_sounds = [sound_strata[u] for _ in range(n_loops) for u in np.random.permutation(len(sound_strata))]
		
		# Check for sequential repetitions in the generated sequence: no previous and current sound are the same.
		resample = any([all_strata_sounds[u] == all_strata_sounds[u - 1] for u in range(1, len(all_strata_sounds))])
	
	all_unique_sounds = all_strata_sounds[:n_norep_max] # Shorten to the desired number of unique sounds.
	all_sounds = all_strata_sounds[:total_sounds] # Shorten to the desired length of the experiment.

	# Determine the indices of both sequence clashes (boundaries) and necessarily unique sounds.
	all_idx = list(range(0,len(all_sounds)))
	unique_idx = [0, 1, 2] + all_idx[-2:] # No repetitions for the last 2 and first 3 sounds in the experiment.
	boundary_idx = [[all_idx[sequence_len * n - 1]] + [all_idx[sequence_len * n]] for n in range(sequence_no)]
	boundary_idx = boundary_idx[1:] # The first pair is irrelevant (the indices of the first and last sound in the exp.)
	
	# Flatten the boundary indices list and add it to the unique_idx list.
	unique_idx = np.sort(unique_idx + [item for sublist in boundary_idx for item in sublist])

	# Determine the sound repetition indices (two values per repetition).
	resample = True
	while resample:

		# Randomly sample repetition indices, ensuring no overlap with unique_idx.
		repeat_idx = [(idx, idx + 1) for idx in np.sort(np.random.permutation(range(3, total_sounds - 1))[:n_reps])]
		flattened_repeat_idx = [x for idx_tuple in repeat_idx for x in idx_tuple]

		# Resample if idx duplicates or if any idx is in both repeat_idx and unique_idx.
		resample = any([ix0 == ix1 for ix0, ix1 in zip(flattened_repeat_idx[1:], flattened_repeat_idx[:-1])])
		resample = resample or bool(set(flattened_repeat_idx) & set(unique_idx))

		assert len(repeat_idx) == n_reps # This should be unnecessary if the resampling logic is correct.

	# Create a sequence of all sounds presented in the experiment.
	for idx1, idx2 in repeat_idx:
	    repeated_sound   = all_sounds[idx1]
	    all_sounds[idx2] = repeated_sound

	# Separate the all_sounds sequence into separate sequences.
	sequences = [all_sounds[sequence_len * n : sequence_len * (n + 1)] for n in range(sequence_no)]

	return sequences

def compute_durations(pars, clock_start, clock_end, verbose = True):
	'''
	Computes the predicted and actual durations of sound or silence parts in trials.

	Parameters:
	- pars: A dictionary, containing all user-defined parameters.
	- clock_start: Start time given by the Expyriment's clock.
	- clock_end: Start time given by the Expyriment's clock.
	- verbose: Prints the computed durations in the terminal when True.

	Returns:
	- dur_predicted: The predicted trial duration, which is calculated from the user-defined audio parameters.
	- dur_actual: The actual trial duration, which is calculated from times given by Expyriment's clock.
	'''
	dur_predicted = pars['SOUNDS_PER_SEQUENCE'] * pars['SOUND_DURATION']
	dur_actual 	  = clock_end - clock_start

	if verbose:
		print(f'Predicted duration: {dur_predicted} msec. Actual duration: {dur_actual} msec.')

	return (dur_predicted, dur_actual)

def give_feedback(current_sound, position_in_sequence, response, good, bad):
	'''
	Determines the response category for a given response to a sound display.
	gives feedback by changing the color of the fixation cross.
	
	Parameters:
	- current_sound: The name of the sound that is currently being played (str).
	- position_in_sequence: The index of the sound in the current sound sequence (int).
	- response: The identity of the key pressed in ASCII code.
	- good: A class implementing fixation cross for correct responses (green/cyan).
	- bad: A class implementing fixation cross for wrong responses (red/orange).

	Returns:
	- perfo_code: The response category (str).
	- run_performance: Dictionary tracking performance across runs (dict).
	- current_sound_key: The current stimuli name as obtained outside the funtion (str).
	- feeedback_status: Indicates whether feedback is given or not (boolean).
	'''
	# sounds_in_sequence is an empty dictionary. 
	# reversed_strata represents the reversed sound_strata dictionary. 
	# Dict keys are sounds names (e.g.: s3_animal_1_ramp10.wav) 
	# Dict values are expyriment audio object IDs, (e.g.: <expyriment.stimuli._audio.Audio object at 0x0000018DED268E08>).
	global sounds_in_sequence, reversed_strata, run_performance

	# Define current and previous sounds with names. 
	# Each sound presented in the experiment has a unique ID.
	# A sound repetition will have the same name but different ID.
	prev_sound_key    = sounds_in_sequence[position_in_sequence - 1] if position_in_sequence > 0 else None
	current_sound_key = reversed_strata.get(current_sound)

	# Default values
	perfo_code, feedback_status = None, None

	# Feedback structure
	if current_sound_key == prev_sound_key:
		if response is not None:
			good.present(clear = False, log_event_tag = True); run_performance["H"] += 1; perfo_code = "HIT"; feedback_status = True
		elif response is None:
			bad.present(clear = False, log_event_tag = True); run_performance["M"] += 1; perfo_code = "MISS"; feedback_status = True
	
	else:
		if response is None:
			run_performance["CR"] += 1;	perfo_code = "CORR_REJECTION"; feedback_status = False
		elif response is not None:
			bad.present(clear = False, log_event_tag = True); run_performance["FA"] += 1; perfo_code = "FALSE_ALARM"; feedback_status = True

	return perfo_code, run_performance, current_sound_key, feedback_status

def play_sounds(sequence, sound_duration, exp, canvas, fixation, correct, wrong, keyboard, response_keys, log_events_sound):
	'''
	Plays one sound sequence, where sounds are presented one after the other.

	Parameters:
	- sequence: A single sequence of sounds (list) from the create_soundtrack() output.
	- sound_duration: The duration of individual sounds. All sounds need to have the same duration.
	- exp: A class implementing a basic experiment in expyriment.
	- canvas: A class implementing a canvas stimulus in expyriment.
	- fixation: A class implementing a general fixation cross in expyriment (white).
	- correct: A class implementing fixation cross for correct responses (green/cyan).
	- wrong: A class implementing fixation cross for correct responses (red/orange).	
	- keyboard: A class implementing a keyboard input in expyriment.
	- response_keys: A list of accepted keys for responding (depends on the chosen response pad).
	- log_events_sound: A file containing information about events, following BIDS specification.

	Returns:
	- sounds_start: Time (float), indicating the start of the sound sequence.
	- sounds_end: Time (float), indicting the end of the sound sequence.
	'''
	global sounds_in_sequence, run_start_time, run_performance
	feedback_shown, fs = None, None
	sounds_start = exp.clock.time

	# Sound ID refers to the specific sound in the experiment
	# Sound repetitions have different sound IDs
	for count, sound_ID in enumerate(sequence):

		# Refresh the screen when feedback was given
		if feedback_shown is not None and count - feedback_shown == 2:
			canvas.present()

		# Stamp audio start time and play
		audio_start = exp.clock.time
		sound_ID.play(maxtime = sound_duration, log_event_tag = True)

		key_ASCII_audio, key_log_entry = None, None

		# Check for key presses while the sound is playing
		while sound_ID.is_playing and sound_ID.time < (audio_start + sound_duration):

			# Non-blocking function to check for pressed keys
			keys = keyboard.read_out_buffered_keys()

			# Key-press trials
			if keys and keys[0] != 115: # 115 is s from scanner sync box
				press_time = exp.clock.time
				key_ASCII_audio = keys[0] # If multiple, we take the first key

				# Show feedback
				perf_code, run_performance, cs, fs = give_feedback(sound_ID,
																   count,
																   key_ASCII_audio,
																   correct,
																   wrong)
				# Logging
				if key_ASCII_audio is not None:

					key_log_entry = {
						"onset": np.abs(audio_start - run_start_time) / 1000,
						"duration": sound_duration / 1000, # dummy duration
						"stim_file": cs.split("stimuli/")[1],
						"response": perf_code,
						"key": chr(key_ASCII_audio),
						"press_time": np.abs(press_time - run_start_time) / 1000,
						"RT": np.abs(press_time - audio_start) / 1000
					}

		# After the sound has stopped playing
		audio_end = exp.clock.time

		# Correct the sound duration for key trials
		if key_log_entry is not None:
			key_log_entry["duration"] = np.abs(audio_end - audio_start) / 1000
			log_events_sound.write(log_format_fStr.format(
												key_log_entry["onset"],
												key_log_entry["duration"],
												key_log_entry["stim_file"],
												key_log_entry["response"],
												key_log_entry["key"],
												key_log_entry["press_time"],
												key_log_entry["RT"]
									))

		# No-key trials	
		if not key_ASCII_audio:
			
			# Show feedback
			perf_code, run_performance, cs, fs = give_feedback(sound_ID,
															   count,
															   key_ASCII_audio,
															   correct,
															   wrong)
			# Logging
			log_events_sound.write(log_format_NaNs.format(
				np.abs(run_start_time - audio_start) / 1000, # onset
				np.abs(audio_end - audio_start) / 1000,  	 # duration
				cs.split("stimuli/")[1],  			  		 # stim_file
				perf_code, 							  		 # response
				"n/a", 								  		 # key
				"n/a",								  		 # press time
				"n/a"								  		 # RT
			))
		
		# Update feedback tracking and sequence record
		if fs:
			feedback_shown = count

		# Update sounds in sequence for correct feedback.
		sounds_in_sequence.append(cs)

	sounds_end = exp.clock.time
	return sounds_start, sounds_end

def play_silence(null_sound, sound_duration, exp, null_number, keyboard, response_keys, log_events_null):
	'''
	Plays one silent sequence, where a single null sound is presented repetitively.

	Parameters:
	- null_sound: A single preloaded null sound.
	- sound_duration: The duration of the null sound.
	- exp: A class implementing a basic experiment in expyriment.
	- null_number: The number of null sound repetitions.
	- keyboard: A class implementing a keyboard input in expyriment.
	- response_keys: A list of accepted keys for responding (depends on the chosen response pad).
	- log_events_null: A file containing information about events, following BIDS specification.

	Returns:
	- silence_start: Time (float), indicating the start of the silence.
	- silence_end: Time (float), indicting the end of the silence.
	'''
	global run_start_time
	silence_start = exp.clock.time

	for null_event in range(null_number):
		
		# Refresh screen (needed in quit key is pressed)
		canvas.present()

		# Stamp audio start time and play
		null_start = exp.clock.time
		null_sound.play(maxtime = sound_duration, log_event_tag = True)

		key_ASCII_silence, key_log_entry = None, None

		# Check for key presses while the sound is playieng
		while null_sound.is_playing and null_sound.time < (null_start + sound_duration):

			# Non-blocking function to check for pressed keys
			keys = keyboard.read_out_buffered_keys()

			# Key-press trials
			if keys and keys[0] != 115: # 115 is s from scanner sync box
				press_time = exp.clock.time
				key_ASCII_silence = keys[0] # If multiple, we take the first key

				# Logging
				if key_ASCII_silence is not None:
					key_log_entry = {
						"onset": np.abs(null_start - run_start_time) / 1000,
						"duration": sound_duration / 1000, # dummy duration
						"stim_file": "null_event.wav",
						"response": "n/a",
						"key": chr(key_ASCII_silence),	
						"press_time": np.abs(press_time - run_start_time) / 1000,
						"RT": np.abs(press_time - null_start) / 1000
					}

		# After the sound has stopped playing
		null_end = exp.clock.time

		# Correct the sound duration for key trials
		if key_log_entry is not None:
			key_log_entry["duration"] = np.abs(null_end - null_start) / 1000
			log_events_null.write(log_format_fStr.format(
												key_log_entry["onset"],
												key_log_entry["duration"],
												key_log_entry["stim_file"],
												key_log_entry["response"],
												key_log_entry["key"],
												key_log_entry["press_time"],
												key_log_entry["RT"]
									))

		# No-key trials
		if not key_ASCII_silence:

			# Logging
			log_events_null.write(log_format_NaNs.format(
				np.abs(run_start_time - null_start) / 1000, # onset
				np.abs(null_end - null_start) / 1000,		# duration
				"null_event.wav",  					  		# stim_file
				"n/a",			         			  		# response
				"n/a",   							  		# key
				"n/a",								  		# press time
				"n/a"								  		# RT
			))
	
	silence_end = exp.clock.time
	return silence_start, silence_end

# 3. LOAD STIMULI -----------------------------------------------------------------------
wav_filepaths = glob.glob(f'{params["AUDIO_DIRECTORY"]}/{params["AUDIOFILE_REGEX"]}')
sounds_all = ["stimuli" + file_1.split("stimuli", 1)[1] for file_1 in wav_filepaths if "s3" in file_1]
random.shuffle(sounds_all)
filename_silence = ["stimuli" + file_2.split("stimuli", 1)[1] for file_2 in wav_filepaths if "null" in file_2][0]

# 4. INITIALIZE THE EXPERIMENT ----------------------------------------------------------
exp = design.Experiment(name = "localizer")
control.initialize(exp)

# 5. CREATE & PRELOAD THE STIMULI -------------------------------------------------------
# Creating stimuli.
keyboard = io.Keyboard()

canvas       = stimuli.Canvas(size = params["CANVAS_SIZE"], colour = params["BLACK"])
blank_canvas = stimuli.Canvas(size = params["CANVAS_SIZE"], colour = params["BLACK"])

instructions  = stimuli.TextScreen(params["INTRO_HEADING"], params["INTRO_TEXT"], heading_size = params["HEADING_SIZE"], text_size = params["TEXT_SIZE"])
scanner_text  = stimuli.TextScreen(params["MRI_HEADING"],   params["MRI_TEXT"],   heading_size = params["HEADING_SIZE"], text_size = params["TEXT_SIZE"])

fix_cross = stimuli.FixCross(size = params["FIXATION_CROSS_SIZE"], position = params["FIXATION_CROSS_POSITION"], line_width = params["FIXATION_CROSS_WIDTH"], colour = params["WHITE"])
wrong     = stimuli.FixCross(size = params["FIXATION_CROSS_SIZE"], position = params["FIXATION_CROSS_POSITION"], line_width = params["FIXATION_CROSS_WIDTH"], colour = params["WRONG"])
correct   = stimuli.FixCross(size = params["FIXATION_CROSS_SIZE"], position = params["FIXATION_CROSS_POSITION"], line_width = params["FIXATION_CROSS_WIDTH"], colour = params["CORRECT"])

silence = stimuli.Audio(filename_silence)
sounds  = {filename: stimuli.Audio(filename) for filename in sounds_all}

# Preloading. This ensures fast stimuli presentation.
fix_cross.preload(); fix_cross.plot(canvas); blank_canvas.preload()
canvas.preload(); instructions.preload(), scanner_text.preload()
wrong.preload(); correct.preload()
for s in sounds.values():
	s.preload()
silence.preload()

# Pair sound ID names (for expyriment presentation) and filenames (for data storage).
sound_strata = random.sample(list(sounds.items()), params["SOUND_STRATA"])
sound_strata = dict(sound_strata)
reversed_strata = {value: key for key, value in sound_strata.items()} # Works because values are unique!
soundtrack = create_soundtrack(sound_strata = list(sound_strata.values()), sequence_len = params["SOUNDS_PER_SEQUENCE"],
								rep_prob = params["SOUND_REP_PROB"], sequence_no = params["NO_TRIALS"] * params["RUNS"])

# 6. RUN THE EXPERIMENT -----------------------------------------------------------------
control.start(skip_ready_screen = True)

# Decide randomly to start with silence or sound.
start_with_sound = random.choice([True, False])

# Wait for the participant to read the instructions.
instructions.present()
keyboard.wait(keys=params['DETECTION_SYMBOL'])
instructions.clear_surface()
blank_canvas.present()

loop = 0
# Start the structure of the experiment
for run in range(params["RUNS"]): # Runs == Blocks == Functional Acquisitions

	# Initialize the log with unique timestamps.
	nw = datetime.now()
	ts = int(nw.timestamp())
	event_output = io.OutputFile(suffix = sesh, directory = f'bids_output')
	event_output.write("onset;duration;stim_file;response;key;press_time;response_time\n")
	run_performance = {"H": 0, "M": 0, "CR": 0, "FA": 0}
	canvas.present()

	# Wait for 4 's' keys from the scanner to synchronize scanner & script onsets.
	keyboard.wait(keys=[misc.constants.K_s]); keyboard.wait(keys=[misc.constants.K_s]); 
	keyboard.wait(keys=[misc.constants.K_s]); keyboard.wait(keys=[misc.constants.K_s])

	# Mark the start of the run
	run_start_time = exp.clock.time

	# Loop through the trials
	for trial in range(params["NO_TRIALS"]):

		if start_with_sound:

			# Sound part
			sounds_in_sequence = []
			t1, t2 = play_sounds(soundtrack[loop],
						params["SOUND_DURATION"],
						exp,
						canvas,
						fix_cross,
						correct,
						wrong,
						keyboard,
						params["DETECTION_SYMBOL"],
						event_output)

			# Refresh the screen
			canvas.present()

			# Silent part
			t3, t4 = play_silence(silence,
						 params["SOUND_DURATION"],
						 exp,
						 params["SOUNDS_PER_SEQUENCE"],
						 keyboard,
						 params["DETECTION_SYMBOL"],
						 event_output)
			print("SOUND FIRST:"); compute_durations(params, t1, t2, True); compute_durations(params, t3, t4, True)
			
			# Refresh the screen
			canvas.present()

		else:
			# Silent part
			t5, t6 = play_silence(silence,
						 params["SOUND_DURATION"],
						 exp,
						 params["SOUNDS_PER_SEQUENCE"],
						 keyboard,
						 params["DETECTION_SYMBOL"],
						 event_output)

			# Refresh the screen
			canvas.present()

			# Sound part
			sounds_in_sequence = []
			t7, t8 = play_sounds(soundtrack[loop],
						params["SOUND_DURATION"],
						exp,
						canvas, 
						fix_cross,
						correct,
						wrong,
						keyboard,
						params["DETECTION_SYMBOL"],
						event_output)
			print("SILENCE FIRST:"); compute_durations(params, t5, t6, True); compute_durations(params, t7, t8, True)

			# Refresh the screen
			canvas.present()

		# Update the count
		loop += 1

	# Save the log
	event_output.rename(f"sub-{exp.subject:02d}_ses-{sesh}_task-{exp.name}_run-{run + 1:02d}_ts-{ts}_events.tsv")
	event_output.save()

	# The experiment ends before the MRI protocol. Inform the participant to keep calm and remain still.
	blank_canvas.present()
	scanner_text.present()

	# Wait for the MRI QU to end the run by pressing a key unavailable to the participant.
	keyboard.wait(keys = [misc.constants.K_e])
	
	# Give encouragement and perfromance update on all runs except the last one.
	if run + 1 < params["RUNS"]:
		performance = f'Correct: {run_performance["H"]}, Wrong: {run_performance["FA"]}'
		progress    = f'Runs completed: {run+1}/{params["RUNS"]}'
		rest = stimuli.TextScreen(
			params["REST_HEADING"], 
			performance + f"\n\n{progress}" + "\n\n" + params["REST_TEXT"],
			heading_size = params["HEADING_SIZE"], 
			text_size = params["TEXT_SIZE"])
		rest.present()

		# Starting a new run with a key unavailable to the participant.
		keyboard.wait(keys = [misc.constants.K_g])
	
	elif run + 1 == params["RUNS"]:
		control.end(goodbye_text = "The end. Thank you for participating! :)")