#! /usr/bin/env python
# Time-stamp: <2024-19-02 m.utrosa@bcbl.eu>

# 1. PREPARATION ----------------------------------------------------------------------------------
import random, glob, os
import numpy as np
from expyriment import design, control, stimuli, io, misc
control.set_develop_mode(on = False) # While developping True, while testing False.

## ------------------------------------------ PARAMETERS ------------------------------------------
params = {
	
	# Experiment status. This will impact the filenames.
	"RUN"     : "1",		  # No need for zeros before integers here.
	"SESSION" : "01", 		  # Prefixed with arbitrary number of 0s for consistent indentation!

	# Local setup
	"AUDIO_DIRECTORY" : "C:/Users/monik/Documents/Donostia/code/temporal_expectations/",
	# "AUDIO_DIRECTORY" : "",
	"AUDIOFILE_REGEX" : "**/*.wav",

	# Experiment structure
	"NO_TRIALS"			 	: 5,	# A trial is a sound-silence sequence duo.
	"NO_SEQUENCES"       	: 5, 	# The number of sound or silence sequences per trial.
									# NO_TRIALS and NO_SEQUENCES has to be the same.
	"SOUNDS_PER_SEQUENCE"   : 30,

	# Visual
	"CANVAS_SIZE" : (1920, 1080), # Monitor resolution.

	"FIXATION_CROSS_SIZE"     : (20, 20),
	"FIXATION_CROSS_POSITION" : (0, 0),
	"FIXATION_CROSS_WIDTH"    : 4,

	"HEADING_SIZE" : 30, 
	"TEXT_SIZE"    : 20,
	# "HEADING"      : "INSTRUCCIONES",
	# "TEXT" 		 : f"Tu tarea consiste en detectar si el sonido se ha repetido o no.\n"
	# 				 "Una repetición de sonido ocurre cuando el sonido actual es igual al último.\n"
	# 				 "\nPulse cualquier botón cuando se repita un sonido. Sé rápido/a.\n"
	# 				 "Recibirás indicación: verde (correcto) y roja (incorrecto).\n"
	# 				 "\nPulse cualquier botón para continuar.",
	"HEADING" 	   : "INSTRUCTIONS",
	"TEXT" 		   : f"Your task is to detect whether the sound has been repeated or not.\n"
					  "A sound repetition is when the current sound is the same as the last one.\n"
					  "\nPress any button when a sound is repeated. Be fast.\n"
					  "You will receive feedback: green (correct) and red (incorrect).\n"
					  "\nPress any button to continue.",

	# Colors in RGB
	"BLACK" : (0, 0, 0),	   # screen background
	"WHITE" : (255, 255, 255), # fixation cross
	"GREEN" : (50,205,50),     # correct response
	"RED"   : (204,0,0),       # incorrect reponse
	# Colorblind versions of green & red.
	# "GREEN" : (0,255,255) # Cyan
	# "RED"   : (255,165,0) # Orange

	# Sound
	"SOUND_STRATA"     : 84,   # Total amount of available sounds.
	"SOUND_DURATION"   : 1000, # milliseconds
	"SOUND_REP_PROB"   : .05,

	# Responses. The rainbow response pad is 1234, while the gun one abcd.
	# "DETECTION_SYMBOL"   : [misc.constants.K_1, misc.constants.K_2, misc.constants.K_3, misc.constants.K_4],
	# "DETECTION_ASCII"    : ['49', '50', '51', '52']
	"DETECTION_SYMBOL"   : [misc.constants.K_a, misc.constants.K_b, misc.constants.K_c, misc.constants.K_d],
	"DETECTION_ASCII" 	 : ['97', '98', '99', '100']
}

## ------------------------------------------ FUNCTIONS -------------------------------------------
def create_soundtrack(sound_strata, sequence_len, rep_prob, sequence_no):
	'''
	Generates sounds sequences with the following constraints:
	(a) Each sound has a probability of repetition defined by `rep_prob`.
	(b) The last two and first three sounds in the experiment are always unique (no repetitions).
	(c) Sounds are distributed randomly across the experiment.
	(d) All sounds are used fairly, avoiding selection bias.

	Parameters:
	- sound_strata: A list of all loaded sounds.
	- sequence_len: The number of sounds per sequence.
	- rep_prob: The probability of a sound repeating within the experiment.
	- sequence_no: The total number of sequences.

	Returns:
	- sequences: A structured sequence of sound sequences (a list of lists) with the above constraints.
	'''

	# Calculate the number of unique and repeated sounds across the sequences.
	n_reps = rep_prob * sequence_no * sequence_len
	rem    = n_reps % int(n_reps) # For non-divisible
	n_reps = int(random.choices([np.floor(n_reps), np.ceil(n_reps)], [1 - rem, rem])[0])
	n_norep_max  = (sequence_len * sequence_no) - n_reps
	assert n_norep_max >= 5, "Probability of repetitions too high for the amount of sequences desired. Adjust sequence parameters."

	# If the number of total sounds needed is larger then the number of available sounds, prolong the sound strata by looping through it multiple times.
	n_loops = int(np.ceil((sequence_len * sequence_no) / len(sound_strata)))

	# Create a list of non-repeated sounds. A repetition is when two sounds repeat consecutively.
	resample = True
	while resample:
		all_strata_sounds = [sound_strata[u] for _ in range(n_loops) for u in np.random.permutation(range(len(sound_strata)))]
		# Check for sequential repetitions in the generated sequence: no previous and current sound are the same.
		resample = any([all_strata_sounds[u] == all_strata_sounds[u - 1] for u in range(1, len(all_strata_sounds))])
	
	all_unique_sounds = all_strata_sounds[:n_norep_max]   # Shorten to the desired number of unique sounds.
	all_sounds = all_strata_sounds[:sequence_len * sequence_no] # Shorten to the desired length of the experiment.

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
		# Randomly sample repetition indices
		repeat_idx = [(idx, idx + 1) for idx in np.sort(np.random.permutation(range(3, sequence_len * sequence_no - 1))[:n_reps])]
		flattened_repeat_idx = [x for idx_tuple in repeat_idx for x in idx_tuple] # Ensure no overlap with unique_idx.

		# Resample if idx duplicates or if any idx is in both repeat_idx and unique_idx.
		resample = any([ix0 == ix1 for ix0, ix1 in zip(flattened_repeat_idx[1:], flattened_repeat_idx[:-1])])
		resample = resample or bool(set(flattened_repeat_idx) & set(unique_idx))

		assert len(repeat_idx) == n_reps # This should be unnecessary if the resampling logic is correct.

	# Create a sequence of all sounds presented in the experiment.
	for idx1, idx2 in repeat_idx:
	    sound1, sound2 = all_sounds[idx1], all_sounds[idx2] # Get the unique sounds at the selected indices.
	    repeated_sound = random.choice([sound1, sound2])    # Randomly choose one of the two sounds to repeat.
	    
	    # Replace the original sounds at the selected indices with the repeated sounds.
	    all_sounds[idx1] = repeated_sound
	    all_sounds[idx2] = repeated_sound

	# Separate the all_sounds sequence into separate sequences.
	sequences = [all_sounds[sequence_len * n : sequence_len * (n + 1)] for n in range(sequence_no)]

	return sequences

def compute_durations(pars, clock_start, clock_end, verbose = True):
	'''
	Compute the predicted and actual durations of an event (e.g.: a sequence or trial).

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

def give_feedback(curr_sound, position_in_sequence, response, hit, fa):
	'''
	Determines the response category for a given response to a sound display and gives feedback by
	changing the color of the fixation cross.
	
	Parameters:
	- curr_sound: The name of the sound that is currently being played (str).
	- position_in_sequence: The index of the sound in the current sound sequence (int).
	- response: The identity of the key pressed (ASCII codes, not symbols).
	- hit: The fixation cross, indicating correct responses.
	- fa: The fixation cross, indicating incorrect responses.
	
	Returns:
	- perfo_code: The response category (str), logged to events.tsv file (BIDS output).
	- perfo_sound: Dictionary tracking performance.
	- curr_sound_key: The current sound's name (key). In return, for updating outside the funtion.
	'''
	# Reference globally defined variables to allow their modification outside the scope of this
	# function. sounds_in_sequence is an empty dictionary, while the reversed_strata represents 
	# the reversed sound_strata dictionary. Keys are sounds names (e.g.: s3_animal_1_ramp10.wav)
	# and values are sound IDs (expyriment audio object IDs; e.g.:
	# <expyriment.stimuli._audio.Audio object at 0x0000018DED268E08>).
	global sounds_in_sequence, reversed_strata

	# Define current and previous sounds with names, not IDs. Each sound presented in the experiment
	# has a unique ID. A sound repetition will have the same name but different ID.
	perfo_sound = {"H": 0, "M": 0, "CR": 0, "FA": 0}
	perfo_code = None
	prev_sound_key = sounds_in_sequence[position_in_sequence - 1] if position_in_sequence > 0 else None
	curr_sound_key = reversed_strata.get(curr_sound)

	# Feedback structure.
	if curr_sound_key is prev_sound_key and response is not None: # HIT
		hit.present(); perfo_sound["H"] += 1; perfo_code = "HIT"
	elif curr_sound_key is prev_sound_key and response is None: # MISS
		perfo_sound["M"] += 1; perfo_code = "MISS"
	elif curr_sound_key is not prev_sound_key and response is None: # CORRECT REJECTION
		perfo_sound["CR"] += 1;	perfo_code = "CORR_REJECTION"
	elif curr_sound_key is not prev_sound_key and response is not None: # FALSE ALARM
		fa.present(); perfo_sound["FA"] += 1; perfo_code = "FALSE_ALARM"

	return perfo_code, perfo_sound, curr_sound_key

def play_sounds(sequence, sound_duration, fixation, response_keys, log_events_sound):
	'''
	Plays one sound sequence, where sounds are presented one after the other (immediately).

	Parameters:
	- sequence: A single sequence of sounds (list) from the create_soundtrack() output (sequences).
	- sound_duration: The duration of individual sounds. All sounds need to have the same duration.
	- fixation: The generic white fixation cross. It's neutral, without any feeback.
	- response_keys: A list of accepted keys for responding (depends on the chosen response pad).
	- log_events_sound: A file containing information about events, following BIDS specification. 
	'''
	global sounds_in_sequence # The updating of this variable ensures correct feedback!
	for count, sound_ID in enumerate(sequence): # Sound ID refers to the specific sound in the experiment (repetitions have different sound IDs).
		fixation_cross.present() # Ensuring return to neutral, if feedback was shown in previous loop.
		audio_start = exp.clock.time # Correct for delays: reading instructions, ...
		audio_end   = audio_start + sound_duration;
		sound_ID.play(log_event_tag = True) # Appends a summary of the inter-event-intervals to the event file.

		while exp.clock.time <= audio_end:
			key_ASCII_audio, RT_audio = keyboard.wait(keys = response_keys, duration = (audio_end - exp.clock.time), wait_for_keyup = False)
			perf_code, curr_perf, cs = give_feedback(sound_ID, count, key_ASCII_audio, correct, wrong) # CS: current sound (name).
			if key_ASCII_audio: # For key presses that are True (not None).
				# Log
				log_events_sound.write(f"{(exp.clock.time) / 1000};") # onset
				log_events_sound.write(f"{(exp.clock.time - audio_start) / 1000};") # duration
				log_events_sound.write("n/a;") # stim_file
				log_events_sound.write("n/a;") # response
				log_events_sound.write(f"{chr(key_ASCII_audio)};") # key
				log_events_sound.write(f"{RT_audio / 1000}\n") # response_time

		# Manual row writing in BIDS format.
		log_events_sound.write(f"{audio_start / 1000};") # onset
		log_events_sound.write(f"{(audio_end - audio_start) / 1000};") # duration
		log_events_sound.write(cs.split("\\")[1]); log_events_sound.write(";") # stim_file
		log_events_sound.write(f"{perf_code};") # response
		log_events_sound.write("n/a;") # key
		log_events_sound.write("n/a\n") # response_time

		# Update sounds in sequence for correct feedback.
		sounds_in_sequence.append(cs)

def play_silence(null_sound, sound_duration, sequence_len, response_keys, log_events_null):
	'''
	Plays one silent sequence, where a single null sound is presented repetitively.

	Parameters:
	- null_sound: A single preloaded null sound.
	- sound_duration: The duration of the null sound.
	- sequence_len: The number null sound repetitions.
	- response_keys: A list of accepted keys for responding (depends on the chosen response pad).
	- log_events_null: A file containing information about events, following BIDS specification. 
	'''
	fixation_cross.present()
	for null_event in range(sequence_len):
		null_start = exp.clock.time # Correct for delays: reading instructions, ...
		null_end   = null_start + sound_duration
		null_sound.play(log_event_tag = True)

		# While playing the sound check for target key presses.
		while exp.clock.time <= null_end:
			key_ASCII_silence, RT_silence = keyboard.wait(keys = response_keys, duration = (null_end - exp.clock.time), wait_for_keyup = False)
			if key_ASCII_silence:
				# Log
				log_events_null.write(f"{(exp.clock.time) / 1000};") # onset
				log_events_null.write(f"{(exp.clock.time - null_start) / 1000};") # duration
				log_events_null.write("n/a;") # stim_file
				log_events_null.write("n/a;") # response
				log_events_null.write(f"{chr(key_ASCII_silence)};") # key
				log_events_null.write(f"{RT_silence / 1000}\n") # response_time

		# Manual row writing in BIDS format.
		log_events_null.write(f"{null_start / 1000};") # onset
		log_events_null.write(f"{(null_end - null_start) / 1000};") # duration
		log_events_null.write("null_event.wav;") # stim_file
		log_events_null.write("n/a;") # response
		log_events_null.write("n/a;") # key
		log_events_null.write("n/a\n") # response_time

## ------------------------------------------ LOAD SOUNDS -----------------------------------------
wav_filepaths = glob.glob(f'{params["AUDIO_DIRECTORY"]}/{params["AUDIOFILE_REGEX"]}')

# All sounds should be stored in a single "Stimuli" folder. Non-null sounds must be marked with "s3".
sounds_all = ["stimuli" + file_1.split("stimuli", 1)[1] for file_1 in wav_filepaths if "s3" in file_1]
random.shuffle(sounds_all)
filename_silence = ["stimuli" + file_2.split("stimuli", 1)[1] for file_2 in wav_filepaths if "null" in file_2][0]

# 3. SET UP LOGGING & INITIALIZE THE EXPERIMENT ---------------------------------------------------
exp = design.Experiment(name = "localizer")
control.initialize(exp)

# 4. CREATE & PRELOAD THE STIMULI -----------------------------------------------------------------
## Creating.
keyboard = io.Keyboard()
canvas = stimuli.Canvas(size=params["CANVAS_SIZE"], colour=params["BLACK"])
fixation_cross = stimuli.FixCross(size=params["FIXATION_CROSS_SIZE"], position=params["FIXATION_CROSS_POSITION"], 
								  line_width=params["FIXATION_CROSS_WIDTH"], colour=params["WHITE"])
wrong = stimuli.FixCross(size=params["FIXATION_CROSS_SIZE"], position=params["FIXATION_CROSS_POSITION"], 
								  line_width=params["FIXATION_CROSS_WIDTH"], colour=params["RED"])
correct = stimuli.FixCross(size=params["FIXATION_CROSS_SIZE"], position=params["FIXATION_CROSS_POSITION"], 
								  line_width=params["FIXATION_CROSS_WIDTH"], colour=params["GREEN"])
instructions = stimuli.TextScreen(params["HEADING"], params["TEXT"], heading_size=params["HEADING_SIZE"], text_size=params["TEXT_SIZE"])
silence = stimuli.Audio(filename_silence)
sounds = {filename: stimuli.Audio(filename) for filename in sounds_all}

## Preloading. This ensures fast stimuli presentation.
canvas.preload(); fixation_cross.preload(); wrong.preload(); correct.preload(); instructions.preload(); silence.preload()
for s in sounds.values():
	s.preload()

## Pair sound ID names (for expyriment presentation) and filenames (for data storage).
sound_strata = random.sample(list(sounds.items()), params["SOUND_STRATA"])
sound_strata = dict(sound_strata)
reversed_strata = {value: key for key, value in sound_strata.items()} # Works because values are unique!
soundtrack = create_soundtrack(sound_strata = list(sound_strata.values()), sequence_len = params["SOUNDS_PER_SEQUENCE"],
								rep_prob = params["SOUND_REP_PROB"], sequence_no = params["NO_SEQUENCES"])

# 6. RUN THE EXPERIMENT ---------------------------------------------------------------------------
session = params["SESSION"]; run = params["RUN"] # Extract info for log's filename.
control.start(skip_ready_screen = True) # Start the experiment without the ready screen and wait for trigger from the MRI.

# Decide randomly to start with silence or sound.
start_with_sound = random.choice([True, False]) # The same on each trial.
control.defaults.fast_response = True # Enable background drawing for faster performance.

# BIDS-formatted EventFile: onset [sec], duration [sec], type [key/sound], correct [HIT/FALSE_ALARM/...].
event_output = io.OutputFile(suffix = params["SESSION"], directory = f'bids_output')
event_output.write("onset;duration;stim_file;response;key;response_time\n") # Column names.

# Instructions & Trigger.
instructions.present()
keyboard.wait(keys=params['DETECTION_SYMBOL']) # Press the any button when you finish reading the instructions.
keyboard.wait(keys=[misc.constants.K_s]) # Wait for 's' key from the scanner to synchronize scanner & script.

# Start looping through the selected number of trials.
exp_start_time = exp.clock.time; print(f"EXPERIMENT STARTED AT: {exp_start_time} msec.")
for trial in range(params["NO_TRIALS"]):
	canvas.present()
	fixation_cross.present()

	if start_with_sound:
		sounds_in_sequence = []
		t1 = exp.clock.time; play_sounds(soundtrack[trial], params["SOUND_DURATION"], fixation_cross, params["DETECTION_SYMBOL"], event_output); t2 = exp.clock.time
		t3 = exp.clock.time; play_silence(silence, params["SOUND_DURATION"], params["SOUNDS_PER_SEQUENCE"], params["DETECTION_SYMBOL"], event_output); t4 = exp.clock.time
		print("SOUND FIRST:"); compute_durations(params, t1, t2, True); compute_durations(params, t3, t4, True)

	else:
		t5 = exp.clock.time; play_silence(silence, params["SOUND_DURATION"], params["SOUNDS_PER_SEQUENCE"], params["DETECTION_SYMBOL"], event_output); t6 = exp.clock.time
		sounds_in_sequence = []
		t7 = exp.clock.time; play_sounds(soundtrack[trial], params["SOUND_DURATION"], fixation_cross, params["DETECTION_SYMBOL"], event_output); t8 = exp.clock.time
		print("SILENCE FIRST:"); compute_durations(params, t5, t6, True); compute_durations(params, t7, t8, True)

	# Save the event log.
	event_output.rename(f"sub-{exp.subject}_ses-{session}_task-{exp.name}_run-{run}_events.tsv")
	event_output.save()

# 7. END THE EXPERIMENT ---------------------------------------------------------------------------
control.end(goodbye_text = "Thank you for participating!")