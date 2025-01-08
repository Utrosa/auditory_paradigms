#! /usr/bin/env python
# Time-stamp: <2024-19-11 m.utrosa@bcbl.eu>

# 1. PREPARATION ----------------------------------------------------------------------------------
import random, glob, os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
from expyriment import design, control, stimuli, io, misc

control.set_develop_mode(on=True) # SET MODE: while developping True, while testing False

def create_soundtrack(sound_strata, trial_len, rep_prob, trial_no):
	'''
	Create a sequence of sounds where: 
	(a) each sound has a prob. of repetition rep_probability,
	(b) the first three sounds are never repeated,
	(c) repetitions within trials with average repetition below 0.05,
	(d) randomly distributed across the experiment,
	(e) no bias in sound "participation".
	'''

	# Calculate the number of sound reps within a trial
	n_reps = trial_no * trial_len * rep_prob
	rem    = n_reps % int(n_reps) # For non-divisible
	n_reps = int(random.choices([np.floor(n_reps), np.ceil(n_reps)], [1-rem, rem])[0])

	# Calculate the number of unique sounds in a trial
	n_norep_max    = trial_no * trial_len - n_reps
	n_norep_strata = int(np.ceil((n_norep_max) / len(sound_strata)))

	# List of non-repeated sounds: ensure that previous and current sound are not the same.
	resample = True
	while resample:
		all_s = [sound_strata[u] for _ in range(n_norep_strata) for u in np.random.permutation(range(len(sound_strata)))]
		resample = any([all_s[u] == all_s[u-1] for u in range(1,len(sound_strata))])

	all_s = all_s[:n_norep_max]

	# Determine the points of stimuli repetitions
	resample = True
	while resample:
		repeat_idx = np.sort(np.random.permutation(range(4, len(all_s)-1))[:n_reps]) # skip the first 3 sounds!
		resample   = any([idx0 == idx1 for idx0, idx1 in zip(repeat_idx[1:], repeat_idx[:-1])])
		resample   = resample or len(set([all_s[idx] for idx in repeat_idx])) != len(repeat_idx)

	# Repeat the selected sounds
	for idx in repeat_idx[::-1]:
		all_s.insert(idx, all_s[idx])

	trials = [all_s[trial_len * n : trial_len * (n + 1)] for n in range(trial_no)]
	return(trials)

def play_sounds(soundtrack, duration):
	''' 
	Plays the soundtracks of natural sounds.
	Asks the subject if the the sound was repeated or not. 
	Tracks reaction time and which key was pressed to respond for each sound in a trial.
	'''
	keys_trial    = []; key_append   = keys_trial.append
	RTs_trial     = []; RT_append    = RTs_trial.append
	sounds_trial  = []; sound_append = sounds_trial.append
	perfo_trial   = {}; perfo_trial["H"] = 0; perfo_trial["M"]  = 0; perfo_trial["CR"]  = 0; perfo_trial["FA"]  = 0

	for sound_ID in soundtrack:
		fixation_cross.present()
		sound_ID.play()
		# exp.clock.wait(params["WAIT_TIME"])

		key, RT = keyboard.wait_char(['1','4'], duration) ################################################

		# Feedback
		if sound_ID in sounds_trial and key == '1': # HIT
			correct.present()
			exp.clock.wait(params["WAIT_TIME"])
			perfo_trial["H"] += 1
		elif sound_ID in sounds_trial and key == '4': # MISS
			wrong.present()
			exp.clock.wait(params["WAIT_TIME"])
			perfo_trial["M"] += 1
		elif sound_ID not in sounds_trial and key == '4': # CORRECT REJECTION ------------- NO FEEDBACK
			correct.present()
			exp.clock.wait(params["WAIT_TIME"])
			perfo_trial["CR"] += 1
		elif sound_ID not in sounds_trial and key == '1': # FALSE ALARM
			wrong.present()
			exp.clock.wait(params["WAIT_TIME"])
			perfo_trial["FA"] += 1

		# Save relevant data
		key_append(key)
		RT_append(RT)
		sound_append(sound_ID)

	return keys_trial, RTs_trial, sounds_trial

params = {
	
	# Local setup
	"AUDIO_DIRECTORY": "C:/Users/monik/Documents/BCBL/code/localizer/",
	"AUDIOFILE_REGEX" : "**/s3_*",

	# Experiment structure
	"NO_TRIALS"			 : 2,     # sounds-silence sequence repetitions
	"SOUNDS_PER_TRIAL"   : 10,
	"WAIT_TIME"          : 150,    # milliseconds (the duration of the pause between sound and question)
	"MAX_RESPONSE_DELAY" : 5000,   # milliseconds

	# Visual
	"CANVAS_SIZE" : (1920, 1080), # monitor resolution

	"FIXATION_CROSS_SIZE"     : (20, 20),
	"FIXATION_CROSS_POSITION" : (0, 0),
	"FIXATION_CROSS_WIDTH"    : 4,

	"HEADING_SIZE" : 30, 
	"TEXT_SIZE"    : 20,
	"TEXT" 		   : f"Tu tarea consiste en detectar si el sonido se ha repetido o no. \n"
					  "Pulse 1 para repetido y 4 para no repetido. \n"
					  "Recibirás indicación: verde (correcto) y roja (incorrecto). \n"
					  " \n"
					  "Pulse 2 para continuar.",

	# Colors in RGB
	"BLACK" : (0, 0, 0),	   # screen background
	"WHITE" : (255, 255, 255), # fixation cross
	"GREEN" : (50,205,50),     # correct response
	"RED"   : (204,0,0),       # incorrect reponse

	# Sound
	"SOUND_STRATA"     : 10,
	"SOUND_DURATION"   : 1000, # milliseconds
	"SOUND_REP_PROB"   : .1,
	"SILENCE_DURATION" : 5000  # milliseconds
}

## Load auditory stimuli
wav_filepaths = glob.glob(f'{params["AUDIO_DIRECTORY"]}/{params["AUDIOFILE_REGEX"]}', recursive=True)
sounds_all = ["stimuli" + file.split("stimuli", 1)[1] for file in wav_filepaths if "s3" in file]
random.shuffle(sounds_all)

# 3. INITIALIZE THE EXPERIMENT --------------------------------------------------------------------
exp = design.Experiment(name="Localizer")
control.initialize(exp)

# 4. CREATE & PRELOAD THE STIMULI -----------------------------------------------------------------
## Preloading ensures fast stimuli presentation.
keyboard = io.Keyboard()
canvas   = stimuli.Canvas(size=params["CANVAS_SIZE"], colour=params["BLACK"]); canvas.preload()
fixation_cross = stimuli.FixCross(size=params["FIXATION_CROSS_SIZE"], position=params["FIXATION_CROSS_POSITION"], 
								  line_width=params["FIXATION_CROSS_WIDTH"], colour=params["WHITE"])
wrong   = stimuli.FixCross(size=params["FIXATION_CROSS_SIZE"], position=params["FIXATION_CROSS_POSITION"], 
								  line_width=params["FIXATION_CROSS_WIDTH"], colour=params["RED"])
correct = stimuli.FixCross(size=params["FIXATION_CROSS_SIZE"], position=params["FIXATION_CROSS_POSITION"], 
								  line_width=params["FIXATION_CROSS_WIDTH"], colour=params["GREEN"])
fixation_cross.preload(); wrong.preload(); correct.preload()

instructions = stimuli.TextScreen(
	"Instrucciones", params["TEXT"], heading_size=params["HEADING_SIZE"], text_size=params["TEXT_SIZE"])
instructions.preload()

sounds = {filename: stimuli.Audio(filename) for filename in sounds_all}
for s in sounds.values():
    s.preload()

trials = create_soundtrack(sound_strata = random.sample(list(sounds.values()), params["SOUND_STRATA"]), trial_len = params["SOUNDS_PER_TRIAL"],
	                       rep_prob = params["SOUND_REP_PROB"], trial_no = params["NO_TRIALS"])

# 5. STORE DATA -----------------------------------------------------------------------------------
exp.add_data_variable_names(['trial_no', 'keys_trial', 'RTs_trial', 'sound_IDs_trial'])

# 6. RUN THE EXPERIMENT ---------------------------------------------------------------------------
control.start(skip_ready_screen=True) # Start the experiment without the ready screen and wait for trigger from the MRI
instructions.present()
keyboard.wait(keys=[misc.constants.K_2]) # Press no. 2 when you read the instructions.
keyboard.wait(keys=[misc.constants.K_s]) # Wait for 's' key from the scanner to synchronize scanner & script!

### Start looping through the selected number of trials.
keys_exp   = []; k_a = keys_exp.append
RTs_exp    = []; r_a = RTs_exp.append

for count, trial in enumerate(trials):
	keyboard.check(keys=[misc.constants.K_ESCAPE]) # Enable stopping the exp with ESC button
	
	# Decide randomly to start with silence or sound
	start_with_sound = random.choice([True, False])
	if start_with_sound:

		# Sounds with fixation
		canvas.present()
		fixation_cross.present()
		keys_trial, RTs_trial, sounds_trial = play_sounds(soundtrack=trial, duration=params["MAX_RESPONSE_DELAY"])
		k_a(keys_trial)
		r_a(RTs_trial)

		# Silence with fixation
		fixation_cross.present()
		exp.clock.wait(params["SILENCE_DURATION"])

	else:
		# Silence with fixation
		fixation_cross.present()
		exp.clock.wait(params["SILENCE_DURATION"])

		# Sounds with fixation
		canvas.present()
		fixation_cross.present()
		keys_trial, RTs_trial, sounds_trial = play_sounds(soundtrack=trial, duration=params["MAX_RESPONSE_DELAY"])
		k_a(keys_trial)
		r_a(RTs_trial)

	# Save trial data
	soundIDs_trial = {key for key, value in sounds.items() if value in sounds_trial}
	exp.data.add([count+1, keys_exp, RTs_exp, soundIDs_trial])

# 7. END THE EXPERIMENT ---------------------------------------------------------------------------
control.end()